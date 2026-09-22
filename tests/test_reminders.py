from datetime import date
from decimal import Decimal

from invoiceflow.models import Invoice, InvoiceLine, InvoiceStatus
from invoiceflow.reminder_policy import ReminderPolicy
from invoiceflow.reminders import ReminderState, plan_reminders


def invoice(number, due_date, *, status=InvoiceStatus.SENT):
    return Invoice(
        number=number,
        client_name=f"Client {number}",
        issue_date=date(2026, 9, 1),
        due_date=due_date,
        currency="USD",
        lines=(InvoiceLine("Service", Decimal("1"), Decimal("100.00")),),
        status=status,
    )


def policy(**overrides):
    values = {
        "name": "Standard",
        "upcoming_days": (14, 7, 0),
        "overdue_grace_days": 2,
        "overdue_interval_days": 5,
        "maximum_reminders": 50,
    }
    values.update(overrides)
    return ReminderPolicy(**values)


def test_plan_selects_exact_upcoming_and_due_dates():
    as_of = date(2026, 9, 22)
    plan = plan_reminders(
        (
            invoice("DUE", as_of),
            invoice("WEEK", date(2026, 9, 29)),
            invoice("OFF-CADENCE", date(2026, 9, 28)),
            invoice("DRAFT", as_of, status=InvoiceStatus.DRAFT),
            invoice("PAID", as_of, status=InvoiceStatus.PAID),
        ),
        policy=policy(),
        as_of=as_of,
    )

    assert [item.number for item in plan.actions] == ["DUE", "WEEK"]
    assert [item.state for item in plan.actions] == [
        ReminderState.DUE_TODAY,
        ReminderState.UPCOMING,
    ]
    assert plan.due_today == 1
    assert plan.upcoming == 1


def test_overdue_cadence_starts_after_grace_period():
    as_of = date(2026, 9, 22)
    plan = plan_reminders(
        (
            invoice("GRACE", date(2026, 9, 20)),
            invoice("FIRST", date(2026, 9, 19)),
            invoice("BETWEEN", date(2026, 9, 18)),
            invoice("SECOND", date(2026, 9, 14)),
        ),
        policy=policy(),
        as_of=as_of,
    )

    assert [item.number for item in plan.actions] == ["SECOND", "FIRST"]
    assert all(item.state is ReminderState.OVERDUE for item in plan.actions)
    assert [item.days_until_due for item in plan.actions] == [-8, -3]


def test_zero_grace_starts_on_first_overdue_day():
    as_of = date(2026, 9, 22)
    plan = plan_reminders(
        (invoice("FIRST", date(2026, 9, 21)),),
        policy=policy(overdue_grace_days=0),
        as_of=as_of,
    )
    assert [item.number for item in plan.actions] == ["FIRST"]
