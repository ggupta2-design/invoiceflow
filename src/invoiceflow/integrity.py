"""Read-only integrity audits for valid InvoiceFlow records."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Iterable

from .models import Invoice, InvoiceFlowError, InvoiceStatus


class IntegrityCode(str, Enum):
    """Stable, privacy-safe integrity finding codes."""

    POSSIBLE_DUPLICATE_INVOICE = "possible_duplicate_invoice"
    DUPLICATE_LINE_ITEM = "duplicate_line_item"
    FUTURE_ISSUE_DATE = "future_issue_date"
    FUTURE_PAYMENT_DATE = "future_payment_date"
    ZERO_TOTAL_ACTIVE = "zero_total_active"


CODE_ORDER = tuple(IntegrityCode)


@dataclass(frozen=True, slots=True)
class IntegrityFinding:
    """Aggregate occurrences of one integrity concern."""

    code: IntegrityCode
    count: int

    def __post_init__(self) -> None:
        if not isinstance(self.code, IntegrityCode):
            raise InvoiceFlowError("integrity finding code is invalid")
        if isinstance(self.count, bool) or not isinstance(self.count, int) or self.count < 1:
            raise InvoiceFlowError("integrity finding count must be positive")


@dataclass(frozen=True, slots=True)
class IntegrityAudit:
    """Value-free audit result that cannot identify a source invoice."""

    as_of: date
    invoice_count: int
    findings: tuple[IntegrityFinding, ...]

    @property
    def finding_count(self) -> int:
        return sum(finding.count for finding in self.findings)

    @property
    def attention_required(self) -> bool:
        return bool(self.findings)

    def count(self, code: IntegrityCode) -> int:
        for finding in self.findings:
            if finding.code is code:
                return finding.count
        return 0


def audit_invoice_integrity(
    invoices: Iterable[Invoice], *, as_of: date
) -> IntegrityAudit:
    """Inspect valid records without changing or retaining their values."""

    if not isinstance(as_of, date):
        raise InvoiceFlowError("as_of must be a date")
    records = tuple(invoices)
    if any(not isinstance(invoice, Invoice) for invoice in records):
        raise InvoiceFlowError("integrity audit entries must be invoices")

    counts: Counter[IntegrityCode] = Counter()
    fingerprints: Counter[tuple[object, ...]] = Counter()
    for invoice in records:
        fingerprints[_invoice_fingerprint(invoice)] += 1
        counts[IntegrityCode.DUPLICATE_LINE_ITEM] += _duplicate_line_count(invoice)
        if invoice.issue_date > as_of:
            counts[IntegrityCode.FUTURE_ISSUE_DATE] += 1
        if invoice.paid_at is not None and invoice.paid_at > as_of:
            counts[IntegrityCode.FUTURE_PAYMENT_DATE] += 1
        if invoice.status is not InvoiceStatus.VOID and invoice.total == 0:
            counts[IntegrityCode.ZERO_TOTAL_ACTIVE] += 1

    counts[IntegrityCode.POSSIBLE_DUPLICATE_INVOICE] = sum(
        occurrences - 1
        for occurrences in fingerprints.values()
        if occurrences > 1
    )
    findings = tuple(
        IntegrityFinding(code=code, count=counts[code])
        for code in CODE_ORDER
        if counts[code]
    )
    return IntegrityAudit(
        as_of=as_of,
        invoice_count=len(records),
        findings=findings,
    )


def _normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def _line_fingerprint(line: object) -> tuple[object, ...]:
    return (
        _normalized(line.description),
        line.quantity,
        line.unit_price,
        line.tax_rate,
    )


def _invoice_fingerprint(invoice: Invoice) -> tuple[object, ...]:
    return (
        _normalized(invoice.client_name),
        invoice.issue_date,
        invoice.due_date,
        invoice.currency,
        tuple(_line_fingerprint(line) for line in invoice.lines),
        invoice.status,
        invoice.paid_at,
    )


def _duplicate_line_count(invoice: Invoice) -> int:
    line_counts = Counter(_line_fingerprint(line) for line in invoice.lines)
    return sum(
        occurrences - 1
        for occurrences in line_counts.values()
        if occurrences > 1
    )
