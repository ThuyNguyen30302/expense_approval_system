from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.expense import Expense, ExpenseCategory, ExpenseStatus
from app.models.user import User
from app.schemas.expense import (
    AuditLogListResponse,
    ExpenseApprovalRequest,
    ExpenseCancelRequest,
    ExpenseCreate,
    ExpenseDecisionReasonRequest,
    ExpenseListResponse,
    ExpensePaidRequest,
    ExpenseResponse,
    ExpenseUpdate,
    PaymentPendingRequest,
)
from app.services.expenses import ExpenseService


router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("", response_model=ExpenseResponse, status_code=201)
def create_expense(
    request: ExpenseCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Expense:
    return ExpenseService(db).create_expense(request, current_user)


@router.get("", response_model=ExpenseListResponse)
def list_expenses(
    status: ExpenseStatus | None = None,
    category: ExpenseCategory | None = None,
    requester_id: UUID | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ExpenseListResponse:
    expenses, total = ExpenseService(db).list_expenses(
        current_user=current_user,
        limit=limit,
        offset=offset,
        status=status,
        category=category,
        requester_id=requester_id,
        from_date=from_date,
        to_date=to_date,
    )
    return ExpenseListResponse(items=expenses, total=total, limit=limit, offset=offset)


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Expense:
    return ExpenseService(db).get_expense(expense_id, current_user)


@router.patch("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: UUID,
    request: ExpenseUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Expense:
    return ExpenseService(db).update_expense(expense_id, request, current_user)


@router.post("/{expense_id}/submit", response_model=ExpenseResponse)
def submit_expense(
    expense_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Expense:
    return ExpenseService(db).submit_expense(expense_id, current_user)


@router.post("/{expense_id}/cancel", response_model=ExpenseResponse)
def cancel_expense(
    expense_id: UUID,
    request: ExpenseCancelRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Expense:
    return ExpenseService(db).cancel_expense(expense_id, request, current_user)


@router.post("/{expense_id}/manager-approval", response_model=ExpenseResponse)
def manager_approve_expense(
    expense_id: UUID,
    request: ExpenseApprovalRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Expense:
    return ExpenseService(db).manager_approve_expense(expense_id, request, current_user)


@router.post("/{expense_id}/manager-rejection", response_model=ExpenseResponse)
def manager_reject_expense(
    expense_id: UUID,
    request: ExpenseDecisionReasonRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Expense:
    return ExpenseService(db).manager_reject_expense(expense_id, request, current_user)


@router.post("/{expense_id}/return-to-employee", response_model=ExpenseResponse)
def return_expense_to_employee(
    expense_id: UUID,
    request: ExpenseDecisionReasonRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Expense:
    return ExpenseService(db).return_expense_to_employee(expense_id, request, current_user)


@router.post("/{expense_id}/accounting-approval", response_model=ExpenseResponse)
def accounting_approve_expense(
    expense_id: UUID,
    request: ExpenseApprovalRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Expense:
    return ExpenseService(db).accounting_approve_expense(expense_id, request, current_user)


@router.post("/{expense_id}/accounting-rejection", response_model=ExpenseResponse)
def accounting_reject_expense(
    expense_id: UUID,
    request: ExpenseDecisionReasonRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Expense:
    return ExpenseService(db).accounting_reject_expense(expense_id, request, current_user)


@router.post("/{expense_id}/payment-pending", response_model=ExpenseResponse)
def mark_payment_pending(
    expense_id: UUID,
    request: PaymentPendingRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Expense:
    return ExpenseService(db).mark_payment_pending(expense_id, request, current_user)


@router.post("/{expense_id}/paid", response_model=ExpenseResponse)
def mark_expense_paid(
    expense_id: UUID,
    request: ExpensePaidRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Expense:
    return ExpenseService(db).mark_expense_paid(expense_id, request, current_user)


@router.get("/{expense_id}/audit-log", response_model=AuditLogListResponse)
def list_expense_audit_logs(
    expense_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AuditLogListResponse:
    audit_logs, total = ExpenseService(db).list_audit_logs(
        expense_id=expense_id,
        current_user=current_user,
        limit=limit,
        offset=offset,
    )
    return AuditLogListResponse(items=audit_logs, total=total, limit=limit, offset=offset)
