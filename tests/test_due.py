from datetime import date

import pytest

from invoiceflow.due import DueState, review_due
from invoiceflow.models import Invoice, InvoiceLine


AS_OF = date(2026, 9, 21)


def invoice(number, due_date, *, status="sent"):
    return Invoice(
        number=number,
        client_name=f"Client {number}",
        issue_date=date(2026, 9, 1),
        due_date=due_date,
        currency="USD",
        lines=(InvoiceLine("Service", "1", "100.00"),),
        status=status,
        paid_at=AS_OF if status == "paid" else None,
    )


def test_due_review_classifies_and_orders_sent_invoices():
    invoices = (
        invoice("UPCOMING", date(2026, 9, 25)),
        invoice("TODAY", AS_OF),
        invoice("OVERDUE-B", date(2026, 9, 20)),
        invoice("OVERDUE-A", date(2026, 9, 20)),
        invoice("LATER", date(2026, 11, 1)),
    )

    review = review_due(invoices, as_of=AS_OF, days=10)

    assert [item.number for item in review.invoices] == [
        "OVERDUE-A",
        "OVERDUE-B",
        "TODAY",
        "UPCOMING",
    ]
    assert [item.state for item in review.invoices] == [
        DueState.OVERDUE,
        DueState.OVERDUE,
        DueState.DUE_TODAY,
        DueState.UPCOMING,
    ]
    assert review.overdue == 2
    assert review.due_today == 1
    assert review.upcoming == 1
    assert review.attention_required


def test_due_review_excludes_drafts_paid_void_and_later_items():
    invoices = (
        invoice("DRAFT", AS_OF, status="draft"),
        invoice("PAID", AS_OF, status="paid"),
        invoice("VOID", AS_OF, status="void"),
        invoice("LATER", date(2026, 10, 31)),
    )

    review = review_due(invoices, as_of=AS_OF, days=30)

    assert review.invoices == ()
    assert not review.attention_required


def test_review_horizon_is_inclusive():
    review = review_due(
        (invoice("EDGE", date(2026, 10, 1)),),
        as_of=AS_OF,
        days=10,
    )

    assert review.invoices[0].days_until_due == 10


@pytest.mark.parametrize("days", [True, -1, 3651, 1.5])
def test_review_rejects_invalid_horizons(days):
    with pytest.raises(ValueError, match="days"):
        review_due((), as_of=AS_OF, days=days)
