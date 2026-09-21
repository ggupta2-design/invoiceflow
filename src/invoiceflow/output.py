"""Protected non-overwriting output for InvoiceFlow reports."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .models import InvoiceFlowError


def write_output(path: str | Path, content: str) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        raise InvoiceFlowError("output file already exists")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    temporary = Path(temporary_name)
    try:
        os.chmod(temporary, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, destination)
        except FileExistsError as exc:
            raise InvoiceFlowError("output file already exists") from exc
        except OSError as exc:
            raise InvoiceFlowError("could not write output") from exc
        return destination
    finally:
        if temporary.exists():
            temporary.unlink()
