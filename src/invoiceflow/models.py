"""Validated invoice domain models."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum
from typing import Any


class InvoiceFlowError(ValueError):
    """Safe, user-facing InvoiceFlow failure."""


_CENTS = Decimal("0.01")
_CURRENCY = re.compile(r"^[A-Z]{3}$")


def _text(value: Any, field: str, *, maximum: int) -> str:
    if not isinstance(value, str):
        raise InvoiceFlowError(f"{field} must be text")
    cleaned = value.strip()
    if not cleaned:
        raise InvoiceFlowError(f"{field} cannot be blank")
    if len(cleaned) > maximum:
        raise InvoiceFlowError(f"{field} cannot exceed {maximum} characters")
    if any(ord(character) < 32 for character in cleaned):
        raise InvoiceFlowError(f"{field} cannot contain control characters")
    return cleaned


def _decimal(
    value: Any,
    field: str,
    *,
    minimum: Decimal,
    maximum: Decimal,
    places: int,
) -> Decimal:
    if isinstance(value, bool):
        raise InvoiceFlowError(f"{field} must be a decimal number")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise InvoiceFlowError(f"{field} must be a decimal number") from exc
    if not result.is_finite() or not minimum <= result <= maximum:
        raise InvoiceFlowError(f"{field} must be from {minimum} to {maximum}")
    if result.as_tuple().exponent < -places:
        raise InvoiceFlowError(f"{field} cannot exceed {places} decimal places")
    return result


def money(value: Decimal) -> Decimal:
    """Round monetary results to cents using conventional half-up rounding."""

    return value.quantize(_CENTS, rounding=ROUND_HALF_UP)


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    VOID = "void"


@dataclass(frozen=True)
class InvoiceLine:
    description: str
    quantity: Decimal
    unit_price: Decimal
    tax_rate: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "description",
            _text(self.description, "line description", maximum=300),
        )
        object.__setattr__(
            self,
            "quantity",
            _decimal(
                self.quantity,
                "line quantity",
                minimum=Decimal("0.0001"),
                maximum=Decimal("1000000"),
                places=4,
            ),
        )
        object.__setattr__(
            self,
            "unit_price",
            _decimal(
                self.unit_price,
                "line unit_price",
                minimum=Decimal("0"),
                maximum=Decimal("1000000000"),
                places=2,
            ),
        )
        object.__setattr__(
            self,
            "tax_rate",
            _decimal(
                self.tax_rate,
                "line tax_rate",
                minimum=Decimal("0"),
                maximum=Decimal("100"),
                places=3,
            ),
        )


@dataclass(frozen=True)
class Invoice:
    number: str
    client_name: str
    issue_date: date
    due_date: date
    currency: str
    lines: tuple[InvoiceLine, ...]
    status: InvoiceStatus = InvoiceStatus.DRAFT
    paid_at: date | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "number", _text(self.number, "invoice number", maximum=50)
        )
        object.__setattr__(
            self,
            "client_name",
            _text(self.client_name, "client name", maximum=200),
        )
        if (
            not isinstance(self.issue_date, date)
            or not isinstance(self.due_date, date)
        ):
            raise InvoiceFlowError("invoice dates must be dates")
        if self.due_date < self.issue_date:
            raise InvoiceFlowError("due_date cannot be before issue_date")
        currency = _text(self.currency, "currency", maximum=3).upper()
        if not _CURRENCY.fullmatch(currency):
            raise InvoiceFlowError("currency must be a three-letter code")
        object.__setattr__(self, "currency", currency)
        if (
            not isinstance(self.lines, tuple)
            or not 1 <= len(self.lines) <= 100
            or any(not isinstance(line, InvoiceLine) for line in self.lines)
        ):
            raise InvoiceFlowError("invoice lines must contain from 1 to 100 items")
        if isinstance(self.status, str):
            try:
                object.__setattr__(self, "status", InvoiceStatus(self.status))
            except ValueError as exc:
                raise InvoiceFlowError("invoice status is not supported") from exc
        if not isinstance(self.status, InvoiceStatus):
            raise InvoiceFlowError("invoice status is not supported")
        if self.status is InvoiceStatus.PAID:
            if not isinstance(self.paid_at, date):
                raise InvoiceFlowError("paid invoices require paid_at")
            if self.paid_at < self.issue_date:
                raise InvoiceFlowError("paid_at cannot be before issue_date")
        elif self.paid_at is not None:
            raise InvoiceFlowError("only paid invoices may include paid_at")
