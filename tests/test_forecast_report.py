import json
from datetime import date, timedelta
from decimal import Decimal

from invoiceflow.forecast import forecast_collections
from invoiceflow.forecast_report import format_forecast, forecast_to_dict
from invoiceflow.models import Invoice, InvoiceLine


AS_OF = date(2026, 9, 25)


def private_invoice():
    return Invoice(
        number="SECRET-42",
        client_name="Confidential Customer",
        issue_date=date(2026, 9, 1),
        due_date=AS_OF - timedelta(days=2),
        currency="USD",
        lines=(InvoiceLine("Unreleased engagement", Decimal("2"), Decimal("7.50")),),
        status="sent",
    )


def test_forecast_dict_contains_aggregate_metrics():
    payload = forecast_to_dict(
        forecast_collections((private_invoice(),), as_of=AS_OF, days=30)
    )
    assert payload["schema"] == 1
    assert payload["report"] == "collection_forecast"
    assert payload["attention_required"] is True
    assert payload["invoice_count"] == 1
    assert payload["currencies"][0]["amount"] == "15.00"
    assert payload["currencies"][0]["buckets"]["overdue"] == {
        "count": 1,
        "amount": "15.00",
    }


def test_forecast_formats_never_disclose_invoice_values():
    forecast = forecast_collections((private_invoice(),), as_of=AS_OF, days=30)
    rendered = format_forecast(forecast) + format_forecast(forecast, as_json=True)
    for private_value in (
        "SECRET-42",
        "Confidential Customer",
        "Unreleased engagement",
        "2026-09-01",
        "2026-09-23",
    ):
        assert private_value not in rendered


def test_json_forecast_is_deterministic_and_valid():
    forecast = forecast_collections((private_invoice(),), as_of=AS_OF)
    first = format_forecast(forecast, as_json=True)
    assert first == format_forecast(forecast, as_json=True)
    assert json.loads(first)["as_of"] == "2026-09-25"
