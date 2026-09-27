import json

from invoiceflow.cli import run


def write_invoice(
    tmp_path,
    *,
    number,
    client="Sensitive Client",
    issue_date="2026-09-28",
    price="100.00",
):
    payload = {
        "schema_version": 1,
        "number": number,
        "client_name": client,
        "issue_date": issue_date,
        "due_date": "2026-10-28",
        "currency": "USD",
        "status": "sent",
        "paid_at": None,
        "lines": [
            {
                "description": "Confidential service",
                "quantity": "1",
                "unit_price": price,
                "tax_rate": "0",
            }
        ],
    }
    path = tmp_path / f"{number}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_integrity_command_is_read_only_and_privacy_safe(tmp_path, capsys):
    ledger = tmp_path / "ledger.json"
    for number in ("SECRET-001", "SECRET-002"):
        assert run(
            ["create", str(ledger), str(write_invoice(tmp_path, number=number))]
        ) == 0
        capsys.readouterr()
    before = ledger.read_bytes()

    assert run(
        ["integrity", str(ledger), "--as-of", "2026-09-27", "--json"]
    ) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["invoice_count"] == 2
    assert payload["finding_count"] == 3
    serialized = json.dumps(payload)
    for private_value in (
        "Sensitive Client",
        "SECRET-001",
        "SECRET-002",
        "Confidential service",
        "2026-09-28",
        "2026-10-28",
        "100.00",
    ):
        assert private_value not in serialized
    assert ledger.read_bytes() == before


def test_integrity_command_exports_without_overwrite(tmp_path, capsys):
    ledger = tmp_path / "ledger.json"
    source = write_invoice(tmp_path, number="INV-EXPORT")
    run(["create", str(ledger), str(source)])
    capsys.readouterr()
    output = tmp_path / "private" / "integrity.json"
    command = [
        "integrity",
        str(ledger),
        "--as-of",
        "2026-09-27",
        "--json",
        "--output",
        str(output),
    ]

    assert run(command) == 1
    assert capsys.readouterr().out == "Wrote integrity.json\n"
    assert output.exists()
    assert run(command) == 2
    assert "already exists" in capsys.readouterr().err


def test_integrity_command_returns_success_for_clear_ledger(tmp_path, capsys):
    ledger = tmp_path / "ledger.json"
    source = write_invoice(
        tmp_path,
        number="CLEAR",
        client="Ordinary Client",
        issue_date="2026-09-01",
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["due_date"] = "2026-10-01"
    source.write_text(json.dumps(payload), encoding="utf-8")
    run(["create", str(ledger), str(source)])
    capsys.readouterr()

    assert run(
        ["integrity", str(ledger), "--as-of", "2026-09-27", "--json"]
    ) == 0
    assert json.loads(capsys.readouterr().out)["finding_count"] == 0
