import json

from invoiceflow.cli import run


def write_invoice(tmp_path, *, number="INV-001", client="Sensitive Client"):
    payload = {
        "schema_version": 1,
        "number": number,
        "client_name": client,
        "issue_date": "2026-09-01",
        "due_date": "2026-09-20",
        "currency": "USD",
        "status": "draft",
        "paid_at": None,
        "lines": [
            {
                "description": "Service",
                "quantity": "1",
                "unit_price": "100.00",
                "tax_rate": "5",
            }
        ],
    }
    path = tmp_path / f"{number}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_validate_and_create_workflow(tmp_path, capsys):
    source = write_invoice(tmp_path)
    ledger = tmp_path / "private" / "ledger.json"

    assert run(["validate", str(source), "--json"]) == 0
    validation = json.loads(capsys.readouterr().out)
    assert validation == {
        "currency": "USD",
        "lines": 1,
        "number": "INV-001",
        "total": "105.00",
        "valid": True,
    }

    assert run(["create", str(ledger), str(source)]) == 0
    assert capsys.readouterr().out == "Created INV-001\n"

    assert run(["create", str(ledger), str(source)]) == 2
    assert "already exists" in capsys.readouterr().err


def test_show_list_and_redacted_export(tmp_path, capsys):
    source = write_invoice(tmp_path)
    ledger = tmp_path / "ledger.json"
    run(["create", str(ledger), str(source)])
    capsys.readouterr()

    assert run(["show", str(ledger), "INV-001", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["client_name"] == "Sensitive Client"

    output = tmp_path / "reports" / "ledger.json"
    command = [
        "list",
        str(ledger),
        "--json",
        "--redact-clients",
        "--output",
        str(output),
    ]
    assert run(command) == 0
    assert capsys.readouterr().out == "Wrote ledger.json\n"
    content = output.read_text(encoding="utf-8")
    assert "Sensitive Client" not in content
    assert "[redacted]" in content

    assert run(command) == 2
    assert "already exists" in capsys.readouterr().err


def test_status_and_due_review_exit_codes(tmp_path, capsys):
    source = write_invoice(tmp_path)
    ledger = tmp_path / "ledger.json"
    run(["create", str(ledger), str(source)])
    capsys.readouterr()

    assert run(["status", str(ledger), "INV-001", "sent"]) == 0
    assert capsys.readouterr().out == "Updated INV-001 to sent\n"

    assert run(
        [
            "due",
            str(ledger),
            "--as-of",
            "2026-09-21",
            "--days",
            "30",
            "--json",
            "--redact-clients",
        ]
    ) == 1
    review = json.loads(capsys.readouterr().out)
    assert review["summary"]["overdue"] == 1
    assert review["invoices"][0]["client_name"] == "[redacted]"

    assert run(
        [
            "status",
            str(ledger),
            "INV-001",
            "paid",
            "--on-date",
            "2026-09-21",
        ]
    ) == 0
    capsys.readouterr()

    assert run(
        ["due", str(ledger), "--as-of", "2026-09-21", "--json"]
    ) == 0
    assert json.loads(capsys.readouterr().out)["summary"]["invoices"] == 0


def test_status_requires_legal_transition_and_payment_date(tmp_path, capsys):
    source = write_invoice(tmp_path)
    ledger = tmp_path / "ledger.json"
    run(["create", str(ledger), str(source)])
    capsys.readouterr()

    assert run(["status", str(ledger), "INV-001", "paid"]) == 2
    assert "cannot transition" in capsys.readouterr().err

    run(["status", str(ledger), "INV-001", "sent"])
    capsys.readouterr()
    assert run(["status", str(ledger), "INV-001", "paid"]) == 2
    assert "requires on_date" in capsys.readouterr().err


def test_list_filters_status_without_exposing_line_details(tmp_path, capsys):
    first = write_invoice(tmp_path, number="INV-001")
    second = write_invoice(tmp_path, number="INV-002", client="Another Client")
    ledger = tmp_path / "ledger.json"
    run(["create", str(ledger), str(first)])
    run(["create", str(ledger), str(second)])
    run(["status", str(ledger), "INV-001", "sent"])
    capsys.readouterr()

    assert run(["list", str(ledger), "--status", "sent", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert [item["number"] for item in payload["invoices"]] == ["INV-001"]
    assert "Service" not in json.dumps(payload)
