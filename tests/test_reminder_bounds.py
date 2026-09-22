from datetime import date
from decimal import Decimal

import pytest

from invoiceflow.models import Invoice, InvoiceFlowError, InvoiceLine, InvoiceStatus
from invoiceflow.reminder_policy import ReminderPolicy
from invoiceflow.reminders import ReminderState, plan_reminders


def invoice(number, due):
    return Invoice(
        number=number,
        client_name="Private Client",
        issue_date=date(2026, 1, 1),
        due_date=due,
        currency="USD",
        lines=(InvoiceLine("Private work", Decimal("1"), Decimal("5")),),
        status=InvoiceStatus.SENT,
    )


def test_plan_applies_global_limit_after_stable_priority():
    policy = ReminderPolicy("Bounded", (7, 0), 0, 1, 2)
    as_of = date(2026, 9, 22)
    plan = plan_reminders(
        (
            invoice("UPCOMING", date(2026, 9, 29)),
            invoice("TODAY", as_of),
            invoice("RECENT", date(2026, 9, 21)),
            invoice("OLDEST", date(2026, 9, 1)),
        ),
        policy=policy,
        as_of=as_of,
    )

    assert plan.eligible_count == 4
    assert plan.truncated is True
    assert plan.attention_required is True
    assert [item.number for item in plan.actions] == ["OLDEST", "RECENT"]
    assert plan.overdue == 2


def test_plan_orders_equal_due_dates_by_casefolded_number():
    policy = ReminderPolicy("Stable", (0,), 0, 7, 10)
    as_of = date(2026, 9, 22)
    plan = plan_reminders(
        (invoice("beta", as_of), invoice("Alpha", as_of)),
        policy=policy,
        as_of=as_of,
    )
    assert [item.number for item in plan.actions] == ["Alpha", "beta"]


@pytest.mark.parametrize(
    ("invoices", "as_of"),
    [
        ([], date(2026, 9, 22)),
        ((), "2026-09-22"),
    ],
)
def test_plan_rejects_invalid_inputs(invoices, as_of):
    with pytest.raises(InvoiceFlowError):
        plan_reminders(
            invoices,
            policy=ReminderPolicy("Safe", (0,), 0, 7, 10),
            as_of=as_of,
        )


def test_empty_plan_does_not_require_attention():
    plan = plan_reminders(
        (),
        policy=ReminderPolicy("Safe", (0,), 0, 7, 10),
        as_of=date(2026, 9, 22),
    )
    assert plan.actions == ()
    assert plan.eligible_count == 0
    assert plan.attention_required is False
    assert plan.truncated is False
