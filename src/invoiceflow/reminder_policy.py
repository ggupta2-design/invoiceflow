"""Strict local policies for payment reminder planning."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import InvoiceFlowError

_POLICY_FIELDS = {
    "schema_version",
    "name",
    "upcoming_days",
    "overdue_grace_days",
    "overdue_interval_days",
    "maximum_reminders",
}
MAX_POLICY_BYTES = 64 * 1024
MAX_UPCOMING_DAYS = 32


def _bounded_int(value: Any, field: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvoiceFlowError(f"{field} must be an integer")
    if not minimum <= value <= maximum:
        raise InvoiceFlowError(f"{field} must be from {minimum} to {maximum}")
    return value


@dataclass(frozen=True)
class ReminderPolicy:
    """A deterministic reminder cadence that never sends messages."""

    name: str
    upcoming_days: tuple[int, ...]
    overdue_grace_days: int
    overdue_interval_days: int
    maximum_reminders: int

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise InvoiceFlowError("policy name must be text")
        name = self.name.strip()
        if not name or len(name) > 100 or any(ord(char) < 32 for char in name):
            raise InvoiceFlowError("policy name must contain 1 to 100 safe characters")
        object.__setattr__(self, "name", name)
        if (
            not isinstance(self.upcoming_days, tuple)
            or not 1 <= len(self.upcoming_days) <= MAX_UPCOMING_DAYS
        ):
            raise InvoiceFlowError(
                f"upcoming_days must contain 1 to {MAX_UPCOMING_DAYS} entries"
            )
        days = tuple(
            _bounded_int(value, "upcoming_days entries", 0, 365)
            for value in self.upcoming_days
        )
        if len(days) != len(set(days)):
            raise InvoiceFlowError("upcoming_days entries must be unique")
        object.__setattr__(self, "upcoming_days", tuple(sorted(days, reverse=True)))
        object.__setattr__(
            self,
            "overdue_grace_days",
            _bounded_int(self.overdue_grace_days, "overdue_grace_days", 0, 365),
        )
        object.__setattr__(
            self,
            "overdue_interval_days",
            _bounded_int(self.overdue_interval_days, "overdue_interval_days", 1, 365),
        )
        object.__setattr__(
            self,
            "maximum_reminders",
            _bounded_int(self.maximum_reminders, "maximum_reminders", 1, 500),
        )


def policy_to_dict(policy: ReminderPolicy) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "name": policy.name,
        "upcoming_days": list(policy.upcoming_days),
        "overdue_grace_days": policy.overdue_grace_days,
        "overdue_interval_days": policy.overdue_interval_days,
        "maximum_reminders": policy.maximum_reminders,
    }


def policy_from_dict(payload: Any) -> ReminderPolicy:
    if not isinstance(payload, dict) or set(payload) != _POLICY_FIELDS:
        raise InvoiceFlowError("reminder policy must contain exactly the supported fields")
    if payload["schema_version"] != 1:
        raise InvoiceFlowError(
            f"unsupported reminder policy schema_version: {payload['schema_version']}"
        )
    raw_days = payload["upcoming_days"]
    if not isinstance(raw_days, list):
        raise InvoiceFlowError("upcoming_days must be a list")
    return ReminderPolicy(
        name=payload["name"],
        upcoming_days=tuple(raw_days),
        overdue_grace_days=payload["overdue_grace_days"],
        overdue_interval_days=payload["overdue_interval_days"],
        maximum_reminders=payload["maximum_reminders"],
    )


def format_policy_json(policy: ReminderPolicy) -> str:
    return json.dumps(policy_to_dict(policy), indent=2, sort_keys=True) + "\n"


def load_reminder_policy(path: str | Path) -> ReminderPolicy:
    source = Path(path)
    if source.is_symlink():
        raise InvoiceFlowError("reminder policy cannot be a symbolic link")
    if not source.exists():
        raise InvoiceFlowError("reminder policy file does not exist")
    if not source.is_file():
        raise InvoiceFlowError("reminder policy path is not a file")
    try:
        if source.stat().st_size > MAX_POLICY_BYTES:
            raise InvoiceFlowError("reminder policy file is too large")
        payload = json.loads(source.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise InvoiceFlowError("reminder policy is not valid UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise InvoiceFlowError(
            f"reminder policy is not valid JSON at line {exc.lineno}"
        ) from exc
    except OSError as exc:
        raise InvoiceFlowError("could not read reminder policy") from exc
    return policy_from_dict(payload)
