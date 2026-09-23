from datetime import date, timedelta
from decimal import Decimal

from invoiceflow.aging import AgingBucket, age_receivables
from invoiceflow.models import Invoice, InvoiceLine, InvoiceStatus


AS_OF = date(2026, 9, 23)


def invoice(number, currency, amount, days_overdue):
    return Invoice(
        number=number,
        client_name=f"Client {number}",
        issue_date=date(2026, 1, 1),
        due_date=AS_OF - timedelta(days=days_overdue),
        currency=currency,
        lines=(InvoiceLine("Service", Decimal("1"), Decimal(amount)),),
        status=InvoiceStatus.SENT,
    )


def test_aging_keeps_currencies_separate_and_sorted():
    aging = age_receivables(
        (
            invoice("USD-OLD", "USD", "40.10", 91),
            invoice("EUR-NOW", "EUR", "25.25", 0),
            invoice("USD-NEW", "USD", "10.15", 10),
        ),
        as_of=AS_OF,
    )

    assert [item.currency for item in aging.currencies] == ["EUR", "USD"]
    eur, usd = aging.currencies
    assert eur.amount == Decimal("25.25")
    assert eur.overdue_count == 0
    assert usd.amount == Decimal("50.25")
    assert usd.overdue_amount == Decimal("50.25")
    assert usd.bucket(AgingBucket.DAYS_1_30).amount == Decimal("10.15")
    assert usd.bucket(AgingBucket.DAYS_91_PLUS).amount == Decimal("40.10")


def test_aging_summary_counts_overdue_invoices_across_currencies():
    aging = age_receivables(
        (
            invoice("CURRENT", "USD", "5.00", -7),
            invoice("OVERDUE-USD", "USD", "6.00", 1),
            invoice("OVERDUE-EUR", "EUR", "7.00", 31),
        ),
        as_of=AS_OF,
    )

    assert aging.invoice_count == 3
    assert aging.overdue_count == 2
    assert aging.attention_required is True


def test_empty_aging_is_stable_and_needs_no_attention():
    aging = age_receivables((), as_of=AS_OF)

    assert aging.currencies == ()
    assert aging.invoice_count == 0
    assert aging.overdue_count == 0
    assert aging.attention_required is False
