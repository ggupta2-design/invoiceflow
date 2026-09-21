"""Strict JSON serialization for individual invoices."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from .models import Invoice, InvoiceFlowError, InvoiceLine

_ROOT_FIELDS = {
    "schema_version",
    "number",
    "client_name",
    "issue_date",
    "due_date",
    "currency",
    "status",
    "paid_at",
    "lines",
}
_LINE_FIELDS = {"description", "quantity", "unit_price", "tax_rate"}


def _date(value: Any, field: str) -> date:
    if not isinstance(value, str):
        raise InvoiceFlowError(f"{field} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise InvoiceFlowError(f"{field} must be an ISO date") from exc


def invoice_to_dict(invoice: Invoice) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "number": invoice.number,
        "client_name": invoice.client_name,
        "issue_date": invoice.issue_date.isoformat(),
        "due_date": invoice.due_date.isoformat(),
        "currency": invoice.currency,
        "status": invoice.status.value,
        "paid_at": invoice.paid_at.isoformat() if invoice.paid_at else None,
        "lines": [
            {
                "description": line.description,
                "quantity": str(line.quantity),
                "unit_price": str(line.unit_price),
                "tax_rate": str(line.tax_rate),
            }
            for line in invoice.lines
        ],
    }


def invoice_from_dict(payload: Any) -> Invoice:
    if not isinstance(payload, dict) or set(payload) != _ROOT_FIELDS:
        raise InvoiceFlowError("invoice must contain exactly the supported fields")
    if payload["schema_version"] != 1:
        raise InvoiceFlowError(
            f"unsupported invoice schema_version: {payload['schema_version']}"
        )
    raw_lines = payload["lines"]
    if not isinstance(raw_lines, list):
        raise InvoiceFlowError("invoice lines must be a list")
    lines = []
    for index, item in enumerate(raw_lines):
        if not isinstance(item, dict) or set(item) != _LINE_FIELDS:
            raise InvoiceFlowError(
                f"invoice lines[{index}] must contain exactly the supported fields"
            )
        lines.append(InvoiceLine(**item))
    paid_at = payload["paid_at"]
    if paid_at is not None:
        paid_at = _date(paid_at, "paid_at")
    return Invoice(
        number=payload["number"],
        client_name=payload["client_name"],
        issue_date=_date(payload["issue_date"], "issue_date"),
        due_date=_date(payload["due_date"], "due_date"),
        currency=payload["currency"],
        lines=tuple(lines),
        status=payload["status"],
        paid_at=paid_at,
    )


def format_invoice_json(invoice: Invoice) -> str:
    return json.dumps(invoice_to_dict(invoice), indent=2, sort_keys=True) + "\n"


def load_invoice(path: str | Path) -> Invoice:
    """Load strict UTF-8 invoice input without echoing private values."""

    source = Path(path)
    if not source.exists():
        raise InvoiceFlowError("invoice file does not exist")
    if not source.is_file():
        raise InvoiceFlowError("invoice path is not a file")
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise InvoiceFlowError("invoice is not valid UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise InvoiceFlowError(
            f"invoice is not valid JSON at line {exc.lineno}"
        ) from exc
    except OSError as exc:
        raise InvoiceFlowError("could not read invoice") from exc
    return invoice_from_dict(payload)
