import json

from invoiceflow.cli import run


def write_policy(tmp_path, **overrides):
    payload = {
        "schema_version": 1,
        "name": "Standard cadence",
        "upcoming_days": [14, 7, 0],
        "overdue_grace_days": 2,
        "overdue_interval_days": 5,
        "maximum_reminders": 25,
    }
    payload.update(overrides)
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_policy_validation_reports_normalized_settings(tmp_path, capsys):
    policy = write_policy(tmp_path, upcoming_days=[0, 14, 7])

    assert run(["reminder-policy-validate", str(policy), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "valid": True,
        "name": "Standard cadence",
        "upcoming_days": [14, 7, 0],
        "overdue_grace_days": 2,
        "overdue_interval_days": 5,
        "maximum_reminders": 25,
    }


def test_policy_validation_uses_safe_errors(tmp_path, capsys):
    policy = write_policy(tmp_path, maximum_reminders=0)

    assert run(["reminder-policy-validate", str(policy)]) == 2
    error = capsys.readouterr().err
    assert "maximum_reminders" in error
    assert "Standard cadence" not in error
