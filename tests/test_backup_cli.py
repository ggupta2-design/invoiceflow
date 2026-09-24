import json

from invoiceflow.cli import run


def write_invoice(tmp_path):
    payload = {
        "schema_version": 1,
        "number": "INV-BACKUP",
        "client_name": "Sensitive Client",
        "issue_date": "2026-09-01",
        "due_date": "2026-10-01",
        "currency": "USD",
        "status": "draft",
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
    source = tmp_path / "invoice.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    return source


def make_ledger(tmp_path, capsys):
    ledger = tmp_path / "ledger.json"
    assert run(["create", str(ledger), str(write_invoice(tmp_path))]) == 0
    capsys.readouterr()
    return ledger


def test_backup_create_and_verify_cli_workflow(tmp_path, capsys):
    ledger = make_ledger(tmp_path, capsys)
    backup = tmp_path / "private" / "ledger.backup.json"

    assert run(
        ["backup-create", str(ledger), str(backup), "--json"]
    ) == 0
    created = json.loads(capsys.readouterr().out)
    assert created["action"] == "created"
    assert created["invoice_count"] == 1
    assert "Sensitive Client" not in json.dumps(created)

    assert run(["backup-verify", str(backup), "--json"]) == 0
    verified = json.loads(capsys.readouterr().out)
    assert verified["action"] == "verified"
    assert verified["ledger_sha256"] == created["ledger_sha256"]


def test_backup_create_cli_refuses_overwrite(tmp_path, capsys):
    ledger = make_ledger(tmp_path, capsys)
    backup = tmp_path / "backup.json"

    assert run(["backup-create", str(ledger), str(backup)]) == 0
    capsys.readouterr()
    assert run(["backup-create", str(ledger), str(backup)]) == 2
    assert "already exists" in capsys.readouterr().err


def test_backup_verify_cli_uses_value_free_errors(tmp_path, capsys):
    backup = tmp_path / "backup.json"
    backup.write_text('{"client_name": "Sensitive Client"}', encoding="utf-8")

    assert run(["backup-verify", str(backup), "--json"]) == 2
    error = capsys.readouterr().err
    assert "supported fields" in error
    assert "Sensitive Client" not in error
