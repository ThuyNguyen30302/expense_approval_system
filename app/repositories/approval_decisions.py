from sqlalchemy.orm import Session

from app.models.approval_decision import ApprovalDecision


class ApprovalDecisionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, decision: ApprovalDecision) -> ApprovalDecision:
        self.db.add(decision)
        self.db.flush()
        self.db.refresh(decision)
        return decision
