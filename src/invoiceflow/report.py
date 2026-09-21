"""Deterministic invoice and due-review reports."""

from __future__ import annotations

import json
from typing import Any

from .due import DueReview
from .models import Invoice


def _client(name: str, redact: bool) -> str:
    return "[redacted]" if redact else name


def invoice_summary_to_dict(
    invoice: Invoice,
    *,
    redact_client: bool = False,
) -> dict[str, Any]:
    return {
        "number": invoice.number,
        "client_name": _client(invoice.client_name, redact_client),
        "issue_date": invoice.issue_date.isoformat(),
        "due_date": invoice.due_date.isoformat(),
        "currency": invoice.currency,
        "status": invoice.status.value,
        "paid_at": invoice.paid_at.isoformat() if invoice.paid_at else None,
        "line_count": len(invoice.lines),
        "subtotal": str(invoice.subtotal),
        "tax": str(invoice.tax),
        "total": str(invoice.total),
    }


def format_invoice(
    invoice: Invoice,
    *,
    as_json: bool = False,
    redact_client: bool = False,
) -> str:
    payload = invoice_summary_to_dict(invoice, redact_client=redact_client)
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"
    return (
        f"Invoice {payload['number']}\n"
        f"Client: {payload['client_name']}\n"
        f"Status: {payload['status']}\n"
        f"Dates: {payload['issue_date']} to {payload['due_date']}\n"
        f"Lines: {payload['line_count']}\n"
        f"Subtotal: {payload['currency']} {payload['subtotal']}\n"
        f"Tax: {payload['currency']} {payload['tax']}\n"
        f"Total: {payload['currency']} {payload['total']}\n"
    )


def format_invoice_list(
    invoices: tuple[Invoice, ...],
    *,
    as_json: bool = False,
    redact_clients: bool = False,
) -> str:
    payload = {
        "count": len(invoices),
        "invoices": [
            invoice_summary_to_dict(invoice, redact_client=redact_clients)
            for invoice in invoices
        ],
    }
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"
    lines = [f"InvoiceFlow ledger: {len(invoices)} invoices"]
    for item in payload["invoices"]:
        lines.append(
            f"- {item['number']}: {item['status']}, {item['currency']} "
            f"{item['total']}, client {item['client_name']}"
        )
    return "\n".join(lines) + "\n"


def due_review_to_dict(
    review: DueReview,
    *,
    redact_clients: bool = False,
) -> dict[str, Any]:
    return {
        "attention_required": review.attention_required,
        "as_of": review.as_of.isoformat(),
        "days": review.days,
        "summary": {
            "invoices": len(review.invoices),
            "overdue": review.overdue,
            "due_today": review.due_today,
            "upcoming": review.upcoming,
        },
        "invoices": [
            {
                "number": item.number,
                "client_name": _client(item.client_name, redact_clients),
                "due_date": item.due_date.isoformat(),
                "currency": item.currency,
                "amount": str(item.amount),
                "state": item.state.value,
                "days_until_due": item.days_until_due,
            }
            for item in review.invoices
        ],
    }


def format_due_review(
    review: DueReview,
    *,
    as_json: bool = False,
    redact_clients: bool = False,
) -> str:
    payload = due_review_to_dict(review, redact_clients=redact_clients)
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"
    summary = payload["summary"]
    lines = [
        "InvoiceFlow due review",
        f"As of: {payload['as_of']}",
        f"Horizon: {payload['days']} days",
        f"Overdue: {summary['overdue']}",
        f"Due today: {summary['due_today']}",
        f"Upcoming: {summary['upcoming']}",
    ]
    for item in payload["invoices"]:
        lines.append(
            f"- {item['number']}: {item['state']}, due {item['due_date']}, "
            f"{item['currency']} {item['amount']}, client {item['client_name']}"
        )
    return "\n".join(lines) + "\n"
