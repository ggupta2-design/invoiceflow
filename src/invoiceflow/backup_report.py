"""Value-free backup operation summaries."""

from __future__ import annotations

import json
from typing import Any

from .backup import BackupSummary
from .models import InvoiceFlowError

_ACTIONS = {"created", "verified", "restored"}


def backup_summary_to_dict(
    summary: BackupSummary,
    *,
    action: str,
) -> dict[str, Any]:
    if action not in _ACTIONS:
        raise InvoiceFlowError("backup action is not supported")
    return {
        "valid": True,
        "action": action,
        "invoice_count": summary.invoice_count,
        "ledger_sha256": summary.ledger_sha256,
    }


def format_backup_summary(
    summary: BackupSummary,
    *,
    action: str,
    as_json: bool = False,
) -> str:
    payload = backup_summary_to_dict(summary, action=action)
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"
    return (
        f"Backup {payload['action']}\n"
        f"Invoices: {payload['invoice_count']}\n"
        f"Ledger SHA-256: {payload['ledger_sha256']}\n"
    )
