from sqlalchemy.orm import Session

from app.models.payment import Payment


class PaymentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.flush()
        self.db.refresh(payment)
        return payment
