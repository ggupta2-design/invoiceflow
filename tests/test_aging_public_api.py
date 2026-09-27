import pytest

import invoiceflow
from invoiceflow.cli import build_parser


def test_aging_workflow_is_available_from_public_api():
    assert invoiceflow.__version__ == "0.7.0"
    assert callable(invoiceflow.age_receivables)
    assert callable(invoiceflow.classify_aging)
    assert callable(invoiceflow.aging_to_dict)
    assert callable(invoiceflow.format_aging)
    assert invoiceflow.AgingBucket.CURRENT.value == "current"


def test_cli_reports_synced_release_version(capsys):
    with pytest.raises(SystemExit) as raised:
        build_parser().parse_args(["--version"])

    assert raised.value.code == 0
    assert capsys.readouterr().out == "invoiceflow 0.7.0\n"


def test_backup_workflow_is_available_from_public_api():
    assert callable(invoiceflow.create_backup)
    assert callable(invoiceflow.load_backup)
    assert callable(invoiceflow.restore_backup)
    assert callable(invoiceflow.backup_summary_to_dict)
    assert callable(invoiceflow.ledger_to_dict)
    assert invoiceflow.MAX_BACKUP_BYTES == 64 * 1024 * 1024


def test_forecast_workflow_is_available_from_public_api():
    assert callable(invoiceflow.forecast_collections)
    assert callable(invoiceflow.classify_due_date)
    assert callable(invoiceflow.forecast_to_dict)
    assert callable(invoiceflow.format_forecast)
    assert invoiceflow.ForecastBucket.OVERDUE.value == "overdue"


def test_payment_performance_is_available_from_public_api():
    assert callable(invoiceflow.analyze_payment_performance)
    assert callable(invoiceflow.classify_settlement_days)
    assert callable(invoiceflow.payment_performance_to_dict)
    assert callable(invoiceflow.format_payment_performance)
    assert invoiceflow.PaymentBucket.SAME_DAY.value == "same_day"


def test_integrity_audit_is_available_from_public_api():
    assert callable(invoiceflow.audit_invoice_integrity)
    assert callable(invoiceflow.integrity_audit_to_dict)
    assert callable(invoiceflow.format_integrity_audit)
    assert (
        invoiceflow.IntegrityCode.POSSIBLE_DUPLICATE_INVOICE.value
        == "possible_duplicate_invoice"
    )
