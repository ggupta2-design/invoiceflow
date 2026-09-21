"""Deterministic due and overdue invoice reviews."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum

from .models import Invoice, InvoiceFlowError, InvoiceStatus


class DueState(str, Enum):
    OVERDUE = "overdue"
    DUE_TODAY = "due_today"
    UPCOMING = "upcoming"


@dataclass(frozen=True)
class DueInvoice:
    number: str
    client_name: str
    due_date: date
    currency: str
    amount: Decimal
    state: DueState
    days_until_due: int


@dataclass(frozen=True)
class DueReview:
    as_of: date
    days: int
    invoices: tuple[DueInvoice, ...]

    @property
    def overdue(self) -> int:
        return sum(item.state is DueState.OVERDUE for item in self.invoices)

    @property
    def due_today(self) -> int:
        return sum(item.state is DueState.DUE_TODAY for item in self.invoices)

    @property
    def upcoming(self) -> int:
        return sum(item.state is DueState.UPCOMING for item in self.invoices)

    @property
    def attention_required(self) -> bool:
        return self.overdue > 0


def review_due(
    invoices: tuple[Invoice, ...],
    *,
    as_of: date,
    days: int = 30,
) -> DueReview:
    """Return sent invoices due by the end of a bounded review horizon."""

    if not isinstance(as_of, date):
        raise InvoiceFlowError("as_of must be a date")
    if isinstance(days, bool) or not isinstance(days, int) or not 0 <= days <= 3650:
        raise InvoiceFlowError("days must be from 0 to 3650")
    horizon = as_of + timedelta(days=days)
    reviewed = []
    for invoice in invoices:
        if invoice.status is not InvoiceStatus.SENT:
            continue
        if invoice.due_date > horizon:
            continue
        delta = (invoice.due_date - as_of).days
        state = (
            DueState.OVERDUE
            if delta < 0
            else DueState.DUE_TODAY
            if delta == 0
            else DueState.UPCOMING
        )
        reviewed.append(
            DueInvoice(
                number=invoice.number,
                client_name=invoice.client_name,
                due_date=invoice.due_date,
                currency=invoice.currency,
                amount=invoice.total,
                state=state,
                days_until_due=delta,
            )
        )
    order = {
        DueState.OVERDUE: 0,
        DueState.DUE_TODAY: 1,
        DueState.UPCOMING: 2,
    }
    return DueReview(
        as_of=as_of,
        days=days,
        invoices=tuple(
            sorted(
                reviewed,
                key=lambda item: (
                    order[item.state],
                    item.due_date,
                    item.number.casefold(),
                ),
            )
        ),
    )
