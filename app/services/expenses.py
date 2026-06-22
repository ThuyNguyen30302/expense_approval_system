from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.approval_decision import ApprovalDecision, ApprovalDecisionType, ApprovalStage
from app.models.audit_log import AuditEventType, AuditLog
from app.models.expense import Expense, ExpenseCategory, ExpenseStatus
from app.models.expense_receipt import ExpenseReceipt
from app.models.payment import Payment, PaymentStatus
from app.models.user import User, UserRole, utc_now
from app.repositories.approval_decisions import ApprovalDecisionRepository
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.expense_receipts import ExpenseReceiptRepository
from app.repositories.expenses import ExpenseRepository
from app.repositories.payments import PaymentRepository
from app.schemas.expense import (
    ExpenseApprovalRequest,
    ExpenseCancelRequest,
    ExpenseCreate,
    ExpenseDecisionReasonRequest,
    ExpensePaidRequest,
    ExpenseUpdate,
    PaymentPendingRequest,
    ReceiptMetadataRequest,
)


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
ACCOUNTING_VISIBLE_STATUSES = {
    ExpenseStatus.MANAGER_APPROVED.value,
    ExpenseStatus.ACCOUNTANT_APPROVED.value,
    ExpenseStatus.ACCOUNTANT_REJECTED.value,
    ExpenseStatus.PAYMENT_PENDING.value,
    ExpenseStatus.PAID.value,
}


class ExpenseService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.expenses = ExpenseRepository(db)
        self.receipts = ExpenseReceiptRepository(db)
        self.audit_logs = AuditLogRepository(db)
        self.approval_decisions = ApprovalDecisionRepository(db)
        self.payments = PaymentRepository(db)

    def create_expense(self, request: ExpenseCreate, current_user: User) -> Expense:
        expense = Expense(
            requester_id=current_user.id,
            assigned_manager_id=current_user.manager_id,
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
        visible_requester_id = None
        visible_manager_id = None
        accounting_visible = False

        if current_user.role == UserRole.ADMIN.value:
            pass
        elif current_user.role == UserRole.MANAGER.value:
            visible_requester_id = current_user.id
            visible_manager_id = current_user.id
        elif current_user.role == UserRole.ACCOUNTANT.value:
            visible_requester_id = current_user.id
            accounting_visible = True
        else:
            visible_requester_id = current_user.id

        if visible_requester_id is not None and requester_id is not None and requester_id != visible_requester_id:
            if visible_manager_id is None and not accounting_visible:
                return [], 0

        return self.expenses.list(
            limit=limit,
            offset=offset,
            requester_id=requester_id,
            visible_requester_id=visible_requester_id,
            visible_manager_id=visible_manager_id,
            accounting_visible=accounting_visible,
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

    def manager_approve_expense(
        self,
        expense_id: UUID,
        request: ExpenseApprovalRequest,
        current_user: User,
    ) -> Expense:
        expense = self._get_existing_expense(expense_id)
        self._ensure_can_manager_act(expense, current_user)
        if expense.status != ExpenseStatus.SUBMITTED.value:
            raise self._invalid_transition_error("Expense cannot be approved from its current status.")

        return self._record_decision_transition(
            expense=expense,
            actor=current_user,
            stage=ApprovalStage.MANAGER,
            decision=ApprovalDecisionType.APPROVED,
            to_status=ExpenseStatus.MANAGER_APPROVED,
            event_type=AuditEventType.MANAGER_APPROVED,
            comment=request.comment,
            decided_at_field="manager_decided_at",
        )

    def manager_reject_expense(
        self,
        expense_id: UUID,
        request: ExpenseDecisionReasonRequest,
        current_user: User,
    ) -> Expense:
        expense = self._get_existing_expense(expense_id)
        self._ensure_can_manager_act(expense, current_user)
        if expense.status != ExpenseStatus.SUBMITTED.value:
            raise self._invalid_transition_error("Expense cannot be rejected from its current status.")

        return self._record_decision_transition(
            expense=expense,
            actor=current_user,
            stage=ApprovalStage.MANAGER,
            decision=ApprovalDecisionType.REJECTED,
            to_status=ExpenseStatus.MANAGER_REJECTED,
            event_type=AuditEventType.MANAGER_REJECTED,
            reason=request.reason,
            decided_at_field="manager_decided_at",
        )

    def return_expense_to_employee(
        self,
        expense_id: UUID,
        request: ExpenseDecisionReasonRequest,
        current_user: User,
    ) -> Expense:
        expense = self._get_existing_expense(expense_id)
        if expense.status == ExpenseStatus.SUBMITTED.value:
            self._ensure_can_manager_act(expense, current_user)
            stage = ApprovalStage.MANAGER
        elif expense.status == ExpenseStatus.MANAGER_APPROVED.value:
            self._ensure_can_accounting_act(current_user)
            stage = ApprovalStage.ACCOUNTING
        else:
            raise self._invalid_transition_error("Expense cannot be returned from its current status.")

        return self._record_decision_transition(
            expense=expense,
            actor=current_user,
            stage=stage,
            decision=ApprovalDecisionType.RETURNED,
            to_status=ExpenseStatus.RETURNED_TO_EMPLOYEE,
            event_type=AuditEventType.EXPENSE_RETURNED,
            reason=request.reason,
        )

    def accounting_approve_expense(
        self,
        expense_id: UUID,
        request: ExpenseApprovalRequest,
        current_user: User,
    ) -> Expense:
        expense = self._get_existing_expense(expense_id)
        self._ensure_can_accounting_act(current_user)
        if expense.status != ExpenseStatus.MANAGER_APPROVED.value:
            raise self._invalid_transition_error("Expense cannot be accounting-approved from its current status.")

        return self._record_decision_transition(
            expense=expense,
            actor=current_user,
            stage=ApprovalStage.ACCOUNTING,
            decision=ApprovalDecisionType.APPROVED,
            to_status=ExpenseStatus.ACCOUNTANT_APPROVED,
            event_type=AuditEventType.ACCOUNTANT_APPROVED,
            comment=request.comment,
            decided_at_field="accountant_decided_at",
        )

    def accounting_reject_expense(
        self,
        expense_id: UUID,
        request: ExpenseDecisionReasonRequest,
        current_user: User,
    ) -> Expense:
        expense = self._get_existing_expense(expense_id)
        self._ensure_can_accounting_act(current_user)
        if expense.status != ExpenseStatus.MANAGER_APPROVED.value:
            raise self._invalid_transition_error("Expense cannot be accounting-rejected from its current status.")

        return self._record_decision_transition(
            expense=expense,
            actor=current_user,
            stage=ApprovalStage.ACCOUNTING,
            decision=ApprovalDecisionType.REJECTED,
            to_status=ExpenseStatus.ACCOUNTANT_REJECTED,
            event_type=AuditEventType.ACCOUNTANT_REJECTED,
            reason=request.reason,
            decided_at_field="accountant_decided_at",
        )

    def mark_payment_pending(
        self,
        expense_id: UUID,
        request: PaymentPendingRequest,
        current_user: User,
    ) -> Expense:
        expense = self._get_existing_expense(expense_id)
        self._ensure_can_accounting_act(current_user)
        if expense.status != ExpenseStatus.ACCOUNTANT_APPROVED.value:
            raise self._invalid_transition_error("Expense cannot be marked payment pending from its current status.")

        previous_status = expense.status
        expense.status = ExpenseStatus.PAYMENT_PENDING.value
        self._create_payment(
            expense=expense,
            actor=current_user,
            status=PaymentStatus.PAYMENT_PENDING,
            payment_method=request.payment_method.value if request.payment_method is not None else None,
            scheduled_at=request.scheduled_at,
            notes=request.notes,
        )
        self._create_audit_log(
            expense=expense,
            actor=current_user,
            event_type=AuditEventType.PAYMENT_PENDING,
            previous_status=previous_status,
            new_status=expense.status,
            comment=request.notes,
            metadata={"payment_method": request.payment_method.value if request.payment_method is not None else None},
        )
        self.db.commit()
        self.db.refresh(expense)
        return self._get_existing_expense(expense.id)

    def mark_expense_paid(
        self,
        expense_id: UUID,
        request: ExpensePaidRequest,
        current_user: User,
    ) -> Expense:
        expense = self._get_existing_expense(expense_id)
        self._ensure_can_accounting_act(current_user)
        if expense.status not in {ExpenseStatus.ACCOUNTANT_APPROVED.value, ExpenseStatus.PAYMENT_PENDING.value}:
            raise self._invalid_transition_error("Expense cannot be marked paid from its current status.")

        previous_status = expense.status
        paid_at = request.paid_at or utc_now()
        expense.status = ExpenseStatus.PAID.value
        expense.paid_at = paid_at
        self._create_payment(
            expense=expense,
            actor=current_user,
            status=PaymentStatus.PAID,
            payment_method=request.payment_method.value if request.payment_method is not None else None,
            payment_reference=request.payment_reference,
            paid_at=paid_at,
            notes=request.notes,
        )
        self._create_audit_log(
            expense=expense,
            actor=current_user,
            event_type=AuditEventType.EXPENSE_PAID,
            previous_status=previous_status,
            new_status=expense.status,
            comment=request.notes,
            metadata={
                "payment_method": request.payment_method.value if request.payment_method is not None else None,
                "payment_reference": request.payment_reference,
            },
        )
        self.db.commit()
        self.db.refresh(expense)
        return self._get_existing_expense(expense.id)

    def list_audit_logs(
        self,
        *,
        expense_id: UUID,
        current_user: User,
        limit: int,
        offset: int,
    ) -> tuple[list[AuditLog], int]:
        expense = self._get_existing_expense(expense_id)
        self._ensure_can_access(expense, current_user)
        return self.audit_logs.list_by_expense(expense_id=expense_id, limit=limit, offset=offset)

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

    def _record_decision_transition(
        self,
        *,
        expense: Expense,
        actor: User,
        stage: ApprovalStage,
        decision: ApprovalDecisionType,
        to_status: ExpenseStatus,
        event_type: AuditEventType,
        reason: str | None = None,
        comment: str | None = None,
        decided_at_field: str | None = None,
    ) -> Expense:
        previous_status = expense.status
        expense.status = to_status.value
        if decided_at_field is not None:
            setattr(expense, decided_at_field, utc_now())

        self.approval_decisions.create(
            ApprovalDecision(
                expense_id=expense.id,
                actor_id=actor.id,
                stage=stage.value,
                decision=decision.value,
                from_status=previous_status,
                to_status=expense.status,
                reason=reason,
                comment=comment,
            )
        )
        self._create_audit_log(
            expense=expense,
            actor=actor,
            event_type=event_type,
            previous_status=previous_status,
            new_status=expense.status,
            comment=reason or comment,
            metadata={"stage": stage.value, "decision": decision.value},
        )
        self.db.commit()
        self.db.refresh(expense)
        return self._get_existing_expense(expense.id)

    def _create_payment(
        self,
        *,
        expense: Expense,
        actor: User,
        status: PaymentStatus,
        payment_method: str | None = None,
        payment_reference: str | None = None,
        scheduled_at: Any | None = None,
        paid_at: Any | None = None,
        notes: str | None = None,
    ) -> Payment:
        return self.payments.create(
            Payment(
                expense_id=expense.id,
                actor_id=actor.id,
                status=status.value,
                payment_method=payment_method,
                payment_reference=payment_reference,
                scheduled_at=scheduled_at,
                paid_at=paid_at,
                notes=notes,
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
        if user.role == UserRole.MANAGER.value and expense.assigned_manager_id == user.id:
            return
        if user.role == UserRole.ACCOUNTANT.value and expense.status in ACCOUNTING_VISIBLE_STATUSES:
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

    def _ensure_can_manager_act(self, expense: Expense, user: User) -> None:
        if user.role == UserRole.ADMIN.value:
            return
        if user.role == UserRole.MANAGER.value and expense.assigned_manager_id == user.id:
            return
        raise AppError(
            status_code=403,
            code="expense_forbidden",
            message="You do not have permission to perform a manager action on this expense.",
        )

    def _ensure_can_accounting_act(self, user: User) -> None:
        if user.role in {UserRole.ACCOUNTANT.value, UserRole.ADMIN.value}:
            return
        raise AppError(
            status_code=403,
            code="expense_forbidden",
            message="You do not have permission to perform an accounting action.",
        )

    def _invalid_transition_error(self, message: str) -> AppError:
        return AppError(
            status_code=409,
            code="expense_invalid_status_transition",
            message=message,
        )
