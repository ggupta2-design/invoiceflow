import pytest

import invoiceflow
from invoiceflow.cli import build_parser


def test_aging_workflow_is_available_from_public_api():
    assert invoiceflow.__version__ == "0.4.0"
    assert callable(invoiceflow.age_receivables)
    assert callable(invoiceflow.classify_aging)
    assert callable(invoiceflow.aging_to_dict)
    assert callable(invoiceflow.format_aging)
    assert invoiceflow.AgingBucket.CURRENT.value == "current"


def test_cli_reports_synced_release_version(capsys):
    with pytest.raises(SystemExit) as raised:
        build_parser().parse_args(["--version"])

    assert raised.value.code == 0
    assert capsys.readouterr().out == "invoiceflow 0.4.0\n"


def test_backup_workflow_is_available_from_public_api():
    assert callable(invoiceflow.create_backup)
    assert callable(invoiceflow.load_backup)
    assert callable(invoiceflow.restore_backup)
    assert callable(invoiceflow.backup_summary_to_dict)
    assert callable(invoiceflow.ledger_to_dict)
    assert invoiceflow.MAX_BACKUP_BYTES == 64 * 1024 * 1024
