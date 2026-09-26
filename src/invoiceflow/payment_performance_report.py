"""Aggregate payment performance reports without invoice-level values."""

from __future__ import annotations

import json
from typing import Any

from .payment_performance import BUCKET_ORDER, PaymentPerformance


def payment_performance_to_dict(
    performance: PaymentPerformance,
) -> dict[str, Any]:
    """Return a stable aggregate report structure."""

    return {
        "schema": 1,
        "report": "payment_performance",
        "window": {
            "from": performance.from_date.isoformat(),
            "through": performance.through_date.isoformat(),
        },
        "target_days": performance.target_days,
        "attention_required": performance.attention_required,
        "invoice_count": performance.invoice_count,
        "over_target_count": performance.over_target_count,
        "currencies": [
            {
                "currency": currency.currency,
                "invoice_count": currency.invoice_count,
                "amount": f"{currency.amount:.2f}",
                "average_days_to_pay": f"{currency.average_days_to_pay:.2f}",
                "over_target_count": currency.over_target_count,
                "buckets": {
                    bucket.value: {
                        "count": currency.bucket(bucket).count,
                        "amount": f"{currency.bucket(bucket).amount:.2f}",
                    }
                    for bucket in BUCKET_ORDER
                },
            }
            for currency in performance.currencies
        ],
    }


def format_payment_performance(
    performance: PaymentPerformance, *, as_json: bool = False
) -> str:
    """Format payment performance as deterministic JSON or readable text."""

    payload = payment_performance_to_dict(performance)
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"

    lines = [
        "InvoiceFlow payment performance",
        f"Window: {payload['window']['from']} through {payload['window']['through']}",
        f"Target: {payload['target_days']} days",
        f"Attention required: {'yes' if payload['attention_required'] else 'no'}",
        f"Paid invoices: {payload['invoice_count']}",
        f"Over target: {payload['over_target_count']}",
    ]
    for currency in payload["currencies"]:
        lines.append(
            f"{currency['currency']}: {currency['invoice_count']} invoices, "
            f"{currency['amount']}, average {currency['average_days_to_pay']} days"
        )
        for bucket in BUCKET_ORDER:
            values = currency["buckets"][bucket.value]
            lines.append(
                f"  {bucket.value}: {values['count']} invoices, {values['amount']}"
            )
    return "\n".join(lines) + "\n"
