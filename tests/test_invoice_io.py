import json
from datetime import date

import pytest

from invoiceflow.invoice_io import (
    format_invoice_json,
    invoice_from_dict,
    invoice_to_dict,
    load_invoice,
)


def payload(**overrides):
    values = {
        "schema_version": 1,
        "number": "INV-001",
        "client_name": "Fictional Studio",
        "issue_date": "2026-09-21",
        "due_date": "2026-10-21",
        "currency": "USD",
        "status": "draft",
        "paid_at": None,
        "lines": [
            {
                "description": "Automation setup",
                "quantity": "2",
                "unit_price": "150.00",
                "tax_rate": "5",
            }
        ],
    }
    values.update(overrides)
    return values


def test_invoice_json_round_trip_is_deterministic(tmp_path):
    invoice = invoice_from_dict(payload())
    path = tmp_path / "invoice.json"
    path.write_text(format_invoice_json(invoice), encoding="utf-8")

    loaded = load_invoice(path)

    assert loaded == invoice
    assert invoice_to_dict(loaded) == payload()
    assert loaded.issue_date == date(2026, 9, 21)
    assert loaded.total.as_tuple().exponent == -2


def test_input_rejects_unknown_missing_and_nested_fields():
    unknown = payload(extra=True)
    missing = payload()
    missing.pop("currency")
    nested = payload()
    nested["lines"] = [{**nested["lines"][0], "private_note": "do not expose"}]

    for invalid in (unknown, missing, nested):
        with pytest.raises(ValueError, match="exactly"):
            invoice_from_dict(invalid)


def test_input_rejects_bad_schema_dates_and_line_container():
    with pytest.raises(ValueError, match="schema_version"):
        invoice_from_dict(payload(schema_version=2))
    with pytest.raises(ValueError, match="ISO date"):
        invoice_from_dict(payload(issue_date="09/21/2026"))
    with pytest.raises(ValueError, match="must be a list"):
        invoice_from_dict(payload(lines={}))


def test_loader_errors_do_not_echo_private_file_values(tmp_path):
    path = tmp_path / "private-invoice.json"
    path.write_text('{"client_name": "Sensitive Customer"', encoding="utf-8")

    with pytest.raises(ValueError) as caught:
        load_invoice(path)

    assert "Sensitive Customer" not in str(caught.value)


def test_loader_rejects_missing_files(tmp_path):
    with pytest.raises(ValueError, match="does not exist"):
        load_invoice(tmp_path / "missing.json")
