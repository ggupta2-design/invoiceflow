from datetime import date
from decimal import Decimal

from invoiceflow.models import Invoice, InvoiceLine, money


def test_line_calculations_use_decimal_half_up_rounding():
    line = InvoiceLine(
        description="Small taxable item",
        quantity="1",
        unit_price="0.05",
        tax_rate="10",
    )

    assert line.subtotal == Decimal("0.05")
    assert line.tax == Decimal("0.01")
    assert line.total == Decimal("0.06")


def test_invoice_totals_sum_rounded_line_values():
    invoice = Invoice(
        number="INV-200",
        client_name="Example Client",
        issue_date=date(2026, 9, 21),
        due_date=date(2026, 10, 1),
        currency="USD",
        lines=(
            InvoiceLine(
                description="Design",
                quantity="2",
                unit_price="125.50",
                tax_rate="7.25",
            ),
            InvoiceLine(
                description="Hosting",
                quantity="1",
                unit_price="20.00",
                tax_rate="0",
            ),
        ),
    )

    assert invoice.subtotal == Decimal("271.00")
    assert invoice.tax == Decimal("18.20")
    assert invoice.total == Decimal("289.20")


def test_fractional_quantities_are_exact_before_cent_rounding():
    line = InvoiceLine(
        description="Consulting hours",
        quantity="1.125",
        unit_price="80.00",
        tax_rate="0",
    )

    assert line.subtotal == Decimal("90.00")
    assert line.total == Decimal("90.00")


def test_money_helper_never_uses_binary_floating_point():
    assert money(Decimal("2.345")) == Decimal("2.35")
    assert money(Decimal("2.344")) == Decimal("2.34")
