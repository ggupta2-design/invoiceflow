"""Privacy-safe aggregate receivables aging."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

from .models import Invoice, InvoiceFlowError, InvoiceStatus, money


class AgingBucket(str, Enum):
    CURRENT = "current"
    DAYS_1_30 = "days_1_30"
    DAYS_31_60 = "days_31_60"
    DAYS_61_90 = "days_61_90"
    DAYS_91_PLUS = "days_91_plus"


_BUCKET_ORDER = tuple(AgingBucket)


@dataclass(frozen=True)
class AgingAmount:
    count: int
    amount: Decimal


@dataclass(frozen=True)
class CurrencyAging:
    currency: str
    buckets: tuple[AgingAmount, ...]

    def __post_init__(self) -> None:
        if len(self.buckets) != len(_BUCKET_ORDER):
            raise InvoiceFlowError("currency aging must contain every aging bucket")

    def bucket(self, name: AgingBucket) -> AgingAmount:
        return self.buckets[_BUCKET_ORDER.index(name)]

    @property
    def invoice_count(self) -> int:
        return sum(item.count for item in self.buckets)

    @property
    def amount(self) -> Decimal:
        return money(sum((item.amount for item in self.buckets), Decimal("0")))

    @property
    def overdue_count(self) -> int:
        return self.invoice_count - self.bucket(AgingBucket.CURRENT).count

    @property
    def overdue_amount(self) -> Decimal:
        return money(self.amount - self.bucket(AgingBucket.CURRENT).amount)


@dataclass(frozen=True)
class ReceivablesAging:
    as_of: date
    currencies: tuple[CurrencyAging, ...]

    @property
    def invoice_count(self) -> int:
        return sum(item.invoice_count for item in self.currencies)

    @property
    def overdue_count(self) -> int:
        return sum(item.overdue_count for item in self.currencies)

    @property
    def attention_required(self) -> bool:
        return self.overdue_count > 0


def classify_aging(due_date: date, *, as_of: date) -> AgingBucket:
    if not isinstance(due_date, date) or not isinstance(as_of, date):
        raise InvoiceFlowError("aging dates must be dates")
    days_overdue = (as_of - due_date).days
    if days_overdue <= 0:
        return AgingBucket.CURRENT
    if days_overdue <= 30:
        return AgingBucket.DAYS_1_30
    if days_overdue <= 60:
        return AgingBucket.DAYS_31_60
    if days_overdue <= 90:
        return AgingBucket.DAYS_61_90
    return AgingBucket.DAYS_91_PLUS


def age_receivables(
    invoices: tuple[Invoice, ...],
    *,
    as_of: date,
) -> ReceivablesAging:
    """Aggregate sent invoices by currency without exposing customer values."""

    if not isinstance(invoices, tuple) or any(
        not isinstance(invoice, Invoice) for invoice in invoices
    ):
        raise InvoiceFlowError("invoices must be a tuple of invoice records")
    if not isinstance(as_of, date):
        raise InvoiceFlowError("as_of must be a date")

    totals: dict[str, dict[AgingBucket, tuple[int, Decimal]]] = {}
    for invoice in invoices:
        if invoice.status is not InvoiceStatus.SENT:
            continue
        bucket = classify_aging(invoice.due_date, as_of=as_of)
        currency = totals.setdefault(
            invoice.currency,
            {name: (0, Decimal("0")) for name in _BUCKET_ORDER},
        )
        count, amount = currency[bucket]
        currency[bucket] = (count + 1, money(amount + invoice.total))

    currencies = []
    for currency in sorted(totals):
        buckets = tuple(
            AgingAmount(count=totals[currency][name][0], amount=totals[currency][name][1])
            for name in _BUCKET_ORDER
        )
        currencies.append(CurrencyAging(currency=currency, buckets=buckets))
    return ReceivablesAging(as_of=as_of, currencies=tuple(currencies))
