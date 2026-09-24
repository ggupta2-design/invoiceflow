"""Validated, checksum-protected local ledger backups."""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import Invoice, InvoiceFlowError
from .output import write_output
from .storage import (
    InvoiceLedger,
    format_ledger_json,
    ledger_from_dict,
    ledger_to_dict,
)

_BACKUP_FIELDS = {
    "schema_version",
    "invoice_count",
    "ledger_sha256",
    "ledger",
}
MAX_BACKUP_BYTES = 64 * 1024 * 1024


@dataclass(frozen=True)
class BackupSummary:
    invoice_count: int
    ledger_sha256: str


@dataclass(frozen=True)
class VerifiedBackup:
    summary: BackupSummary
    invoices: tuple[Invoice, ...]


def _canonical_ledger(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_ledger(payload)).hexdigest()


def build_backup(invoices: tuple[Invoice, ...]) -> dict[str, Any]:
    ledger = ledger_to_dict(invoices)
    return {
        "schema_version": 1,
        "invoice_count": len(invoices),
        "ledger_sha256": _digest(ledger),
        "ledger": ledger,
    }


def create_backup(
    ledger_path: str | Path,
    backup_path: str | Path,
) -> BackupSummary:
    source = Path(ledger_path)
    if source.is_symlink():
        raise InvoiceFlowError("ledger cannot be a symbolic link")
    if not source.exists():
        raise InvoiceFlowError("ledger file does not exist")
    invoices = InvoiceLedger(source).load()
    payload = build_backup(invoices)
    write_output(
        backup_path,
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    )
    return BackupSummary(
        invoice_count=payload["invoice_count"],
        ledger_sha256=payload["ledger_sha256"],
    )


def backup_from_dict(payload: Any) -> VerifiedBackup:
    if not isinstance(payload, dict) or set(payload) != _BACKUP_FIELDS:
        raise InvoiceFlowError("backup must contain exactly the supported fields")
    if payload["schema_version"] != 1:
        raise InvoiceFlowError(
            f"unsupported backup schema_version: {payload['schema_version']}"
        )
    count = payload["invoice_count"]
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise InvoiceFlowError("backup invoice_count must be a non-negative integer")
    digest = payload["ledger_sha256"]
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise InvoiceFlowError("backup ledger_sha256 must be a lowercase SHA-256 digest")
    ledger = payload["ledger"]
    if not isinstance(ledger, dict):
        raise InvoiceFlowError("backup ledger must be an object")
    expected = _digest(ledger)
    if not hmac.compare_digest(digest, expected):
        raise InvoiceFlowError("backup checksum does not match ledger contents")
    invoices = ledger_from_dict(ledger)
    if ledger_to_dict(invoices) != ledger:
        raise InvoiceFlowError("backup ledger is not in canonical form")
    if count != len(invoices):
        raise InvoiceFlowError("backup invoice_count does not match ledger contents")
    return VerifiedBackup(
        summary=BackupSummary(invoice_count=count, ledger_sha256=digest),
        invoices=invoices,
    )


def load_backup(path: str | Path) -> VerifiedBackup:
    source = Path(path)
    if source.is_symlink():
        raise InvoiceFlowError("backup cannot be a symbolic link")
    if not source.exists():
        raise InvoiceFlowError("backup file does not exist")
    if not source.is_file():
        raise InvoiceFlowError("backup path is not a file")
    try:
        if source.stat().st_size > MAX_BACKUP_BYTES:
            raise InvoiceFlowError("backup file is too large")
        payload = json.loads(source.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise InvoiceFlowError("backup is not valid UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise InvoiceFlowError(
            f"backup is not valid JSON at line {exc.lineno}"
        ) from exc
    except OSError as exc:
        raise InvoiceFlowError("could not read backup") from exc
    return backup_from_dict(payload)


def restore_backup(
    backup_path: str | Path,
    ledger_path: str | Path,
) -> BackupSummary:
    """Restore a verified backup to a new ledger without overwriting data."""

    verified = load_backup(backup_path)
    write_output(ledger_path, format_ledger_json(verified.invoices))
    return verified.summary
