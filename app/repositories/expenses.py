from datetime import date
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.expense import Expense


class ExpenseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, expense: Expense) -> Expense:
        self.db.add(expense)
        self.db.flush()
        self.db.refresh(expense)
        return expense

    def get_by_id(self, expense_id: UUID) -> Expense | None:
        statement = (
            select(Expense)
            .options(selectinload(Expense.receipts))
            .where(Expense.id == expense_id)
        )
        return self.db.execute(statement).scalar_one_or_none()

    def list(
        self,
        *,
        limit: int,
        offset: int,
        requester_id: UUID | None = None,
        visible_requester_id: UUID | None = None,
        visible_manager_id: UUID | None = None,
        accounting_visible: bool = False,
        status: str | None = None,
        category: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> tuple[list[Expense], int]:
        statement = self._filtered_select(
            requester_id=requester_id,
            visible_requester_id=visible_requester_id,
            visible_manager_id=visible_manager_id,
            accounting_visible=accounting_visible,
            status=status,
            category=category,
            from_date=from_date,
            to_date=to_date,
        )
        count_statement = select(func.count()).select_from(statement.subquery())

        expenses = self.db.execute(
            statement.options(selectinload(Expense.receipts))
            .order_by(Expense.created_at.desc())
            .limit(limit)
            .offset(offset)
        ).scalars().all()
        total = self.db.execute(count_statement).scalar_one()
        return list(expenses), total

    def _filtered_select(
        self,
        *,
        requester_id: UUID | None,
        visible_requester_id: UUID | None,
        visible_manager_id: UUID | None,
        accounting_visible: bool,
        status: str | None,
        category: str | None,
        from_date: date | None,
        to_date: date | None,
    ) -> Select[tuple[Expense]]:
        statement = select(Expense)
        visibility_conditions = []
        if visible_requester_id is not None:
            visibility_conditions.append(Expense.requester_id == visible_requester_id)
        if visible_manager_id is not None:
            visibility_conditions.append(Expense.assigned_manager_id == visible_manager_id)
        if accounting_visible:
            visibility_conditions.append(
                Expense.status.in_(
                    [
                        "manager_approved",
                        "accountant_approved",
                        "accountant_rejected",
                        "payment_pending",
                        "paid",
                    ]
                )
            )
        if visibility_conditions:
            statement = statement.where(or_(*visibility_conditions))
        if requester_id is not None:
            statement = statement.where(Expense.requester_id == requester_id)
        if status is not None:
            statement = statement.where(Expense.status == status)
        if category is not None:
            statement = statement.where(Expense.category == category)
        if from_date is not None:
            statement = statement.where(Expense.expense_date >= from_date)
        if to_date is not None:
            statement = statement.where(Expense.expense_date <= to_date)
        return statement
