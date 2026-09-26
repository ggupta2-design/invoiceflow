from datetime import date, timedelta
from decimal import Decimal

import pytest

from invoiceflow.models import Invoice, InvoiceFlowError, InvoiceLine, InvoiceStatus
from invoiceflow.payment_performance import (
    PaymentBucket,
    analyze_payment_performance,
    classify_settlement_days,
)


FROM_DATE = date(2026, 9, 1)
THROUGH_DATE = date(2026, 9, 30)


def invoice(
    number,
    *,
    issue_date=date(2026, 9, 1),
    paid_at=date(2026, 9, 15),
    status=InvoiceStatus.PAID,
):
    return Invoice(
        number=number,
        client_name="Private Client",
        issue_date=issue_date,
        due_date=issue_date + timedelta(days=30),
        currency="USD",
        lines=(InvoiceLine("Private work", Decimal("1"), Decimal("100")),),
        status=status,
        paid_at=paid_at if status is InvoiceStatus.PAID else None,
    )


@pytest.mark.parametrize(
    ("days", "expected"),
    [
        (0, PaymentBucket.SAME_DAY),
        (1, PaymentBucket.DAYS_1_7),
        (7, PaymentBucket.DAYS_1_7),
        (8, PaymentBucket.DAYS_8_30),
        (30, PaymentBucket.DAYS_8_30),
        (31, PaymentBucket.DAYS_31_60),
        (60, PaymentBucket.DAYS_31_60),
        (61, PaymentBucket.DAYS_61_PLUS),
        (500, PaymentBucket.DAYS_61_PLUS),
    ],
)
def test_payment_bucket_boundaries(days, expected):
    assert classify_settlement_days(days) is expected


def test_performance_includes_only_paid_invoices_in_window():
    result = analyze_payment_performance(
        (
            invoice("PAID"),
            invoice("BEFORE", paid_at=date(2026, 8, 31)),
            invoice("AFTER", paid_at=date(2026, 10, 1)),
            invoice("SENT", status=InvoiceStatus.SENT),
            invoice("DRAFT", status=InvoiceStatus.DRAFT),
            invoice("VOID", status=InvoiceStatus.VOID),
        ),
        from_date=FROM_DATE,
        through_date=THROUGH_DATE,
    )
    assert result.invoice_count == 1
    assert result.currencies[0].bucket(PaymentBucket.DAYS_8_30).count == 1


@pytest.mark.parametrize(
    ("start", "end", "target"),
    [
        ("2026-09-01", THROUGH_DATE, 30),
        (FROM_DATE, "2026-09-30", 30),
        (date(2026, 10, 1), THROUGH_DATE, 30),
        (FROM_DATE, FROM_DATE + timedelta(days=3651), 30),
        (FROM_DATE, THROUGH_DATE, -1),
        (FROM_DATE, THROUGH_DATE, 3651),
        (FROM_DATE, THROUGH_DATE, True),
    ],
)
def test_performance_rejects_invalid_bounds(start, end, target):
    with pytest.raises(InvoiceFlowError):
        analyze_payment_performance(
            (), from_date=start, through_date=end, target_days=target
        )


def test_target_is_exceeded_only_by_longer_payments():
    result = analyze_payment_performance(
        (
            invoice("AT-TARGET", paid_at=date(2026, 9, 11)),
            invoice("OVER-TARGET", paid_at=date(2026, 9, 12)),
        ),
        from_date=FROM_DATE,
        through_date=THROUGH_DATE,
        target_days=10,
    )
    assert result.over_target_count == 1
    assert result.attention_required
