import json

import pytest

from invoiceflow.models import InvoiceFlowError
from invoiceflow.reminder_policy import (
    ReminderPolicy,
    format_policy_json,
    load_reminder_policy,
    policy_from_dict,
    policy_to_dict,
)


def payload(**overrides):
    value = {
        "schema_version": 1,
        "name": "Standard cadence",
        "upcoming_days": [14, 7, 0],
        "overdue_grace_days": 2,
        "overdue_interval_days": 5,
        "maximum_reminders": 25,
    }
    value.update(overrides)
    return value


def test_policy_normalizes_upcoming_days_deterministically():
    policy = policy_from_dict(payload(upcoming_days=[0, 14, 7]))

    assert policy.upcoming_days == (14, 7, 0)
    assert policy_to_dict(policy) == payload()
    assert json.loads(format_policy_json(policy)) == payload()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("upcoming_days", []),
        ("upcoming_days", [1, 1]),
        ("upcoming_days", [366]),
        ("overdue_grace_days", -1),
        ("overdue_interval_days", 0),
        ("maximum_reminders", 501),
        ("maximum_reminders", True),
    ],
)
def test_policy_rejects_unsafe_bounds(field, value):
    with pytest.raises(InvoiceFlowError):
        policy_from_dict(payload(**{field: value}))


def test_policy_requires_exact_fields_and_supported_version():
    with pytest.raises(InvoiceFlowError, match="exactly"):
        policy_from_dict({**payload(), "unexpected": True})
    with pytest.raises(InvoiceFlowError, match="schema_version"):
        policy_from_dict(payload(schema_version=2))


def test_policy_loader_rejects_symlinks_and_large_files(tmp_path):
    source = tmp_path / "policy.json"
    source.write_text(json.dumps(payload()), encoding="utf-8")
    assert load_reminder_policy(source).name == "Standard cadence"

    link = tmp_path / "link.json"
    link.symlink_to(source)
    with pytest.raises(InvoiceFlowError, match="symbolic"):
        load_reminder_policy(link)

    large = tmp_path / "large.json"
    large.write_text(" " * (64 * 1024 + 1), encoding="utf-8")
    with pytest.raises(InvoiceFlowError, match="too large"):
        load_reminder_policy(large)


def test_direct_policy_construction_is_validated():
    with pytest.raises(InvoiceFlowError):
        ReminderPolicy(
            name=" ",
            upcoming_days=(7,),
            overdue_grace_days=0,
            overdue_interval_days=7,
            maximum_reminders=10,
        )
