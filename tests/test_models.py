from datetime import date
from decimal import Decimal

import pytest

from invoiceflow.models import Invoice, InvoiceLine, InvoiceStatus


def line(**overrides):
    values = {
        "description": "Implementation",
        "quantity": "2",
        "unit_price": "125.50",
        "tax_rate": "7.25",
    }
    values.update(overrides)
    return InvoiceLine(**values)


def invoice(**overrides):
    values = {
        "number": "INV-100",
        "client_name": "Example Client",
        "issue_date": date(2026, 9, 21),
        "due_date": date(2026, 10, 21),
        "currency": "usd",
        "lines": (line(),),
    }
    values.update(overrides)
    return Invoice(**values)


def test_invoice_normalizes_safe_identifiers():
    record = invoice(number="  INV-100  ", currency="usd")

    assert record.number == "INV-100"
    assert record.client_name == "Example Client"
    assert record.currency == "USD"
    assert record.status is InvoiceStatus.DRAFT


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"number": ""}, "invoice number"),
        ({"client_name": ""}, "client name"),
        ({"currency": "US"}, "three-letter"),
        ({"currency": "U1D"}, "three-letter"),
        ({"lines": ()}, "1 to 100"),
        ({"due_date": date(2026, 9, 20)}, "before issue_date"),
        ({"status": "missing"}, "status"),
    ],
)
def test_invoice_rejects_invalid_records(changes, message):
    with pytest.raises(ValueError, match=message):
        invoice(**changes)


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"description": ""}, "description"),
        ({"quantity": "0"}, "quantity"),
        ({"quantity": "1.00001"}, "decimal places"),
        ({"unit_price": "-0.01"}, "unit_price"),
        ({"unit_price": "1.001"}, "decimal places"),
        ({"tax_rate": "100.001"}, "tax_rate"),
        ({"tax_rate": True}, "decimal"),
    ],
)
def test_line_items_enforce_numeric_and_text_bounds(changes, message):
    with pytest.raises(ValueError, match=message):
        line(**changes)


def test_paid_state_requires_valid_payment_date():
    with pytest.raises(ValueError, match="require paid_at"):
        invoice(status="paid")

    with pytest.raises(ValueError, match="before issue_date"):
        invoice(status="paid", paid_at=date(2026, 9, 20))

    paid = invoice(status="paid", paid_at=date(2026, 9, 22))
    assert paid.paid_at == date(2026, 9, 22)

    with pytest.raises(ValueError, match="only paid"):
        invoice(status="sent", paid_at=date(2026, 9, 22))
