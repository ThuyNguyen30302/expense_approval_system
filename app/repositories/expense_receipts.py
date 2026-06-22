from sqlalchemy.orm import Session

from app.models.expense_receipt import ExpenseReceipt


class ExpenseReceiptRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, receipt: ExpenseReceipt) -> ExpenseReceipt:
        self.db.add(receipt)
        self.db.flush()
        self.db.refresh(receipt)
        return receipt
