from datetime import date, timedelta
from decimal import Decimal

import pytest

from invoiceflow.forecast import (
    ForecastBucket,
    classify_due_date,
    forecast_collections,
)
from invoiceflow.models import Invoice, InvoiceFlowError, InvoiceLine, InvoiceStatus


AS_OF = date(2026, 9, 25)


def invoice(number, due, *, status=InvoiceStatus.SENT, paid_at=None, currency="USD"):
    return Invoice(
        number=number,
        client_name="Private Client",
        issue_date=date(2026, 1, 1),
        due_date=due,
        currency=currency,
        lines=(InvoiceLine("Private work", Decimal("1"), Decimal("100")),),
        status=status,
        paid_at=paid_at,
    )


@pytest.mark.parametrize(
    ("offset", "expected"),
    [
        (-1, ForecastBucket.OVERDUE),
        (0, ForecastBucket.DUE_TODAY),
        (1, ForecastBucket.DAYS_1_7),
        (7, ForecastBucket.DAYS_1_7),
        (8, ForecastBucket.DAYS_8_30),
        (30, ForecastBucket.DAYS_8_30),
        (31, ForecastBucket.LATER),
        (90, ForecastBucket.LATER),
        (91, None),
    ],
)
def test_forecast_window_boundaries(offset, expected):
    assert (
        classify_due_date(
            AS_OF + timedelta(days=offset), as_of=AS_OF, days=90
        )
        is expected
    )


def test_forecast_includes_only_sent_invoices():
    result = forecast_collections(
        (
            invoice("SENT", AS_OF),
            invoice("DRAFT", AS_OF, status=InvoiceStatus.DRAFT),
            invoice("PAID", AS_OF, status=InvoiceStatus.PAID, paid_at=AS_OF),
            invoice("VOID", AS_OF, status=InvoiceStatus.VOID),
        ),
        as_of=AS_OF,
    )
    assert result.invoice_count == 1
    assert result.currencies[0].bucket(ForecastBucket.DUE_TODAY).count == 1


@pytest.mark.parametrize("days", [-1, 3651, True, 1.5])
def test_forecast_rejects_invalid_horizons(days):
    with pytest.raises(InvoiceFlowError):
        forecast_collections((), as_of=AS_OF, days=days)


def test_zero_day_horizon_keeps_overdue_and_due_today():
    result = forecast_collections(
        (
            invoice("OLD", AS_OF - timedelta(days=1)),
            invoice("TODAY", AS_OF),
            invoice("TOMORROW", AS_OF + timedelta(days=1)),
        ),
        as_of=AS_OF,
        days=0,
    )
    assert result.invoice_count == 2
    assert result.excluded_after_horizon == 1
    assert result.attention_required
