from datetime import date, timedelta
from decimal import Decimal

import pytest

from invoiceflow.aging import AgingBucket, age_receivables, classify_aging
from invoiceflow.models import Invoice, InvoiceFlowError, InvoiceLine, InvoiceStatus


AS_OF = date(2026, 9, 23)


def invoice(number, due, *, status=InvoiceStatus.SENT, paid_at=None):
    return Invoice(
        number=number,
        client_name="Private Client",
        issue_date=date(2026, 1, 1),
        due_date=due,
        currency="USD",
        lines=(InvoiceLine("Private work", Decimal("1"), Decimal("100")),),
        status=status,
        paid_at=paid_at,
    )


@pytest.mark.parametrize(
    ("days_overdue", "expected"),
    [
        (-10, AgingBucket.CURRENT),
        (0, AgingBucket.CURRENT),
        (1, AgingBucket.DAYS_1_30),
        (30, AgingBucket.DAYS_1_30),
        (31, AgingBucket.DAYS_31_60),
        (60, AgingBucket.DAYS_31_60),
        (61, AgingBucket.DAYS_61_90),
        (90, AgingBucket.DAYS_61_90),
        (91, AgingBucket.DAYS_91_PLUS),
        (500, AgingBucket.DAYS_91_PLUS),
    ],
)
def test_classify_aging_boundaries(days_overdue, expected):
    due = AS_OF - timedelta(days=days_overdue)
    assert classify_aging(due, as_of=AS_OF) is expected


def test_aging_includes_only_sent_invoices():
    aging = age_receivables(
        (
            invoice("SENT", AS_OF),
            invoice("DRAFT", AS_OF, status=InvoiceStatus.DRAFT),
            invoice(
                "PAID",
                AS_OF,
                status=InvoiceStatus.PAID,
                paid_at=AS_OF,
            ),
            invoice("VOID", AS_OF, status=InvoiceStatus.VOID),
        ),
        as_of=AS_OF,
    )

    assert aging.invoice_count == 1
    assert aging.currencies[0].bucket(AgingBucket.CURRENT).count == 1


def test_aging_rejects_invalid_inputs():
    with pytest.raises(InvoiceFlowError):
        age_receivables([], as_of=AS_OF)
    with pytest.raises(InvoiceFlowError):
        age_receivables((), as_of="2026-09-23")
