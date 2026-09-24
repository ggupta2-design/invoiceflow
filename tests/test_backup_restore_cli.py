import json

from invoiceflow.cli import run


def prepare_backup(tmp_path, capsys):
    invoice = tmp_path / "invoice.json"
    invoice.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "number": "INV-RESTORE",
                "client_name": "Sensitive Client",
                "issue_date": "2026-09-01",
                "due_date": "2026-10-01",
                "currency": "USD",
                "status": "draft",
                "paid_at": None,
                "lines": [
                    {
                        "description": "Private service",
                        "quantity": "1",
                        "unit_price": "20.00",
                        "tax_rate": "0",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    ledger = tmp_path / "source-ledger.json"
    backup = tmp_path / "backup.json"
    assert run(["create", str(ledger), str(invoice)]) == 0
    capsys.readouterr()
    assert run(["backup-create", str(ledger), str(backup)]) == 0
    capsys.readouterr()
    return backup


def test_restore_cli_requires_explicit_confirmation(tmp_path, capsys):
    backup = prepare_backup(tmp_path, capsys)
    destination = tmp_path / "restored.json"

    assert run(["backup-restore", str(backup), str(destination)]) == 2
    assert "--confirm RESTORE" in capsys.readouterr().err
    assert not destination.exists()

    assert run(
        [
            "backup-restore",
            str(backup),
            str(destination),
            "--confirm",
            "not-restore",
        ]
    ) == 2
    capsys.readouterr()
    assert not destination.exists()


def test_restore_cli_recovers_to_new_ledger_without_private_output(tmp_path, capsys):
    backup = prepare_backup(tmp_path, capsys)
    destination = tmp_path / "restored" / "ledger.json"

    assert run(
        [
            "backup-restore",
            str(backup),
            str(destination),
            "--confirm",
            "RESTORE",
        ]
    ) == 0
    output = capsys.readouterr().out

    assert "Backup restored" in output
    assert "Invoices: 1" in output
    assert "Sensitive Client" not in output
    assert run(["show", str(destination), "INV-RESTORE", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["client_name"] == "Sensitive Client"


def test_restore_cli_never_overwrites_existing_destination(tmp_path, capsys):
    backup = prepare_backup(tmp_path, capsys)
    destination = tmp_path / "existing.json"
    destination.write_text("preserve", encoding="utf-8")

    assert run(
        [
            "backup-restore",
            str(backup),
            str(destination),
            "--confirm",
            "RESTORE",
        ]
    ) == 2
    assert "already exists" in capsys.readouterr().err
    assert destination.read_text(encoding="utf-8") == "preserve"
