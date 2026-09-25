import json

from invoiceflow.cli import run


def write_invoice(tmp_path, *, number, due_date, client="Sensitive Client"):
    payload = {
        "schema_version": 1,
        "number": number,
        "client_name": client,
        "issue_date": "2026-01-01",
        "due_date": due_date,
        "currency": "USD",
        "status": "sent",
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


def test_forecast_command_is_read_only_and_privacy_safe(tmp_path, capsys):
    ledger = tmp_path / "ledger.json"
    source = write_invoice(tmp_path, number="SECRET-001", due_date="2026-09-20")
    assert run(["create", str(ledger), str(source)]) == 0
    capsys.readouterr()
    before = ledger.read_bytes()

    assert run(
        ["forecast", str(ledger), "--as-of", "2026-09-25", "--json"]
    ) == 1
    payload = json.loads(capsys.readouterr().out)

    assert payload["overdue_count"] == 1
    assert payload["currencies"][0]["amount"] == "100.00"
    serialized = json.dumps(payload)
    assert "Sensitive Client" not in serialized
    assert "SECRET-001" not in serialized
    assert "Confidential work" not in serialized
    assert "2026-09-20" not in serialized
    assert ledger.read_bytes() == before


def test_forecast_command_exports_without_overwrite(tmp_path, capsys):
    ledger = tmp_path / "ledger.json"
    source = write_invoice(tmp_path, number="INV-EXPORT", due_date="2026-09-24")
    run(["create", str(ledger), str(source)])
    capsys.readouterr()
    output = tmp_path / "private" / "forecast.json"
    command = [
        "forecast",
        str(ledger),
        "--as-of",
        "2026-09-25",
        "--json",
        "--output",
        str(output),
    ]

    assert run(command) == 1
    assert capsys.readouterr().out == "Wrote forecast.json\n"
    assert output.exists()
    assert run(command) == 2
    assert "already exists" in capsys.readouterr().err


def test_forecast_command_signals_success_without_overdue_invoices(tmp_path, capsys):
    ledger = tmp_path / "ledger.json"
    source = write_invoice(tmp_path, number="INV-FUTURE", due_date="2026-10-01")
    run(["create", str(ledger), str(source)])
    capsys.readouterr()

    assert run(
        [
            "forecast",
            str(ledger),
            "--as-of",
            "2026-09-25",
            "--days",
            "30",
            "--json",
        ]
    ) == 0
    assert json.loads(capsys.readouterr().out)["overdue_count"] == 0


def test_forecast_command_rejects_out_of_bounds_horizon(tmp_path, capsys):
    ledger = tmp_path / "ledger.json"
    assert run(
        ["forecast", str(ledger), "--as-of", "2026-09-25", "--days", "3651"]
    ) == 2
    assert "days must be" in capsys.readouterr().err
