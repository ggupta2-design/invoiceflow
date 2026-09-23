import json
from datetime import date, timedelta
from decimal import Decimal

from invoiceflow.aging import age_receivables
from invoiceflow.aging_report import aging_to_dict, format_aging
from invoiceflow.models import Invoice, InvoiceLine, InvoiceStatus


AS_OF = date(2026, 9, 23)


def private_invoice():
    return Invoice(
        number="SECRET-INV-42",
        client_name="Sensitive Customer",
        issue_date=date(2026, 8, 1),
        due_date=AS_OF - timedelta(days=31),
        currency="USD",
        lines=(InvoiceLine("Confidential engagement", Decimal("1"), Decimal("125.50")),),
        status=InvoiceStatus.SENT,
    )


def test_json_aging_report_contains_aggregate_metrics():
    payload = aging_to_dict(age_receivables((private_invoice(),), as_of=AS_OF))

    assert payload["summary"] == {
        "currencies": 1,
        "open_invoices": 1,
        "overdue_invoices": 1,
    }
    assert payload["currencies"][0]["amount"] == "125.50"
    assert payload["currencies"][0]["buckets"]["days_31_60"] == {
        "count": 1,
        "amount": "125.50",
    }


def test_reports_omit_customer_invoice_and_line_values():
    aging = age_receivables((private_invoice(),), as_of=AS_OF)
    text_report = format_aging(aging)
    json_report = format_aging(aging, as_json=True)

    for private_value in (
        "Sensitive Customer",
        "SECRET-INV-42",
        "Confidential engagement",
    ):
        assert private_value not in text_report
        assert private_value not in json_report
    assert "USD 125.50" in text_report


def test_json_report_is_valid_and_deterministic():
    aging = age_receivables((private_invoice(),), as_of=AS_OF)
    first = format_aging(aging, as_json=True)
    second = format_aging(aging, as_json=True)

    assert first == second
    assert json.loads(first)["attention_required"] is True
