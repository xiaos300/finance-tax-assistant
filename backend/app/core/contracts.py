"""Implemented D0/D1 subset of contracts 1.2; strict shared wire DTOs."""
from typing import Annotated, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from datetime import date, datetime
import re

Id = Annotated[str, Field(min_length=1, max_length=128)]
Version = Annotated[int, Field(ge=1)]
Revision = Annotated[int, Field(ge=0)]
T = TypeVar("T")


class Contract(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid",regex_engine='python-re')


class Health(Contract):
    status: Literal["alive", "ready", "not_ready"]
    checks: dict[str, bool] = Field(default_factory=dict)


class Envelope(Contract, Generic[T]):
    data: T
    request_id: Id


class ErrorBody(Contract):
    code: Id
    message: Annotated[str, Field(min_length=1, max_length=1000)]
    details: dict[str, object]
    retryable: bool
    turn_id: UUID | None


class ErrorEnvelope(Contract):
    error: ErrorBody
    request_id: Id


Company = Literal['C001','C002']
Name = Annotated[str, Field(min_length=1,max_length=200)]
Text500 = Annotated[str, Field(min_length=1,max_length=500)]
Note = Annotated[str, Field(max_length=4000)]
Money = Annotated[str, Field(pattern=r'^(0|[1-9][0-9]*)\.[0-9]{2}$')]
Month = Annotated[str, Field(pattern=re.compile(r'^(?!0000)[0-9]{4}-(0[1-9]|1[0-2])$'))]
Cursor = Annotated[str, Field(min_length=1,max_length=2000)]
Topic = Literal['amount','purpose','bank']


class CompanyAccess(Contract):
    company_id: Company
    name: Name
    can_write: bool


class Principal(Contract):
    user_id: Id
    name: Name
    companies: list[CompanyAccess]


class InvoiceSearchItem(Contract):
    company_id: Company
    company_name: Name
    invoice_id: Id
    invoice_date: str
    seller: Text500
    item_name: Text500
    amount: Money
    row_version: Version

    @field_validator('invoice_date')
    @classmethod
    def valid_date(cls,v):
        if date.fromisoformat(v).isoformat()!=v:raise ValueError('Invalid date')
        return v


class Invoice(InvoiceSearchItem):
    purpose: Note | None
    note: Note | None
    updated_at: Annotated[str,Field(pattern='Z$')]

    @field_validator('updated_at')
    @classmethod
    def valid_time(cls,v):
        datetime.fromisoformat(v)
        return v


class InvoicePage(Contract):
    items: list[InvoiceSearchItem]
    next_cursor: Cursor | None


class BankTransaction(Contract):
    company_id: Company
    transaction_id: Id
    transaction_date: str
    direction: Literal['income','expense']
    amount: Money
    counterparty: Text500
    note: Note | None

    @field_validator('transaction_date')
    @classmethod
    def valid_date(cls,v):
        if date.fromisoformat(v).isoformat()!=v:raise ValueError('Invalid date')
        return v


class BankPage(Contract):
    items: list[BankTransaction]
    next_cursor: Cursor | None


class Metric(Contract):
    amount: Money
    record_count: Annotated[int,Field(ge=0)]
    empty: bool


class RuleRef(Contract):
    rule_id: Id
    name: Name
    version: Annotated[str,Field(min_length=1,max_length=32)]
    revision: Version


class SimplePolicy(Contract):
    kind: Literal['all','independent_totals','bank_readonly']


class ThresholdPolicy(Contract):
    kind: Literal['amount_gte']
    threshold_cents: Annotated[int,Field(ge=0,le=9223372036854775807)]


Policy = Annotated[SimplePolicy | ThresholdPolicy,Field(discriminator='kind')]


class Rule(RuleRef):
    topic: Topic
    company_ids: Annotated[list[Company],Field(min_length=1)]
    effective_from: str
    status: Literal['enabled','disabled']
    body: Annotated[str,Field(min_length=1,max_length=20000)]
    policy: Policy
    source_ref: Annotated[str,Field(min_length=1,max_length=1000)]

    @field_validator('effective_from')
    @classmethod
    def valid_date(cls,v):
        if date.fromisoformat(v).isoformat()!=v:raise ValueError('Invalid date')
        return v

    @field_validator('company_ids')
    @classmethod
    def unique_companies(cls,v):
        if len(v)!=len(set(v)):raise ValueError('Duplicate companies')
        return v


class RuleResolution(Contract):
    resolution_status: Literal['resolved','missing','conflict','unsupported']
    rules: list[Rule]
    rule_refs: list[RuleRef]


class Totals(Contract):
    company_id: Company
    business_month: Month
    currency: Literal['CNY']
    invoice_total: Metric | None = None
    bank_expense: Metric | None = None
    bank_income: Metric | None = None
    basis_status: Literal['resolved','insufficient_rules','rule_conflict']
    rule_refs: list[RuleRef]

    @model_validator(mode='after')
    def has_metric(self):
        if all(getattr(self,k) is None for k in ('invoice_total','bank_expense','bank_income')):raise ValueError('Metric required')
        return self


class MissingInvoice(Contract):
    company_id: Company
    invoice_id: Id
    amount: Money
    purpose: Note | None
    note: Note | None


class Check(Contract):
    company_id: Company
    business_month: Month
    queried_at: Annotated[str,Field(pattern='Z$')]
    rule_refs: list[RuleRef]
    check_status: Literal['checked','unsupported','insufficient_rules','rule_conflict']
    missing: list[MissingInvoice] | None
    count: Annotated[int,Field(ge=0)] | None

    @field_validator('queried_at')
    @classmethod
    def valid_time(cls,v):
        datetime.fromisoformat(v)
        return v

    @model_validator(mode='after')
    def consistent_check(self):
        if self.check_status=='checked':
            if self.missing is None or self.count!=len(self.missing):raise ValueError('Check count mismatch')
        elif self.missing is not None or self.count is not None:raise ValueError('Unavailable check must have null results')
        return self
