import json
from datetime import date
from decimal import Decimal

from invoiceflow.models import Invoice, InvoiceLine
from invoiceflow.payment_performance import analyze_payment_performance
from invoiceflow.payment_performance_report import (
    format_payment_performance,
    payment_performance_to_dict,
)


def private_invoice():
    return Invoice(
        number="SECRET-42",
        client_name="Confidential Customer",
        issue_date=date(2026, 8, 1),
        due_date=date(2026, 8, 31),
        currency="USD",
        lines=(InvoiceLine("Unreleased engagement", Decimal("2"), Decimal("7.50")),),
        status="paid",
        paid_at=date(2026, 9, 9),
    )


def performance():
    return analyze_payment_performance(
        (private_invoice(),),
        from_date=date(2026, 9, 1),
        through_date=date(2026, 9, 30),
        target_days=30,
    )


def test_payment_performance_dict_contains_aggregate_metrics():
    payload = payment_performance_to_dict(performance())
    assert payload["schema"] == 1
    assert payload["report"] == "payment_performance"
    assert payload["attention_required"] is True
    assert payload["invoice_count"] == 1
    assert payload["over_target_count"] == 1
    assert payload["currencies"][0]["amount"] == "15.00"
    assert payload["currencies"][0]["average_days_to_pay"] == "39.00"


def test_payment_performance_formats_omit_invoice_values():
    rendered = format_payment_performance(performance())
    rendered += format_payment_performance(performance(), as_json=True)
    for private_value in (
        "SECRET-42",
        "Confidential Customer",
        "Unreleased engagement",
        "2026-08-01",
        "2026-08-31",
        "2026-09-09",
    ):
        assert private_value not in rendered


def test_json_payment_performance_is_deterministic_and_valid():
    first = format_payment_performance(performance(), as_json=True)
    assert first == format_payment_performance(performance(), as_json=True)
    assert json.loads(first)["window"] == {
        "from": "2026-09-01",
        "through": "2026-09-30",
    }
