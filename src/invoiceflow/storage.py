"""Atomic private local storage for InvoiceFlow ledgers."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .invoice_io import invoice_from_dict, invoice_to_dict
from .models import Invoice, InvoiceFlowError

_LEDGER_FIELDS = {"schema_version", "invoices"}
MAX_LEDGER_INVOICES = 10_000


@dataclass(frozen=True)
class InvoiceLedger:
    path: Path

    def __init__(self, path: str | Path):
        object.__setattr__(self, "path", Path(path))

    def load(self) -> tuple[Invoice, ...]:
        if not self.path.exists():
            return ()
        if self.path.is_symlink():
            raise InvoiceFlowError("ledger cannot be a symbolic link")
        if not self.path.is_file():
            raise InvoiceFlowError("ledger path is not a file")
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except UnicodeDecodeError as exc:
            raise InvoiceFlowError("ledger is not valid UTF-8") from exc
        except json.JSONDecodeError as exc:
            raise InvoiceFlowError(
                f"ledger is not valid JSON at line {exc.lineno}"
            ) from exc
        except OSError as exc:
            raise InvoiceFlowError("could not read ledger") from exc
        return ledger_from_dict(payload)

    def save(self, invoices: tuple[Invoice, ...]) -> None:
        validated = _validate_invoices(invoices)
        if self.path.exists() and self.path.is_symlink():
            raise InvoiceFlowError("ledger cannot be a symbolic link")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        content = format_ledger_json(validated)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.",
            suffix=".tmp",
            dir=self.path.parent,
        )
        temporary = Path(temporary_name)
        try:
            os.chmod(temporary, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        except OSError as exc:
            raise InvoiceFlowError("could not write ledger") from exc
        finally:
            if temporary.exists():
                temporary.unlink()


def _validate_invoices(invoices: tuple[Invoice, ...]) -> tuple[Invoice, ...]:
    if (
        not isinstance(invoices, tuple)
        or len(invoices) > MAX_LEDGER_INVOICES
        or any(not isinstance(invoice, Invoice) for invoice in invoices)
    ):
        raise InvoiceFlowError(
            f"ledger invoices must contain at most {MAX_LEDGER_INVOICES} entries"
        )
    ordered = tuple(sorted(invoices, key=lambda item: item.number.casefold()))
    keys = [invoice.number.casefold() for invoice in ordered]
    if len(keys) != len(set(keys)):
        raise InvoiceFlowError("invoice numbers must be unique")
    return ordered


def ledger_to_dict(invoices: tuple[Invoice, ...]) -> dict[str, Any]:
    validated = _validate_invoices(invoices)
    return {
        "schema_version": 1,
        "invoices": [invoice_to_dict(invoice) for invoice in validated],
    }


def format_ledger_json(invoices: tuple[Invoice, ...]) -> str:
    return json.dumps(ledger_to_dict(invoices), indent=2, sort_keys=True) + "\n"


def ledger_from_dict(payload: Any) -> tuple[Invoice, ...]:
    if not isinstance(payload, dict) or set(payload) != _LEDGER_FIELDS:
        raise InvoiceFlowError("ledger must contain exactly the supported fields")
    if payload["schema_version"] != 1:
        raise InvoiceFlowError(
            f"unsupported ledger schema_version: {payload['schema_version']}"
        )
    raw = payload["invoices"]
    if not isinstance(raw, list):
        raise InvoiceFlowError("ledger invoices must be a list")
    return _validate_invoices(tuple(invoice_from_dict(item) for item in raw))
