import json
import os
from datetime import date

from invoiceflow.backup import create_backup, load_backup
from invoiceflow.models import Invoice, InvoiceLine
from invoiceflow.storage import InvoiceLedger


def invoice(number):
    return Invoice(
        number=number,
        client_name="Private Client",
        issue_date=date(2026, 9, 1),
        due_date=date(2026, 10, 1),
        currency="USD",
        lines=(InvoiceLine("Private service", "1", "25.00"),),
    )


def test_create_backup_round_trips_validated_ledger(tmp_path):
    ledger_path = tmp_path / "ledger.json"
    backup_path = tmp_path / "backups" / "ledger.backup.json"
    InvoiceLedger(ledger_path).save((invoice("INV-002"), invoice("INV-001")))

    summary = create_backup(ledger_path, backup_path)
    verified = load_backup(backup_path)

    assert summary == verified.summary
    assert summary.invoice_count == 2
    assert len(summary.ledger_sha256) == 64
    assert [item.number for item in verified.invoices] == ["INV-001", "INV-002"]
    assert os.stat(backup_path).st_mode & 0o777 == 0o600


def test_backup_envelope_contains_versioned_ledger_and_digest(tmp_path):
    ledger_path = tmp_path / "ledger.json"
    backup_path = tmp_path / "backup.json"
    InvoiceLedger(ledger_path).save((invoice("INV-001"),))

    create_backup(ledger_path, backup_path)
    payload = json.loads(backup_path.read_text(encoding="utf-8"))

    assert set(payload) == {
        "schema_version",
        "invoice_count",
        "ledger_sha256",
        "ledger",
    }
    assert payload["schema_version"] == 1
    assert payload["ledger"]["schema_version"] == 1
    assert payload["invoice_count"] == 1
