"""Value-free reports for invoice integrity audits."""

from __future__ import annotations

import json
from typing import Any

from .integrity import IntegrityAudit


def integrity_audit_to_dict(audit: IntegrityAudit) -> dict[str, Any]:
    """Return a deterministic report with codes and aggregate counts only."""

    return {
        "schema": 1,
        "report": "invoice_integrity",
        "as_of": audit.as_of.isoformat(),
        "attention_required": audit.attention_required,
        "invoice_count": audit.invoice_count,
        "finding_count": audit.finding_count,
        "findings": [
            {"code": finding.code.value, "count": finding.count}
            for finding in audit.findings
        ],
    }


def format_integrity_audit(
    audit: IntegrityAudit, *, as_json: bool = False
) -> str:
    """Format a privacy-safe integrity audit as JSON or readable text."""

    payload = integrity_audit_to_dict(audit)
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"

    lines = [
        "InvoiceFlow integrity audit",
        f"As of: {payload['as_of']}",
        f"Attention required: {'yes' if payload['attention_required'] else 'no'}",
        f"Invoices checked: {payload['invoice_count']}",
        f"Findings: {payload['finding_count']}",
    ]
    for finding in payload["findings"]:
        lines.append(f"  {finding['code']}: {finding['count']}")
    return "\n".join(lines) + "\n"
