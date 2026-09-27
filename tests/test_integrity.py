from datetime import date, timedelta
from decimal import Decimal

import pytest

from invoiceflow.integrity import IntegrityCode, audit_invoice_integrity
from invoiceflow.models import Invoice, InvoiceFlowError, InvoiceLine, InvoiceStatus


AS_OF = date(2026, 9, 27)


def invoice(
    number,
    *,
    client="Private Client",
    issue_date=date(2026, 9, 1),
    lines=None,
    status=InvoiceStatus.SENT,
    paid_at=None,
):
    return Invoice(
        number=number,
        client_name=client,
        issue_date=issue_date,
        due_date=issue_date + timedelta(days=30),
        currency="USD",
        lines=lines
        or (InvoiceLine("Private work", Decimal("1"), Decimal("100")),),
        status=status,
        paid_at=paid_at,
    )


def test_audit_detects_possible_duplicate_invoices_without_numbers():
    result = audit_invoice_integrity(
        (
            invoice("INV-001", client="Private   Client"),
            invoice("INV-002", client="private client"),
            invoice("INV-003", client="Different Client"),
        ),
        as_of=AS_OF,
    )
    assert result.invoice_count == 3
    assert result.count(IntegrityCode.POSSIBLE_DUPLICATE_INVOICE) == 1
    assert result.attention_required


def test_audit_counts_repeated_line_items_beyond_first():
    repeated = InvoiceLine("Same work", Decimal("1"), Decimal("25"))
    result = audit_invoice_integrity(
        (invoice("INV-LINES", lines=(repeated, repeated, repeated)),),
        as_of=AS_OF,
    )
    assert result.count(IntegrityCode.DUPLICATE_LINE_ITEM) == 2


def test_audit_detects_future_record_dates():
    result = audit_invoice_integrity(
        (
            invoice("FUTURE-ISSUE", issue_date=AS_OF + timedelta(days=1)),
            invoice(
                "FUTURE-PAID",
                status=InvoiceStatus.PAID,
                paid_at=AS_OF + timedelta(days=1),
            ),
        ),
        as_of=AS_OF,
    )
    assert result.count(IntegrityCode.FUTURE_ISSUE_DATE) == 1
    assert result.count(IntegrityCode.FUTURE_PAYMENT_DATE) == 1


def test_audit_rejects_invalid_inputs():
    with pytest.raises(InvoiceFlowError):
        audit_invoice_integrity((), as_of="2026-09-27")
    with pytest.raises(InvoiceFlowError):
        audit_invoice_integrity((object(),), as_of=AS_OF)
