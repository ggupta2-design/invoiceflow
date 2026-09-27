import json
from datetime import date
from decimal import Decimal

from invoiceflow.integrity import audit_invoice_integrity
from invoiceflow.integrity_report import (
    format_integrity_audit,
    integrity_audit_to_dict,
)
from invoiceflow.models import Invoice, InvoiceLine


AS_OF = date(2026, 9, 27)


def private_invoice(number):
    return Invoice(
        number=number,
        client_name="Confidential Customer",
        issue_date=date(2026, 9, 28),
        due_date=date(2026, 10, 28),
        currency="USD",
        lines=(InvoiceLine("Secret engagement", Decimal("1"), Decimal("0")),),
        status="sent",
    )


def audit():
    return audit_invoice_integrity(
        (private_invoice("SECRET-1"), private_invoice("SECRET-2")),
        as_of=AS_OF,
    )


def test_integrity_dict_contains_only_aggregate_findings():
    payload = integrity_audit_to_dict(audit())
    assert payload["schema"] == 1
    assert payload["report"] == "invoice_integrity"
    assert payload["attention_required"] is True
    assert payload["invoice_count"] == 2
    assert payload["finding_count"] == 5
    assert payload["findings"] == [
        {"code": "possible_duplicate_invoice", "count": 1},
        {"code": "future_issue_date", "count": 2},
        {"code": "zero_total_active", "count": 2},
    ]


def test_integrity_formats_omit_invoice_values():
    rendered = format_integrity_audit(audit())
    rendered += format_integrity_audit(audit(), as_json=True)
    for private_value in (
        "SECRET-1",
        "SECRET-2",
        "Confidential Customer",
        "Secret engagement",
        "2026-09-28",
        "2026-10-28",
    ):
        assert private_value not in rendered


def test_json_integrity_report_is_deterministic_and_valid():
    first = format_integrity_audit(audit(), as_json=True)
    assert first == format_integrity_audit(audit(), as_json=True)
    assert json.loads(first)["as_of"] == "2026-09-27"
