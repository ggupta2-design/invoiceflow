"""Deterministic, privacy-aware reminder plan reports."""

from __future__ import annotations

import json
from typing import Any

from .reminders import ReminderPlan


def reminder_plan_to_dict(
    plan: ReminderPlan,
    *,
    redact_clients: bool = False,
) -> dict[str, Any]:
    return {
        "attention_required": plan.attention_required,
        "policy": plan.policy_name,
        "as_of": plan.as_of.isoformat(),
        "truncated": plan.truncated,
        "summary": {
            "eligible": plan.eligible_count,
            "scheduled": len(plan.actions),
            "overdue": plan.overdue,
            "due_today": plan.due_today,
            "upcoming": plan.upcoming,
        },
        "actions": [
            {
                "number": item.number,
                "client_name": "[redacted]" if redact_clients else item.client_name,
                "due_date": item.due_date.isoformat(),
                "currency": item.currency,
                "amount": str(item.amount),
                "state": item.state.value,
                "days_until_due": item.days_until_due,
            }
            for item in plan.actions
        ],
    }


def format_reminder_plan(
    plan: ReminderPlan,
    *,
    as_json: bool = False,
    redact_clients: bool = False,
) -> str:
    payload = reminder_plan_to_dict(plan, redact_clients=redact_clients)
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"
    summary = payload["summary"]
    lines = [
        "InvoiceFlow reminder plan",
        f"Policy: {payload['policy']}",
        f"As of: {payload['as_of']}",
        f"Eligible: {summary['eligible']}",
        f"Scheduled: {summary['scheduled']}",
        f"Overdue: {summary['overdue']}",
        f"Due today: {summary['due_today']}",
        f"Upcoming: {summary['upcoming']}",
        f"Truncated: {'yes' if payload['truncated'] else 'no'}",
    ]
    for item in payload["actions"]:
        lines.append(
            f"- {item['number']}: {item['state']}, due {item['due_date']}, "
            f"{item['currency']} {item['amount']}, client {item['client_name']}"
        )
    return "\n".join(lines) + "\n"
