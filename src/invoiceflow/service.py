"""Invoice creation and query workflows."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date

from .models import Invoice, InvoiceFlowError, InvoiceStatus
from .storage import InvoiceLedger

_ALLOWED_TRANSITIONS = {
    InvoiceStatus.DRAFT: {InvoiceStatus.SENT, InvoiceStatus.VOID},
    InvoiceStatus.SENT: {InvoiceStatus.PAID, InvoiceStatus.VOID},
    InvoiceStatus.PAID: set(),
    InvoiceStatus.VOID: set(),
}


@dataclass(frozen=True)
class InvoiceService:
    ledger: InvoiceLedger

    def create(self, invoice: Invoice) -> Invoice:
        invoices = self.ledger.load()
        if any(
            existing.number.casefold() == invoice.number.casefold()
            for existing in invoices
        ):
            raise InvoiceFlowError("invoice number already exists")
        self.ledger.save(invoices + (invoice,))
        return invoice

    def get(self, number: str) -> Invoice:
        key = number.strip().casefold() if isinstance(number, str) else ""
        if not key:
            raise InvoiceFlowError("invoice number cannot be blank")
        for invoice in self.ledger.load():
            if invoice.number.casefold() == key:
                return invoice
        raise InvoiceFlowError("invoice was not found")

    def list(
        self,
        *,
        status: InvoiceStatus | str | None = None,
    ) -> tuple[Invoice, ...]:
        invoices = self.ledger.load()
        if status is None:
            return invoices
        try:
            selected = InvoiceStatus(status)
        except ValueError as exc:
            raise InvoiceFlowError("invoice status is not supported") from exc
        return tuple(invoice for invoice in invoices if invoice.status is selected)


    def transition(
        self,
        number: str,
        status: InvoiceStatus | str,
        *,
        on_date: date | None = None,
    ) -> Invoice:
        current = self.get(number)
        try:
            target = InvoiceStatus(status)
        except ValueError as exc:
            raise InvoiceFlowError("invoice status is not supported") from exc
        if target is current.status:
            raise InvoiceFlowError("invoice already has the requested status")
        if target not in _ALLOWED_TRANSITIONS[current.status]:
            raise InvoiceFlowError(
                f"cannot transition invoice from {current.status.value} "
                f"to {target.value}"
            )
        if target is InvoiceStatus.PAID:
            if not isinstance(on_date, date):
                raise InvoiceFlowError("paid transition requires on_date")
            updated = replace(current, status=target, paid_at=on_date)
        else:
            if on_date is not None:
                raise InvoiceFlowError("on_date is only supported for paid invoices")
            updated = replace(current, status=target, paid_at=None)

        invoices = tuple(
            updated if invoice.number.casefold() == current.number.casefold()
            else invoice
            for invoice in self.ledger.load()
        )
        self.ledger.save(invoices)
        return updated
