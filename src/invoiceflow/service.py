"""Invoice creation and query workflows."""

from __future__ import annotations

from dataclasses import dataclass

from .models import Invoice, InvoiceFlowError, InvoiceStatus
from .storage import InvoiceLedger


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
