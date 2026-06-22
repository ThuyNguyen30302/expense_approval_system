from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.audit_log import AuditEventType, AuditLog
from app.models.expense import Expense, ExpenseCategory, ExpenseStatus
from app.models.expense_receipt import ExpenseReceipt
from app.models.user import User, UserRole, utc_now
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.expense_receipts import ExpenseReceiptRepository
from app.repositories.expenses import ExpenseRepository
from app.schemas.expense import ExpenseCancelRequest, ExpenseCreate, ExpenseUpdate, ReceiptMetadataRequest


EDITABLE_STATUSES = {
    ExpenseStatus.DRAFT.value,
    ExpenseStatus.RETURNED_TO_EMPLOYEE.value,
}
SUBMITTABLE_STATUSES = {
    ExpenseStatus.DRAFT.value,
    ExpenseStatus.RETURNED_TO_EMPLOYEE.value,
}
CANCELLABLE_STATUSES = {
    ExpenseStatus.DRAFT.value,
    ExpenseStatus.SUBMITTED.value,
    ExpenseStatus.RETURNED_TO_EMPLOYEE.value,
}


class ExpenseService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.expenses = ExpenseRepository(db)
        self.receipts = ExpenseReceiptRepository(db)
        self.audit_logs = AuditLogRepository(db)

    def create_expense(self, request: ExpenseCreate, current_user: User) -> Expense:
        expense = Expense(
            requester_id=current_user.id,
            title=request.title,
            description=request.description,
            category=request.category.value,
            amount=request.amount,
            currency=request.currency,
            status=ExpenseStatus.DRAFT.value,
            expense_date=request.expense_date,
            department=request.department,
            project_code=request.project_code,
        )
        created_expense = self.expenses.create(expense)

        if request.receipt is not None:
            self._create_receipt(created_expense, request.receipt, current_user)

        self._create_audit_log(
            expense=created_expense,
            actor=current_user,
            event_type=AuditEventType.EXPENSE_CREATED,
            previous_status=None,
            new_status=created_expense.status,
            metadata={"title": created_expense.title},
        )
        self.db.commit()
        self.db.refresh(created_expense)
        return self._get_existing_expense(created_expense.id)

    def list_expenses(
        self,
        *,
        current_user: User,
        limit: int,
        offset: int,
        status: ExpenseStatus | None = None,
        category: ExpenseCategory | None = None,
        requester_id: UUID | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> tuple[list[Expense], int]:
        visible_requester_id = None if current_user.role == UserRole.ADMIN.value else current_user.id
        if visible_requester_id is not None and requester_id is not None and requester_id != visible_requester_id:
            return [], 0

        return self.expenses.list(
            limit=limit,
            offset=offset,
            requester_id=requester_id,
            visible_requester_id=visible_requester_id,
            status=status.value if status is not None else None,
            category=category.value if category is not None else None,
            from_date=from_date,
            to_date=to_date,
        )

    def get_expense(self, expense_id: UUID, current_user: User) -> Expense:
        expense = self._get_existing_expense(expense_id)
        self._ensure_can_access(expense, current_user)
        return expense

    def update_expense(
        self,
        expense_id: UUID,
        request: ExpenseUpdate,
        current_user: User,
    ) -> Expense:
        expense = self._get_existing_expense(expense_id)
        self._ensure_can_modify(expense, current_user)
        if expense.status not in EDITABLE_STATUSES:
            raise self._invalid_transition_error("Expense cannot be updated from its current status.")

        data = request.model_dump(exclude_unset=True)
        changed_fields = self._apply_update(expense, data)
        if changed_fields:
            self._create_audit_log(
                expense=expense,
                actor=current_user,
                event_type=AuditEventType.EXPENSE_UPDATED,
                previous_status=expense.status,
                new_status=expense.status,
                metadata={"changed_fields": changed_fields},
            )
        self.db.commit()
        self.db.refresh(expense)
        return self._get_existing_expense(expense.id)

    def submit_expense(self, expense_id: UUID, current_user: User) -> Expense:
        expense = self._get_existing_expense(expense_id)
        self._ensure_can_modify(expense, current_user)
        if expense.status not in SUBMITTABLE_STATUSES:
            raise self._invalid_transition_error("Expense cannot be submitted from its current status.")

        previous_status = expense.status
        expense.status = ExpenseStatus.SUBMITTED.value
        expense.submitted_at = utc_now()
        self._create_audit_log(
            expense=expense,
            actor=current_user,
            event_type=AuditEventType.EXPENSE_SUBMITTED,
            previous_status=previous_status,
            new_status=expense.status,
        )
        self.db.commit()
        self.db.refresh(expense)
        return self._get_existing_expense(expense.id)

    def cancel_expense(
        self,
        expense_id: UUID,
        request: ExpenseCancelRequest,
        current_user: User,
    ) -> Expense:
        expense = self._get_existing_expense(expense_id)
        self._ensure_can_modify(expense, current_user)
        if expense.status not in CANCELLABLE_STATUSES:
            raise self._invalid_transition_error("Expense cannot be cancelled from its current status.")

        previous_status = expense.status
        expense.status = ExpenseStatus.CANCELLED.value
        expense.cancelled_at = utc_now()
        self._create_audit_log(
            expense=expense,
            actor=current_user,
            event_type=AuditEventType.EXPENSE_CANCELLED,
            previous_status=previous_status,
            new_status=expense.status,
            comment=request.reason,
        )
        self.db.commit()
        self.db.refresh(expense)
        return self._get_existing_expense(expense.id)

    def _create_receipt(
        self,
        expense: Expense,
        request: ReceiptMetadataRequest,
        current_user: User,
    ) -> ExpenseReceipt:
        if not any([request.url, request.file_name, request.metadata]):
            raise AppError(
                status_code=422,
                code="receipt_missing_reference",
                message="Receipt must include url, file_name, or metadata.",
            )

        receipt = ExpenseReceipt(
            expense_id=expense.id,
            uploaded_by_id=current_user.id,
            url=request.url,
            file_name=request.file_name,
            content_type=request.content_type,
            size_bytes=request.size_bytes,
            checksum=request.checksum,
            receipt_metadata=request.metadata,
        )
        created_receipt = self.receipts.create(receipt)
        self._create_audit_log(
            expense=expense,
            actor=current_user,
            event_type=AuditEventType.RECEIPT_ADDED,
            previous_status=expense.status,
            new_status=expense.status,
            metadata={"file_name": request.file_name, "content_type": request.content_type},
        )
        return created_receipt

    def _apply_update(self, expense: Expense, data: dict[str, Any]) -> list[str]:
        changed_fields: list[str] = []
        for field_name, value in data.items():
            if isinstance(value, ExpenseCategory):
                value = value.value
            current_value = getattr(expense, field_name)
            if current_value != value:
                setattr(expense, field_name, value)
                changed_fields.append(field_name)
        return changed_fields

    def _create_audit_log(
        self,
        *,
        expense: Expense,
        actor: User,
        event_type: AuditEventType,
        previous_status: str | None,
        new_status: str | None,
        comment: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        return self.audit_logs.create(
            AuditLog(
                expense_id=expense.id,
                actor_id=actor.id,
                event_type=event_type.value,
                previous_status=previous_status,
                new_status=new_status,
                comment=comment,
                audit_metadata=metadata,
            )
        )

    def _get_existing_expense(self, expense_id: UUID) -> Expense:
        expense = self.expenses.get_by_id(expense_id)
        if expense is None:
            raise AppError(
                status_code=404,
                code="expense_not_found",
                message="Expense was not found.",
            )
        return expense

    def _ensure_can_access(self, expense: Expense, user: User) -> None:
        if user.role == UserRole.ADMIN.value or expense.requester_id == user.id:
            return
        raise AppError(
            status_code=403,
            code="expense_forbidden",
            message="You do not have permission to access this expense.",
        )

    def _ensure_can_modify(self, expense: Expense, user: User) -> None:
        if user.role == UserRole.ADMIN.value or expense.requester_id == user.id:
            return
        raise AppError(
            status_code=403,
            code="expense_forbidden",
            message="You do not have permission to modify this expense.",
        )

    def _invalid_transition_error(self, message: str) -> AppError:
        return AppError(
            status_code=409,
            code="expense_invalid_status_transition",
            message=message,
        )
