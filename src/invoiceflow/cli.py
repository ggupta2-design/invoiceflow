"""InvoiceFlow command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Sequence

from .due import review_due
from .invoice_io import load_invoice
from .models import InvoiceFlowError, InvoiceStatus
from .output import write_output
from .report import format_due_review, format_invoice, format_invoice_list
from .service import InvoiceService
from .storage import InvoiceLedger


def _date_argument(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD") from exc


def _report_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--redact-clients", action="store_true")
    parser.add_argument("--output", type=Path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="invoiceflow",
        description="Track private invoices in a local ledger",
    )
    parser.add_argument("--version", action="version", version="invoiceflow 0.1.0")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser(
        "validate",
        help="validate an invoice without changing a ledger",
    )
    validate.add_argument("invoice", type=Path)
    validate.add_argument("--json", action="store_true", dest="as_json")

    create = commands.add_parser("create", help="add an invoice to a local ledger")
    create.add_argument("ledger", type=Path)
    create.add_argument("invoice", type=Path)

    show = commands.add_parser("show", help="show one invoice summary")
    show.add_argument("ledger", type=Path)
    show.add_argument("number")
    _report_options(show)

    listing = commands.add_parser("list", help="list invoices deterministically")
    listing.add_argument("ledger", type=Path)
    listing.add_argument(
        "--status",
        choices=[status.value for status in InvoiceStatus],
    )
    _report_options(listing)

    status = commands.add_parser("status", help="transition an invoice safely")
    status.add_argument("ledger", type=Path)
    status.add_argument("number")
    status.add_argument("new_status", choices=[item.value for item in InvoiceStatus])
    status.add_argument("--on-date", type=_date_argument)

    due = commands.add_parser("due", help="review sent invoices due in a window")
    due.add_argument("ledger", type=Path)
    due.add_argument("--as-of", type=_date_argument, required=True)
    due.add_argument("--days", type=int, default=30)
    _report_options(due)
    return parser


def _emit(content: str, output: Path | None) -> None:
    if output is None:
        print(content, end="" if content.endswith("\n") else "\n")
    else:
        destination = write_output(output, content)
        print(f"Wrote {destination.name}")


def run(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate":
            invoice = load_invoice(args.invoice)
            payload = {
                "valid": True,
                "number": invoice.number,
                "currency": invoice.currency,
                "lines": len(invoice.lines),
                "total": str(invoice.total),
            }
            if args.as_json:
                print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                print(
                    "Invoice is valid\n"
                    f"Number: {invoice.number}\n"
                    f"Currency: {invoice.currency}\n"
                    f"Lines: {len(invoice.lines)}\n"
                    f"Total: {invoice.total}"
                )
            return 0

        service = InvoiceService(InvoiceLedger(args.ledger))
        if args.command == "create":
            invoice = service.create(load_invoice(args.invoice))
            print(f"Created {invoice.number}")
            return 0

        if args.command == "show":
            content = format_invoice(
                service.get(args.number),
                as_json=args.as_json,
                redact_client=args.redact_clients,
            )
            _emit(content, args.output)
            return 0

        if args.command == "list":
            content = format_invoice_list(
                service.list(status=args.status),
                as_json=args.as_json,
                redact_clients=args.redact_clients,
            )
            _emit(content, args.output)
            return 0

        if args.command == "status":
            invoice = service.transition(
                args.number,
                args.new_status,
                on_date=args.on_date,
            )
            print(f"Updated {invoice.number} to {invoice.status.value}")
            return 0

        review = review_due(
            service.list(),
            as_of=args.as_of,
            days=args.days,
        )
        content = format_due_review(
            review,
            as_json=args.as_json,
            redact_clients=args.redact_clients,
        )
        _emit(content, args.output)
        return 1 if review.attention_required else 0
    except InvoiceFlowError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
