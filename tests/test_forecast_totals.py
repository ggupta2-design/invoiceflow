from datetime import date, timedelta
from decimal import Decimal

from invoiceflow.forecast import ForecastBucket, forecast_collections
from invoiceflow.models import Invoice, InvoiceLine


AS_OF = date(2026, 9, 25)


def invoice(number, due, currency, amount):
    return Invoice(
        number=number,
        client_name="Private Client",
        issue_date=date(2026, 1, 1),
        due_date=due,
        currency=currency,
        lines=(InvoiceLine("Private work", Decimal("1"), Decimal(amount)),),
        status="sent",
    )


def test_forecast_separates_currencies_and_uses_exact_totals():
    result = forecast_collections(
        (
            invoice("U1", AS_OF - timedelta(days=3), "usd", "10.01"),
            invoice("U2", AS_OF - timedelta(days=1), "USD", "20.02"),
            invoice("E1", AS_OF + timedelta(days=7), "EUR", "30.03"),
            invoice("U3", AS_OF + timedelta(days=20), "USD", "40.04"),
        ),
        as_of=AS_OF,
        days=30,
    )

    assert tuple(item.currency for item in result.currencies) == ("EUR", "USD")
    eur, usd = result.currencies
    assert eur.bucket(ForecastBucket.DAYS_1_7).amount == Decimal("30.03")
    assert usd.bucket(ForecastBucket.OVERDUE).count == 2
    assert usd.bucket(ForecastBucket.OVERDUE).amount == Decimal("30.03")
    assert usd.amount == Decimal("70.07")
    assert result.invoice_count == 4
    assert result.overdue_count == 2


def test_forecast_counts_sent_invoices_after_horizon_without_values():
    result = forecast_collections(
        (
            invoice("NEAR", AS_OF + timedelta(days=30), "USD", "1.00"),
            invoice("FAR-USD", AS_OF + timedelta(days=31), "USD", "999.00"),
            invoice("FAR-EUR", AS_OF + timedelta(days=100), "EUR", "888.00"),
        ),
        as_of=AS_OF,
        days=30,
    )

    assert result.invoice_count == 1
    assert result.excluded_after_horizon == 2
    assert tuple(item.currency for item in result.currencies) == ("USD",)


def test_forecast_is_deterministic_for_input_order():
    invoices = (
        invoice("A", AS_OF, "USD", "1.00"),
        invoice("B", AS_OF + timedelta(days=8), "EUR", "2.00"),
    )
    assert forecast_collections(invoices, as_of=AS_OF) == forecast_collections(
        tuple(reversed(invoices)), as_of=AS_OF
    )
