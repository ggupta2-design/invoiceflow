import json

from invoiceflow.cli import run


def write_invoice(tmp_path, *, number="SECRET-001", paid_at="2026-09-20"):
    payload = {
        "schema_version": 1,
        "number": number,
        "client_name": "Sensitive Client",
        "issue_date": "2026-08-01",
        "due_date": "2026-08-31",
        "currency": "USD",
        "status": "paid",
        "paid_at": paid_at,
        "lines": [
            {
                "description": "Confidential service",
                "quantity": "1",
                "unit_price": "100.00",
                "tax_rate": "0",
            }
        ],
    }
    path = tmp_path / f"{number}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def command(ledger, *extra):
    return [
        "payment-performance",
        str(ledger),
        "--from-date",
        "2026-09-01",
        "--through-date",
        "2026-09-30",
        *extra,
    ]


def test_payment_performance_is_read_only_and_privacy_safe(tmp_path, capsys):
    ledger = tmp_path / "ledger.json"
    source = write_invoice(tmp_path)
    assert run(["create", str(ledger), str(source)]) == 0
    capsys.readouterr()
    before = ledger.read_bytes()

    assert run(command(ledger, "--json")) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["invoice_count"] == 1
    assert payload["over_target_count"] == 1
    assert payload["currencies"][0]["amount"] == "100.00"
    serialized = json.dumps(payload)
    for private_value in (
        "Sensitive Client",
        "SECRET-001",
        "Confidential service",
        "2026-08-01",
        "2026-08-31",
        "2026-09-20",
    ):
        assert private_value not in serialized
    assert ledger.read_bytes() == before


def test_payment_performance_exports_without_overwrite(tmp_path, capsys):
    ledger = tmp_path / "ledger.json"
    run(["create", str(ledger), str(write_invoice(tmp_path))])
    capsys.readouterr()
    output = tmp_path / "private" / "performance.json"
    args = command(ledger, "--json", "--output", str(output))

    assert run(args) == 1
    assert capsys.readouterr().out == "Wrote performance.json\n"
    assert output.exists()
    assert run(args) == 2
    assert "already exists" in capsys.readouterr().err


def test_payment_performance_returns_success_when_target_is_met(tmp_path, capsys):
    ledger = tmp_path / "ledger.json"
    source = write_invoice(tmp_path, number="FAST", paid_at="2026-08-05")
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["issue_date"] = "2026-08-01"
    payload["due_date"] = "2026-08-31"
    source.write_text(json.dumps(payload), encoding="utf-8")
    run(["create", str(ledger), str(source)])
    capsys.readouterr()

    assert run(
        [
            "payment-performance",
            str(ledger),
            "--from-date",
            "2026-08-01",
            "--through-date",
            "2026-08-31",
            "--target-days",
            "7",
            "--json",
        ]
    ) == 0
    assert json.loads(capsys.readouterr().out)["over_target_count"] == 0


def test_payment_performance_rejects_invalid_window(tmp_path, capsys):
    ledger = tmp_path / "ledger.json"
    assert run(
        [
            "payment-performance",
            str(ledger),
            "--from-date",
            "2026-10-01",
            "--through-date",
            "2026-09-01",
        ]
    ) == 2
    assert "from_date cannot be after" in capsys.readouterr().err
