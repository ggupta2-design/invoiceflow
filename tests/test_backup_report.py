import json

import pytest

from invoiceflow.backup import BackupSummary
from invoiceflow.backup_report import backup_summary_to_dict, format_backup_summary


SUMMARY = BackupSummary(invoice_count=3, ledger_sha256="a" * 64)


@pytest.mark.parametrize("action", ["created", "verified", "restored"])
def test_backup_summary_supports_every_operation(action):
    payload = backup_summary_to_dict(SUMMARY, action=action)

    assert payload == {
        "valid": True,
        "action": action,
        "invoice_count": 3,
        "ledger_sha256": "a" * 64,
    }


def test_backup_reports_are_value_free():
    text_report = format_backup_summary(SUMMARY, action="verified")
    json_report = format_backup_summary(
        SUMMARY,
        action="verified",
        as_json=True,
    )

    assert "Private Client" not in text_report
    assert "INV-PRIVATE" not in text_report
    assert "Private Client" not in json_report
    assert "INV-PRIVATE" not in json_report
    assert json.loads(json_report)["invoice_count"] == 3


def test_unknown_backup_action_is_rejected():
    with pytest.raises(ValueError, match="not supported"):
        format_backup_summary(SUMMARY, action="deleted")
