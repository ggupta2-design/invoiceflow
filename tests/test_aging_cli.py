import json

from invoiceflow.cli import run


def write_invoice(tmp_path, *, number, due_date, status="sent", client="Sensitive Client"):
    payload = {
        "schema_version": 1,
        "number": number,
        "client_name": client,
        "issue_date": "2026-01-01",
        "due_date": due_date,
        "currency": "USD",
        "status": status,
        "paid_at": None,
        "lines": [
            {
                "description": "Confidential work",
                "quantity": "1",
                "unit_price": "100.00",
                "tax_rate": "0",
            }
        ],
    }
    path = tmp_path / f"{number}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_aging_command_is_read_only_and_privacy_safe(tmp_path, capsys):
    ledger = tmp_path / "ledger.json"
    source = write_invoice(
        tmp_path,
        number="SECRET-001",
        due_date="2026-08-20",
    )
    assert run(["create", str(ledger), str(source)]) == 0
    capsys.readouterr()
    before = ledger.read_bytes()

    assert run(
        ["aging", str(ledger), "--as-of", "2026-09-23", "--json"]
    ) == 1
    payload = json.loads(capsys.readouterr().out)

    assert payload["summary"]["overdue_invoices"] == 1
    assert payload["currencies"][0]["amount"] == "100.00"
    serialized = json.dumps(payload)
    assert "Sensitive Client" not in serialized
    assert "SECRET-001" not in serialized
    assert "Confidential work" not in serialized
    assert ledger.read_bytes() == before


def test_aging_command_exports_without_overwrite(tmp_path, capsys):
    ledger = tmp_path / "ledger.json"
    source = write_invoice(
        tmp_path,
        number="INV-EXPORT",
        due_date="2026-09-22",
    )
    run(["create", str(ledger), str(source)])
    capsys.readouterr()
    output = tmp_path / "private" / "aging.json"
    command = [
        "aging",
        str(ledger),
        "--as-of",
        "2026-09-23",
        "--json",
        "--output",
        str(output),
    ]

    assert run(command) == 1
    assert capsys.readouterr().out == "Wrote aging.json\n"
    assert output.exists()
    assert run(command) == 2
    assert "already exists" in capsys.readouterr().err


def test_aging_command_returns_success_without_overdue_receivables(tmp_path, capsys):
    ledger = tmp_path / "ledger.json"
    source = write_invoice(
        tmp_path,
        number="INV-CURRENT",
        due_date="2026-10-01",
    )
    run(["create", str(ledger), str(source)])
    capsys.readouterr()

    assert run(
        ["aging", str(ledger), "--as-of", "2026-09-23", "--json"]
    ) == 0
    assert json.loads(capsys.readouterr().out)["summary"]["overdue_invoices"] == 0
