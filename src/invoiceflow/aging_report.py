"""Aggregate aging reports that omit invoice and customer identifiers."""

from __future__ import annotations

import json
from typing import Any

from .aging import AgingBucket, ReceivablesAging

_BUCKET_LABELS = {
    AgingBucket.CURRENT: "Current",
    AgingBucket.DAYS_1_30: "1-30 days",
    AgingBucket.DAYS_31_60: "31-60 days",
    AgingBucket.DAYS_61_90: "61-90 days",
    AgingBucket.DAYS_91_PLUS: "91+ days",
}


def aging_to_dict(aging: ReceivablesAging) -> dict[str, Any]:
    return {
        "attention_required": aging.attention_required,
        "as_of": aging.as_of.isoformat(),
        "summary": {
            "currencies": len(aging.currencies),
            "open_invoices": aging.invoice_count,
            "overdue_invoices": aging.overdue_count,
        },
        "currencies": [
            {
                "currency": item.currency,
                "invoice_count": item.invoice_count,
                "amount": str(item.amount),
                "overdue_count": item.overdue_count,
                "overdue_amount": str(item.overdue_amount),
                "buckets": {
                    name.value: {
                        "count": item.bucket(name).count,
                        "amount": str(item.bucket(name).amount),
                    }
                    for name in AgingBucket
                },
            }
            for item in aging.currencies
        ],
    }


def format_aging(
    aging: ReceivablesAging,
    *,
    as_json: bool = False,
) -> str:
    payload = aging_to_dict(aging)
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"

    summary = payload["summary"]
    lines = [
        "InvoiceFlow receivables aging",
        f"As of: {payload['as_of']}",
        f"Currencies: {summary['currencies']}",
        f"Open invoices: {summary['open_invoices']}",
        f"Overdue invoices: {summary['overdue_invoices']}",
    ]
    for currency in aging.currencies:
        lines.append(
            f"{currency.currency}: {currency.invoice_count} invoices, "
            f"{currency.amount} total, {currency.overdue_amount} overdue"
        )
        for bucket in AgingBucket:
            amount = currency.bucket(bucket)
            lines.append(
                f"- {_BUCKET_LABELS[bucket]}: {amount.count}, "
                f"{currency.currency} {amount.amount}"
            )
    return "\n".join(lines) + "\n"
