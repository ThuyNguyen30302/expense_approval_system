from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, audit_log: AuditLog) -> AuditLog:
        self.db.add(audit_log)
        self.db.flush()
        self.db.refresh(audit_log)
        return audit_log

    def list_by_expense(
        self,
        *,
        expense_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[AuditLog], int]:
        statement = select(AuditLog).where(AuditLog.expense_id == expense_id)
        count_statement = select(func.count()).select_from(statement.subquery())
        audit_logs = self.db.execute(
            statement.order_by(AuditLog.created_at.asc()).limit(limit).offset(offset)
        ).scalars().all()
        total = self.db.execute(count_statement).scalar_one()
        return list(audit_logs), total
