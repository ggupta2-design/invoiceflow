import json
import os
from datetime import date

import pytest

from invoiceflow.models import Invoice, InvoiceLine
from invoiceflow.storage import InvoiceLedger


def invoice(number):
    return Invoice(
        number=number,
        client_name="Fictional Client",
        issue_date=date(2026, 9, 21),
        due_date=date(2026, 10, 21),
        currency="USD",
        lines=(
            InvoiceLine(
                description="Service",
                quantity="1",
                unit_price="100.00",
            ),
        ),
    )


def test_missing_ledger_is_empty_and_save_is_private(tmp_path):
    path = tmp_path / "private" / "ledger.json"
    ledger = InvoiceLedger(path)

    assert ledger.load() == ()
    ledger.save((invoice("INV-002"), invoice("INV-001")))

    loaded = ledger.load()
    assert [item.number for item in loaded] == ["INV-001", "INV-002"]
    assert os.stat(path).st_mode & 0o777 == 0o600


def test_ledger_rejects_duplicate_numbers_case_insensitively(tmp_path):
    ledger = InvoiceLedger(tmp_path / "ledger.json")

    with pytest.raises(ValueError, match="unique"):
        ledger.save((invoice("INV-001"), invoice("inv-001")))


def test_invalid_update_preserves_existing_ledger(tmp_path):
    path = tmp_path / "ledger.json"
    ledger = InvoiceLedger(path)
    ledger.save((invoice("INV-001"),))
    original = path.read_text(encoding="utf-8")

    with pytest.raises(ValueError):
        ledger.save((invoice("INV-002"), invoice("inv-002")))

    assert path.read_text(encoding="utf-8") == original


def test_ledger_rejects_unknown_fields_and_versions(tmp_path):
    path = tmp_path / "ledger.json"

    path.write_text(
        json.dumps({"schema_version": 1, "invoices": [], "extra": True}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="exactly"):
        InvoiceLedger(path).load()

    path.write_text(
        json.dumps({"schema_version": 2, "invoices": []}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="schema_version"):
        InvoiceLedger(path).load()


def test_ledger_rejects_symbolic_links(tmp_path):
    target = tmp_path / "target.json"
    target.write_text('{"schema_version": 1, "invoices": []}', encoding="utf-8")
    link = tmp_path / "ledger.json"
    link.symlink_to(target)

    with pytest.raises(ValueError, match="symbolic"):
        InvoiceLedger(link).load()
    with pytest.raises(ValueError, match="symbolic"):
        InvoiceLedger(link).save((invoice("INV-001"),))
