from datetime import date
from decimal import Decimal

from invoiceflow.integrity import IntegrityCode, audit_invoice_integrity
from invoiceflow.models import Invoice, InvoiceLine, InvoiceStatus


AS_OF = date(2026, 9, 27)


def invoice(number, *, status=InvoiceStatus.SENT, price="0", paid_at=None):
    return Invoice(
        number=number,
        client_name=f"Client {number}",
        issue_date=date(2026, 9, 1),
        due_date=date(2026, 10, 1),
        currency="USD",
        lines=(InvoiceLine("Work", Decimal("1"), Decimal(price)),),
        status=status,
        paid_at=paid_at,
    )


def test_zero_total_finding_excludes_void_records():
    result = audit_invoice_integrity(
        (
            invoice("DRAFT", status=InvoiceStatus.DRAFT),
            invoice("SENT"),
            invoice("PAID", status=InvoiceStatus.PAID, paid_at=AS_OF),
            invoice("VOID", status=InvoiceStatus.VOID),
            invoice("NONZERO", price="1"),
        ),
        as_of=AS_OF,
    )
    assert result.count(IntegrityCode.ZERO_TOTAL_ACTIVE) == 3


def test_clear_audit_has_no_findings():
    result = audit_invoice_integrity(
        (invoice("CLEAR", price="100"),),
        as_of=AS_OF,
    )
    assert result.findings == ()
    assert result.finding_count == 0
    assert not result.attention_required


def test_findings_follow_stable_code_order():
    repeated = InvoiceLine("Repeated", Decimal("1"), Decimal("0"))
    records = (
        Invoice(
            number="A",
            client_name="Same Client",
            issue_date=date(2026, 9, 28),
            due_date=date(2026, 10, 1),
            currency="USD",
            lines=(repeated, repeated),
            status="sent",
        ),
        Invoice(
            number="B",
            client_name="same client",
            issue_date=date(2026, 9, 28),
            due_date=date(2026, 10, 1),
            currency="USD",
            lines=(repeated, repeated),
            status="sent",
        ),
    )
    result = audit_invoice_integrity(records, as_of=AS_OF)
    assert tuple(finding.code for finding in result.findings) == tuple(
        code for code in IntegrityCode if result.count(code)
    )


def test_audit_is_deterministic_for_input_order():
    records = (invoice("B", price="10"), invoice("A", price="20"))
    assert audit_invoice_integrity(
        records, as_of=AS_OF
    ) == audit_invoice_integrity(tuple(reversed(records)), as_of=AS_OF)
