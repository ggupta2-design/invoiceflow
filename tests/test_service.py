from datetime import date

import pytest

from invoiceflow.models import Invoice, InvoiceLine, InvoiceStatus
from invoiceflow.service import InvoiceService
from invoiceflow.storage import InvoiceLedger


def invoice(number="INV-001"):
    return Invoice(
        number=number,
        client_name="Fictional Client",
        issue_date=date(2026, 9, 21),
        due_date=date(2026, 10, 21),
        currency="USD",
        lines=(InvoiceLine("Service", "1", "100.00"),),
    )


def service(tmp_path):
    return InvoiceService(InvoiceLedger(tmp_path / "ledger.json"))


def test_create_get_and_list_are_deterministic(tmp_path):
    invoices = service(tmp_path)
    invoices.create(invoice("INV-002"))
    invoices.create(invoice("INV-001"))

    assert invoices.get(" inv-001 ").number == "INV-001"
    assert [item.number for item in invoices.list()] == ["INV-001", "INV-002"]


def test_create_rejects_duplicate_and_get_hides_ledger_details(tmp_path):
    invoices = service(tmp_path)
    invoices.create(invoice("INV-001"))

    with pytest.raises(ValueError, match="already exists"):
        invoices.create(invoice("inv-001"))
    with pytest.raises(ValueError, match="not found"):
        invoices.get("private-customer-reference")


def test_status_filters_accept_enum_or_string(tmp_path):
    invoices = service(tmp_path)
    invoices.create(invoice("INV-001"))
    invoices.transition("INV-001", "sent")
    invoices.create(invoice("INV-002"))

    assert [item.number for item in invoices.list(status="sent")] == ["INV-001"]
    assert [item.number for item in invoices.list(status=InvoiceStatus.DRAFT)] == [
        "INV-002"
    ]


def test_lifecycle_requires_explicit_legal_transitions(tmp_path):
    invoices = service(tmp_path)
    invoices.create(invoice())

    with pytest.raises(ValueError, match="cannot transition"):
        invoices.transition("INV-001", "paid", on_date=date(2026, 9, 22))

    sent = invoices.transition("INV-001", "sent")
    assert sent.status is InvoiceStatus.SENT

    with pytest.raises(ValueError, match="already"):
        invoices.transition("INV-001", "sent")
    with pytest.raises(ValueError, match="requires on_date"):
        invoices.transition("INV-001", "paid")

    paid = invoices.transition(
        "INV-001", "paid", on_date=date(2026, 9, 22)
    )
    assert paid.status is InvoiceStatus.PAID
    assert paid.paid_at == date(2026, 9, 22)
    assert invoices.get("INV-001") == paid

    with pytest.raises(ValueError, match="cannot transition"):
        invoices.transition("INV-001", "void")


def test_void_transition_is_terminal_and_rejects_payment_date(tmp_path):
    invoices = service(tmp_path)
    invoices.create(invoice())

    with pytest.raises(ValueError, match="only supported"):
        invoices.transition("INV-001", "void", on_date=date(2026, 9, 22))

    void = invoices.transition("INV-001", "void")
    assert void.status is InvoiceStatus.VOID

    with pytest.raises(ValueError, match="cannot transition"):
        invoices.transition("INV-001", "sent")
