import json
from datetime import date

import pytest

from invoiceflow.models import Invoice, InvoiceLine
from invoiceflow.storage import format_ledger_json, ledger_from_dict, ledger_to_dict


def invoice(number):
    return Invoice(
        number=number,
        client_name="Fictional Client",
        issue_date=date(2026, 9, 1),
        due_date=date(2026, 10, 1),
        currency="USD",
        lines=(InvoiceLine("Service", "1", "10.00"),),
    )


def test_ledger_serialization_is_sorted_and_round_trips():
    invoices = (invoice("INV-002"), invoice("INV-001"))

    payload = ledger_to_dict(invoices)
    restored = ledger_from_dict(payload)

    assert [item["number"] for item in payload["invoices"]] == [
        "INV-001",
        "INV-002",
    ]
    assert restored == tuple(sorted(invoices, key=lambda item: item.number))
    assert json.loads(format_ledger_json(invoices)) == payload


def test_ledger_serialization_rejects_duplicates():
    with pytest.raises(ValueError, match="unique"):
        ledger_to_dict((invoice("INV-001"), invoice("inv-001")))


def test_ledger_parser_requires_exact_schema():
    with pytest.raises(ValueError, match="exactly"):
        ledger_from_dict(
            {"schema_version": 1, "invoices": [], "unexpected": True}
        )
    with pytest.raises(ValueError, match="schema_version"):
        ledger_from_dict({"schema_version": 2, "invoices": []})
