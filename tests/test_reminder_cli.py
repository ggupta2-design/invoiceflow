import json

from invoiceflow.cli import run


def write_invoice(tmp_path):
    payload = {
        "schema_version": 1,
        "number": "INV-REMINDER",
        "client_name": "Sensitive Client",
        "issue_date": "2026-09-01",
        "due_date": "2026-09-20",
        "currency": "USD",
        "status": "sent",
        "paid_at": None,
        "lines": [
            {
                "description": "Confidential service",
                "quantity": "1",
                "unit_price": "100.00",
                "tax_rate": "0",
            }
        ],
    }
    path = tmp_path / "invoice.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def write_policy(tmp_path, *, upcoming_days=None):
    payload = {
        "schema_version": 1,
        "name": "Safe cadence",
        "upcoming_days": upcoming_days or [7, 0],
        "overdue_grace_days": 0,
        "overdue_interval_days": 1,
        "maximum_reminders": 10,
    }
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_reminder_command_plans_without_changing_ledger(tmp_path, capsys):
    ledger = tmp_path / "ledger.json"
    source = write_invoice(tmp_path)
    policy = write_policy(tmp_path)
    assert run(["create", str(ledger), str(source)]) == 0
    capsys.readouterr()
    before = ledger.read_bytes()

    assert run(
        [
            "reminders",
            str(ledger),
            str(policy),
            "--as-of",
            "2026-09-22",
            "--json",
            "--redact-clients",
        ]
    ) == 1
    payload = json.loads(capsys.readouterr().out)

    assert payload["summary"]["scheduled"] == 1
    assert payload["actions"][0]["client_name"] == "[redacted]"
    assert "Sensitive Client" not in json.dumps(payload)
    assert "Confidential service" not in json.dumps(payload)
    assert ledger.read_bytes() == before


def test_reminder_command_exports_without_overwrite(tmp_path, capsys):
    ledger = tmp_path / "ledger.json"
    run(["create", str(ledger), str(write_invoice(tmp_path))])
    capsys.readouterr()
    policy = write_policy(tmp_path)
    output = tmp_path / "private" / "reminders.json"
    command = [
        "reminders",
        str(ledger),
        str(policy),
        "--as-of",
        "2026-09-22",
        "--json",
        "--redact-clients",
        "--output",
        str(output),
    ]

    assert run(command) == 1
    assert capsys.readouterr().out == "Wrote reminders.json\n"
    assert output.exists()
    assert run(command) == 2
    assert "already exists" in capsys.readouterr().err


def test_reminder_command_returns_success_when_nothing_is_scheduled(tmp_path, capsys):
    ledger = tmp_path / "ledger.json"
    run(["create", str(ledger), str(write_invoice(tmp_path))])
    capsys.readouterr()
    policy = write_policy(tmp_path)

    assert run(
        [
            "reminders",
            str(ledger),
            str(policy),
            "--as-of",
            "2026-09-20",
            "--json",
        ]
    ) == 1
    capsys.readouterr()

    empty_policy = write_policy(tmp_path, upcoming_days=[14])
    assert run(
        [
            "reminders",
            str(ledger),
            str(empty_policy),
            "--as-of",
            "2026-09-20",
            "--json",
        ]
    ) == 0
    assert json.loads(capsys.readouterr().out)["summary"]["scheduled"] == 0
