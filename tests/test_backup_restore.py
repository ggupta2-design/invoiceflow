import json
import os
from datetime import date

import pytest

from invoiceflow.backup import create_backup, restore_backup
from invoiceflow.models import Invoice, InvoiceLine
from invoiceflow.storage import InvoiceLedger


def invoice(number):
    return Invoice(
        number=number,
        client_name="Private Client",
        issue_date=date(2026, 9, 1),
        due_date=date(2026, 10, 1),
        currency="USD",
        lines=(InvoiceLine("Service", "1", "75.00"),),
    )


def make_backup(tmp_path):
    source = tmp_path / "source.json"
    backup = tmp_path / "backup.json"
    InvoiceLedger(source).save((invoice("INV-002"), invoice("INV-001")))
    create_backup(source, backup)
    return backup


def test_restore_creates_a_private_valid_ledger(tmp_path):
    backup = make_backup(tmp_path)
    destination = tmp_path / "restored" / "ledger.json"

    summary = restore_backup(backup, destination)

    assert summary.invoice_count == 2
    assert [item.number for item in InvoiceLedger(destination).load()] == [
        "INV-001",
        "INV-002",
    ]
    assert os.stat(destination).st_mode & 0o777 == 0o600


def test_restore_never_overwrites_an_existing_ledger(tmp_path):
    backup = make_backup(tmp_path)
    destination = tmp_path / "existing.json"
    destination.write_text("preserve me", encoding="utf-8")

    with pytest.raises(ValueError, match="already exists"):
        restore_backup(backup, destination)

    assert destination.read_text(encoding="utf-8") == "preserve me"


def test_failed_verification_does_not_create_destination(tmp_path):
    backup = make_backup(tmp_path)
    payload = json.loads(backup.read_text(encoding="utf-8"))
    payload["invoice_count"] = 999
    backup.write_text(json.dumps(payload), encoding="utf-8")
    destination = tmp_path / "restored.json"

    with pytest.raises(ValueError, match="invoice_count"):
        restore_backup(backup, destination)

    assert not destination.exists()


def test_restore_rejects_symbolic_link_destinations(tmp_path):
    backup = make_backup(tmp_path)
    target = tmp_path / "target.json"
    target.write_text("preserve me", encoding="utf-8")
    link = tmp_path / "ledger-link.json"
    link.symlink_to(target)

    with pytest.raises(ValueError, match="already exists"):
        restore_backup(backup, link)

    assert target.read_text(encoding="utf-8") == "preserve me"
