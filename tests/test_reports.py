import json
from datetime import date

from invoiceflow.due import review_due
from invoiceflow.models import Invoice, InvoiceLine
from invoiceflow.report import (
    due_review_to_dict,
    format_due_review,
    format_invoice,
    format_invoice_list,
)


def invoice(number="INV-001", *, status="sent", due=date(2026, 9, 20)):
    return Invoice(
        number=number,
        client_name="Sensitive Client",
        issue_date=date(2026, 9, 1),
        due_date=due,
        currency="USD",
        lines=(InvoiceLine("Private consulting detail", "1", "100.00", "5"),),
        status=status,
    )


def test_invoice_summary_reports_totals_without_line_descriptions():
    report = format_invoice(invoice(), as_json=True)
    payload = json.loads(report)

    assert payload["subtotal"] == "100.00"
    assert payload["tax"] == "5.00"
    assert payload["total"] == "105.00"
    assert "Private consulting detail" not in report


def test_invoice_list_redacts_clients_deterministically():
    report = format_invoice_list(
        (invoice("INV-002"), invoice("INV-001")),
        as_json=True,
        redact_clients=True,
    )
    payload = json.loads(report)

    assert payload["count"] == 2
    assert all(
        item["client_name"] == "[redacted]" for item in payload["invoices"]
    )
    assert "Sensitive Client" not in report


def test_due_report_has_aggregate_status_and_optional_redaction():
    review = review_due(
        (invoice(),),
        as_of=date(2026, 9, 21),
        days=30,
    )

    payload = due_review_to_dict(review, redact_clients=True)
    text = format_due_review(review, redact_clients=True)

    assert payload["attention_required"] is True
    assert payload["summary"]["overdue"] == 1
    assert payload["invoices"][0]["client_name"] == "[redacted]"
    assert "Sensitive Client" not in text
    assert "Overdue: 1" in text


def test_empty_due_report_is_clear():
    review = review_due((), as_of=date(2026, 9, 21), days=30)
    payload = due_review_to_dict(review)

    assert payload["attention_required"] is False
    assert payload["summary"]["invoices"] == 0
