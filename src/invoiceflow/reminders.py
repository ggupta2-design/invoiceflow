"""Read-only payment reminder planning without message delivery."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

from .models import Invoice, InvoiceFlowError, InvoiceStatus
from .reminder_policy import ReminderPolicy


class ReminderState(str, Enum):
    OVERDUE = "overdue"
    DUE_TODAY = "due_today"
    UPCOMING = "upcoming"


@dataclass(frozen=True)
class ReminderAction:
    number: str
    client_name: str
    due_date: date
    currency: str
    amount: Decimal
    state: ReminderState
    days_until_due: int


@dataclass(frozen=True)
class ReminderPlan:
    policy_name: str
    as_of: date
    actions: tuple[ReminderAction, ...]
    eligible_count: int

    @property
    def truncated(self) -> bool:
        return self.eligible_count > len(self.actions)

    @property
    def overdue(self) -> int:
        return sum(item.state is ReminderState.OVERDUE for item in self.actions)

    @property
    def due_today(self) -> int:
        return sum(item.state is ReminderState.DUE_TODAY for item in self.actions)

    @property
    def upcoming(self) -> int:
        return sum(item.state is ReminderState.UPCOMING for item in self.actions)

    @property
    def attention_required(self) -> bool:
        return bool(self.actions) or self.truncated


def _state_for(
    invoice: Invoice,
    *,
    policy: ReminderPolicy,
    as_of: date,
) -> tuple[ReminderState, int] | None:
    days_until_due = (invoice.due_date - as_of).days
    if days_until_due >= 0:
        if days_until_due not in policy.upcoming_days:
            return None
        state = (
            ReminderState.DUE_TODAY
            if days_until_due == 0
            else ReminderState.UPCOMING
        )
        return state, days_until_due

    days_overdue = -days_until_due
    if days_overdue <= policy.overdue_grace_days:
        return None
    cadence_day = days_overdue - policy.overdue_grace_days - 1
    if cadence_day % policy.overdue_interval_days:
        return None
    return ReminderState.OVERDUE, days_until_due


def plan_reminders(
    invoices: tuple[Invoice, ...],
    *,
    policy: ReminderPolicy,
    as_of: date,
) -> ReminderPlan:
    """Plan bounded reminder actions for sent invoices without sending them."""

    if not isinstance(invoices, tuple) or any(
        not isinstance(invoice, Invoice) for invoice in invoices
    ):
        raise InvoiceFlowError("invoices must be a tuple of invoice records")
    if not isinstance(policy, ReminderPolicy):
        raise InvoiceFlowError("policy must be a reminder policy")
    if not isinstance(as_of, date):
        raise InvoiceFlowError("as_of must be a date")

    eligible = []
    for invoice in invoices:
        if invoice.status is not InvoiceStatus.SENT:
            continue
        result = _state_for(invoice, policy=policy, as_of=as_of)
        if result is None:
            continue
        state, days_until_due = result
        eligible.append(
            ReminderAction(
                number=invoice.number,
                client_name=invoice.client_name,
                due_date=invoice.due_date,
                currency=invoice.currency,
                amount=invoice.total,
                state=state,
                days_until_due=days_until_due,
            )
        )

    priority = {
        ReminderState.OVERDUE: 0,
        ReminderState.DUE_TODAY: 1,
        ReminderState.UPCOMING: 2,
    }
    ordered = tuple(
        sorted(
            eligible,
            key=lambda item: (
                priority[item.state],
                item.due_date,
                item.number.casefold(),
            ),
        )
    )
    return ReminderPlan(
        policy_name=policy.name,
        as_of=as_of,
        actions=ordered[: policy.maximum_reminders],
        eligible_count=len(ordered),
    )
