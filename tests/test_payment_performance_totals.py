from datetime import date, timedelta
from decimal import Decimal

from invoiceflow.models import Invoice, InvoiceLine
from invoiceflow.payment_performance import PaymentBucket, analyze_payment_performance


FROM_DATE = date(2026, 9, 1)
THROUGH_DATE = date(2026, 9, 30)


def invoice(number, currency, amount, settlement_days, paid_at):
    issue_date = paid_at - timedelta(days=settlement_days)
    return Invoice(
        number=number,
        client_name="Private Client",
        issue_date=issue_date,
        due_date=issue_date + timedelta(days=30),
        currency=currency,
        lines=(InvoiceLine("Private work", Decimal("1"), Decimal(amount)),),
        status="paid",
        paid_at=paid_at,
    )


def test_performance_separates_currencies_and_exact_amounts():
    result = analyze_payment_performance(
        (
            invoice("U1", "usd", "10.01", 0, date(2026, 9, 5)),
            invoice("U2", "USD", "20.02", 10, date(2026, 9, 15)),
            invoice("E1", "EUR", "30.03", 40, date(2026, 9, 20)),
        ),
        from_date=FROM_DATE,
        through_date=THROUGH_DATE,
        target_days=30,
    )

    assert tuple(item.currency for item in result.currencies) == ("EUR", "USD")
    eur, usd = result.currencies
    assert eur.bucket(PaymentBucket.DAYS_31_60).amount == Decimal("30.03")
    assert eur.average_days_to_pay == Decimal("40.00")
    assert eur.over_target_count == 1
    assert usd.amount == Decimal("30.03")
    assert usd.average_days_to_pay == Decimal("5.00")
    assert result.invoice_count == 3
    assert result.over_target_count == 1


def test_average_days_to_pay_rounds_half_up_to_two_places():
    result = analyze_payment_performance(
        (
            invoice("A", "USD", "1.00", 1, date(2026, 9, 10)),
            invoice("B", "USD", "1.00", 2, date(2026, 9, 11)),
            invoice("C", "USD", "1.00", 2, date(2026, 9, 12)),
        ),
        from_date=FROM_DATE,
        through_date=THROUGH_DATE,
    )
    assert result.currencies[0].average_days_to_pay == Decimal("1.67")


def test_performance_is_deterministic_for_input_order():
    invoices = (
        invoice("A", "USD", "1.00", 5, date(2026, 9, 10)),
        invoice("B", "EUR", "2.00", 10, date(2026, 9, 11)),
    )
    assert analyze_payment_performance(
        invoices, from_date=FROM_DATE, through_date=THROUGH_DATE
    ) == analyze_payment_performance(
        tuple(reversed(invoices)),
        from_date=FROM_DATE,
        through_date=THROUGH_DATE,
    )
