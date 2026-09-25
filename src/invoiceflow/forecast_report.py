"""Aggregate collection forecast reports without invoice-level values."""

from __future__ import annotations

import json
from typing import Any

from .forecast import BUCKET_ORDER, CollectionForecast


def forecast_to_dict(forecast: CollectionForecast) -> dict[str, Any]:
    """Return a stable, value-free forecast report structure."""

    return {
        "schema": 1,
        "report": "collection_forecast",
        "as_of": forecast.as_of.isoformat(),
        "days": forecast.days,
        "attention_required": forecast.attention_required,
        "invoice_count": forecast.invoice_count,
        "overdue_count": forecast.overdue_count,
        "excluded_after_horizon": forecast.excluded_after_horizon,
        "currencies": [
            {
                "currency": currency.currency,
                "invoice_count": currency.invoice_count,
                "amount": f"{currency.amount:.2f}",
                "buckets": {
                    bucket.value: {
                        "count": currency.bucket(bucket).count,
                        "amount": f"{currency.bucket(bucket).amount:.2f}",
                    }
                    for bucket in BUCKET_ORDER
                },
            }
            for currency in forecast.currencies
        ],
    }


def format_forecast(forecast: CollectionForecast, *, as_json: bool = False) -> str:
    """Format an aggregate collection forecast as JSON or readable text."""

    payload = forecast_to_dict(forecast)
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"

    lines = [
        "InvoiceFlow collection forecast",
        f"As of: {payload['as_of']}",
        f"Horizon: {payload['days']} days",
        f"Attention required: {'yes' if payload['attention_required'] else 'no'}",
        f"Included invoices: {payload['invoice_count']}",
        f"Overdue invoices: {payload['overdue_count']}",
        f"Beyond horizon: {payload['excluded_after_horizon']}",
    ]
    for currency in payload["currencies"]:
        lines.append(
            f"{currency['currency']}: {currency['invoice_count']} invoices, "
            f"{currency['amount']}"
        )
        for bucket in BUCKET_ORDER:
            values = currency["buckets"][bucket.value]
            lines.append(
                f"  {bucket.value}: {values['count']} invoices, {values['amount']}"
            )
    return "\n".join(lines) + "\n"
