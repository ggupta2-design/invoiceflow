import json
from datetime import date
from decimal import Decimal

from invoiceflow.reminder_report import format_reminder_plan, reminder_plan_to_dict
from invoiceflow.reminders import ReminderAction, ReminderPlan, ReminderState


def plan():
    return ReminderPlan(
        policy_name="Standard",
        as_of=date(2026, 9, 22),
        actions=(
            ReminderAction(
                number="INV-PRIVATE",
                client_name="Sensitive Client",
                due_date=date(2026, 9, 20),
                currency="USD",
                amount=Decimal("100.00"),
                state=ReminderState.OVERDUE,
                days_until_due=-2,
            ),
        ),
        eligible_count=3,
    )


def test_json_report_exposes_counts_and_truncation():
    payload = json.loads(format_reminder_plan(plan(), as_json=True))

    assert payload["attention_required"] is True
    assert payload["truncated"] is True
    assert payload["summary"] == {
        "eligible": 3,
        "scheduled": 1,
        "overdue": 1,
        "due_today": 0,
        "upcoming": 0,
    }


def test_redaction_removes_client_without_hiding_operational_fields():
    payload = reminder_plan_to_dict(plan(), redact_clients=True)

    assert payload["actions"][0]["client_name"] == "[redacted]"
    assert payload["actions"][0]["number"] == "INV-PRIVATE"
    assert "Sensitive Client" not in json.dumps(payload)


def test_text_report_is_deterministic_and_omits_private_line_details():
    report = format_reminder_plan(plan(), redact_clients=True)

    assert report.startswith("InvoiceFlow reminder plan\nPolicy: Standard\n")
    assert "Truncated: yes" in report
    assert "client [redacted]" in report
    assert "Sensitive Client" not in report
    assert "line description" not in report.lower()
