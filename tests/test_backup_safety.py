import json
from datetime import date

import pytest

from invoiceflow.backup import MAX_BACKUP_BYTES, create_backup, load_backup
from invoiceflow.models import Invoice, InvoiceLine
from invoiceflow.storage import InvoiceLedger


def invoice():
    return Invoice(
        number="INV-PRIVATE",
        client_name="Sensitive Client",
        issue_date=date(2026, 9, 1),
        due_date=date(2026, 10, 1),
        currency="USD",
        lines=(InvoiceLine("Sensitive work", "1", "50.00"),),
    )


def make_backup(tmp_path):
    ledger = tmp_path / "ledger.json"
    backup = tmp_path / "backup.json"
    InvoiceLedger(ledger).save((invoice(),))
    create_backup(ledger, backup)
    return ledger, backup


def test_tampering_is_detected_before_invoice_use(tmp_path):
    _, backup = make_backup(tmp_path)
    payload = json.loads(backup.read_text(encoding="utf-8"))
    payload["ledger"]["invoices"][0]["client_name"] = "Changed"
    backup.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="checksum"):
        load_backup(backup)


def test_create_never_overwrites_an_existing_backup(tmp_path):
    ledger, backup = make_backup(tmp_path)
    original = backup.read_bytes()

    with pytest.raises(ValueError, match="already exists"):
        create_backup(ledger, backup)

    assert backup.read_bytes() == original


def test_backup_loader_rejects_symbolic_links(tmp_path):
    _, backup = make_backup(tmp_path)
    link = tmp_path / "backup-link.json"
    link.symlink_to(backup)

    with pytest.raises(ValueError, match="symbolic"):
        load_backup(link)


def test_backup_loader_rejects_oversized_files(tmp_path):
    backup = tmp_path / "large.json"
    with backup.open("wb") as handle:
        handle.truncate(MAX_BACKUP_BYTES + 1)

    with pytest.raises(ValueError, match="too large"):
        load_backup(backup)


def test_backup_creation_requires_an_existing_ledger(tmp_path):
    with pytest.raises(ValueError, match="does not exist"):
        create_backup(tmp_path / "missing.json", tmp_path / "backup.json")
