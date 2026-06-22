from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.expense import ExpenseCategory, ExpenseStatus
from app.models.payment import PaymentMethod


class ReceiptMetadataRequest(BaseModel):
    url: str | None = None
    file_name: str | None = Field(default=None, max_length=255)
    content_type: str | None = Field(default=None, max_length=120)
    size_bytes: int | None = Field(default=None, gt=0)
    checksum: str | None = Field(default=None, max_length=128)
    metadata: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_has_reference(self) -> "ReceiptMetadataRequest":
        if not any([self.url, self.file_name, self.metadata]):
            raise ValueError("Receipt must include url, file_name, or metadata.")
        return self


class ReceiptMetadataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    expense_id: UUID
    uploaded_by_id: UUID
    url: str | None = None
    file_name: str | None = None
    content_type: str | None = None
    size_bytes: int | None = None
    checksum: str | None = None
    receipt_metadata: dict[str, Any] | None = Field(default=None, serialization_alias="metadata")
    created_at: datetime


class ExpenseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    category: ExpenseCategory
    amount: Decimal = Field(gt=0, decimal_places=2, max_digits=12)
    currency: str = Field(min_length=3, max_length=3)
    expense_date: date
    department: str | None = Field(default=None, max_length=120)
    project_code: str | None = Field(default=None, max_length=80)
    receipt: ReceiptMetadataRequest | None = None

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, currency: str) -> str:
        if not currency.isalpha() or currency.upper() != currency:
            raise ValueError("Currency must be a three-letter uppercase code.")
        return currency


class ExpenseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    category: ExpenseCategory | None = None
    amount: Decimal | None = Field(default=None, gt=0, decimal_places=2, max_digits=12)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    expense_date: date | None = None
    department: str | None = Field(default=None, max_length=120)
    project_code: str | None = Field(default=None, max_length=80)

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, currency: str | None) -> str | None:
        if currency is None:
            return currency
        if not currency.isalpha() or currency.upper() != currency:
            raise ValueError("Currency must be a three-letter uppercase code.")
        return currency


class ExpenseCancelRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)


class ExpenseApprovalRequest(BaseModel):
    comment: str | None = Field(default=None, max_length=1000)


class ExpenseDecisionReasonRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)


class PaymentPendingRequest(BaseModel):
    payment_method: PaymentMethod | None = None
    scheduled_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=1000)


class ExpensePaidRequest(BaseModel):
    paid_at: datetime | None = None
    payment_method: PaymentMethod | None = None
    payment_reference: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=1000)


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    expense_id: UUID
    actor_id: UUID | None = None
    event_type: str
    previous_status: ExpenseStatus | None = None
    new_status: ExpenseStatus | None = None
    comment: str | None = None
    audit_metadata: dict[str, Any] | None = Field(default=None, serialization_alias="metadata")
    created_at: datetime


class ExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    requester_id: UUID
    assigned_manager_id: UUID | None = None
    title: str
    description: str | None = None
    category: ExpenseCategory
    amount: Decimal
    currency: str
    status: ExpenseStatus
    expense_date: date
    department: str | None = None
    project_code: str | None = None
    submitted_at: datetime | None = None
    manager_decided_at: datetime | None = None
    accountant_decided_at: datetime | None = None
    paid_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    receipts: list[ReceiptMetadataResponse] = Field(default_factory=list)


class ExpenseListResponse(BaseModel):
    items: list[ExpenseResponse]
    total: int
    limit: int
    offset: int


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    limit: int
    offset: int
