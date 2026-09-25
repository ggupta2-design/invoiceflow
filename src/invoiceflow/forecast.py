"""Privacy-safe, read-only cash collection forecasting."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Iterable

from .models import Invoice, InvoiceFlowError, InvoiceStatus, money


class ForecastBucket(str, Enum):
    """Stable due-date windows used by collection forecasts."""

    OVERDUE = "overdue"
    DUE_TODAY = "due_today"
    DAYS_1_7 = "days_1_7"
    DAYS_8_30 = "days_8_30"
    LATER = "later"


BUCKET_ORDER = tuple(ForecastBucket)


@dataclass(frozen=True, slots=True)
class ForecastAmount:
    """Aggregate invoice count and exact amount for one window."""

    count: int
    amount: Decimal


@dataclass(frozen=True, slots=True)
class CurrencyForecast:
    """Collection forecast for one currency."""

    currency: str
    buckets: tuple[ForecastAmount, ...]

    def __post_init__(self) -> None:
        if len(self.buckets) != len(BUCKET_ORDER):
            raise InvoiceFlowError("currency forecast must contain every bucket")

    def bucket(self, bucket: ForecastBucket) -> ForecastAmount:
        return self.buckets[BUCKET_ORDER.index(bucket)]

    @property
    def invoice_count(self) -> int:
        return sum(item.count for item in self.buckets)

    @property
    def amount(self) -> Decimal:
        return money(sum((item.amount for item in self.buckets), Decimal("0")))


@dataclass(frozen=True, slots=True)
class CollectionForecast:
    """Bounded aggregate forecast that never retains invoice identity."""

    as_of: date
    days: int
    currencies: tuple[CurrencyForecast, ...]
    excluded_after_horizon: int

    @property
    def invoice_count(self) -> int:
        return sum(item.invoice_count for item in self.currencies)

    @property
    def overdue_count(self) -> int:
        return sum(
            item.bucket(ForecastBucket.OVERDUE).count for item in self.currencies
        )

    @property
    def attention_required(self) -> bool:
        return self.overdue_count > 0


def classify_due_date(
    due_date: date, *, as_of: date, days: int
) -> ForecastBucket | None:
    """Classify a due date, returning None when it is beyond the horizon."""

    _validate_forecast_inputs(as_of, days)
    if not isinstance(due_date, date):
        raise InvoiceFlowError("due_date must be a date")
    offset = (due_date - as_of).days
    if offset < 0:
        return ForecastBucket.OVERDUE
    if offset == 0:
        return ForecastBucket.DUE_TODAY
    if offset > days:
        return None
    if offset <= 7:
        return ForecastBucket.DAYS_1_7
    if offset <= 30:
        return ForecastBucket.DAYS_8_30
    if offset <= days:
        return ForecastBucket.LATER
    return None


def forecast_collections(
    invoices: Iterable[Invoice], *, as_of: date, days: int = 90
) -> CollectionForecast:
    """Aggregate sent invoices by currency and bounded due-date window."""

    _validate_forecast_inputs(as_of, days)
    totals: dict[str, dict[ForecastBucket, list[Decimal | int]]] = {}
    excluded = 0
    for invoice in invoices:
        if not isinstance(invoice, Invoice):
            raise InvoiceFlowError("forecast entries must be invoices")
        if invoice.status is not InvoiceStatus.SENT:
            continue
        bucket = classify_due_date(invoice.due_date, as_of=as_of, days=days)
        if bucket is None:
            excluded += 1
            continue
        currency = totals.setdefault(
            invoice.currency,
            {key: [0, Decimal("0")] for key in BUCKET_ORDER},
        )
        currency[bucket][0] += 1
        currency[bucket][1] += invoice.total

    forecasts = tuple(
        CurrencyForecast(
            currency=currency,
            buckets=tuple(
                ForecastAmount(
                    count=int(values[bucket][0]),
                    amount=money(values[bucket][1]),
                )
                for bucket in BUCKET_ORDER
            ),
        )
        for currency, values in sorted(totals.items())
    )
    return CollectionForecast(
        as_of=as_of,
        days=days,
        currencies=forecasts,
        excluded_after_horizon=excluded,
    )


def _validate_forecast_inputs(as_of: date, days: int) -> None:
    if not isinstance(as_of, date):
        raise InvoiceFlowError("as_of must be a date")
    if isinstance(days, bool) or not isinstance(days, int) or not 0 <= days <= 3650:
        raise InvoiceFlowError("days must be an integer between 0 and 3650")
