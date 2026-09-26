"""Read-only, privacy-safe payment performance analytics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Iterable

from .models import Invoice, InvoiceFlowError, InvoiceStatus, money


class PaymentBucket(str, Enum):
    """Stable settlement-time windows."""

    SAME_DAY = "same_day"
    DAYS_1_7 = "days_1_7"
    DAYS_8_30 = "days_8_30"
    DAYS_31_60 = "days_31_60"
    DAYS_61_PLUS = "days_61_plus"


BUCKET_ORDER = tuple(PaymentBucket)
_AVERAGE_PLACES = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class PaymentAmount:
    """Aggregate count and exact amount for one settlement window."""

    count: int
    amount: Decimal


@dataclass(frozen=True, slots=True)
class CurrencyPaymentPerformance:
    """Aggregate payment performance for one currency."""

    currency: str
    buckets: tuple[PaymentAmount, ...]
    settlement_days_total: int
    over_target_count: int

    def __post_init__(self) -> None:
        if len(self.buckets) != len(BUCKET_ORDER):
            raise InvoiceFlowError("payment performance must contain every bucket")

    def bucket(self, bucket: PaymentBucket) -> PaymentAmount:
        return self.buckets[BUCKET_ORDER.index(bucket)]

    @property
    def invoice_count(self) -> int:
        return sum(item.count for item in self.buckets)

    @property
    def amount(self) -> Decimal:
        return money(sum((item.amount for item in self.buckets), Decimal("0")))

    @property
    def average_days_to_pay(self) -> Decimal:
        if not self.invoice_count:
            return Decimal("0.00")
        return (
            Decimal(self.settlement_days_total) / Decimal(self.invoice_count)
        ).quantize(_AVERAGE_PLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True, slots=True)
class PaymentPerformance:
    """Bounded portfolio payment performance without invoice identities."""

    from_date: date
    through_date: date
    target_days: int
    currencies: tuple[CurrencyPaymentPerformance, ...]

    @property
    def invoice_count(self) -> int:
        return sum(item.invoice_count for item in self.currencies)

    @property
    def over_target_count(self) -> int:
        return sum(item.over_target_count for item in self.currencies)

    @property
    def attention_required(self) -> bool:
        return self.over_target_count > 0


def classify_settlement_days(days: int) -> PaymentBucket:
    """Classify a non-negative issue-to-payment duration."""

    if isinstance(days, bool) or not isinstance(days, int) or days < 0:
        raise InvoiceFlowError("settlement days must be a non-negative integer")
    if days == 0:
        return PaymentBucket.SAME_DAY
    if days <= 7:
        return PaymentBucket.DAYS_1_7
    if days <= 30:
        return PaymentBucket.DAYS_8_30
    if days <= 60:
        return PaymentBucket.DAYS_31_60
    return PaymentBucket.DAYS_61_PLUS


def analyze_payment_performance(
    invoices: Iterable[Invoice],
    *,
    from_date: date,
    through_date: date,
    target_days: int = 30,
) -> PaymentPerformance:
    """Aggregate paid invoices whose payment dates fall inside the window."""

    _validate_inputs(from_date, through_date, target_days)
    totals: dict[str, dict[str, object]] = {}
    for invoice in invoices:
        if not isinstance(invoice, Invoice):
            raise InvoiceFlowError("payment performance entries must be invoices")
        if invoice.status is not InvoiceStatus.PAID:
            continue
        assert invoice.paid_at is not None
        if not from_date <= invoice.paid_at <= through_date:
            continue
        settlement_days = (invoice.paid_at - invoice.issue_date).days
        bucket = classify_settlement_days(settlement_days)
        currency = totals.setdefault(
            invoice.currency,
            {
                "buckets": {
                    key: [0, Decimal("0")] for key in BUCKET_ORDER
                },
                "days": 0,
                "over_target": 0,
            },
        )
        values = currency["buckets"][bucket]
        values[0] += 1
        values[1] += invoice.total
        currency["days"] += settlement_days
        if settlement_days > target_days:
            currency["over_target"] += 1

    currencies = tuple(
        CurrencyPaymentPerformance(
            currency=code,
            buckets=tuple(
                PaymentAmount(
                    count=int(values["buckets"][bucket][0]),
                    amount=money(values["buckets"][bucket][1]),
                )
                for bucket in BUCKET_ORDER
            ),
            settlement_days_total=int(values["days"]),
            over_target_count=int(values["over_target"]),
        )
        for code, values in sorted(totals.items())
    )
    return PaymentPerformance(
        from_date=from_date,
        through_date=through_date,
        target_days=target_days,
        currencies=currencies,
    )


def _validate_inputs(from_date: date, through_date: date, target_days: int) -> None:
    if not isinstance(from_date, date) or not isinstance(through_date, date):
        raise InvoiceFlowError("payment window values must be dates")
    if from_date > through_date:
        raise InvoiceFlowError("from_date cannot be after through_date")
    if (through_date - from_date).days > 3650:
        raise InvoiceFlowError("payment window cannot exceed 3650 days")
    if (
        isinstance(target_days, bool)
        or not isinstance(target_days, int)
        or not 0 <= target_days <= 3650
    ):
        raise InvoiceFlowError("target_days must be an integer between 0 and 3650")
