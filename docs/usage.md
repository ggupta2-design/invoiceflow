# Using InvoiceFlow

Install InvoiceFlow in a virtual environment:

```bash
python -m pip install -e .
```

Copy the fictional example to a private location before editing it:

```bash
cp examples/invoice.json ~/private/invoice-001.json
```

## Validate an invoice

```bash
invoiceflow validate ~/private/invoice-001.json
invoiceflow validate ~/private/invoice-001.json --json
```

Validation is local and never changes a ledger. Inputs use a strict
schema-version-1 JSON object. Unknown fields, unsupported versions, malformed
dates, unsupported statuses, invalid decimal precision, and values outside
documented bounds are rejected.

## Create a ledger record

```bash
invoiceflow create ~/private/invoiceflow-ledger.json \
  ~/private/invoice-001.json
```

Invoice numbers are unique case-insensitively. The ledger is sorted
deterministically and updated atomically. The first successful command creates
the private ledger; later commands preserve its schema and existing records.

## Review invoices

```bash
invoiceflow show ~/private/invoiceflow-ledger.json EXAMPLE-001
invoiceflow list ~/private/invoiceflow-ledger.json --json
invoiceflow list ~/private/invoiceflow-ledger.json \
  --status sent --json --redact-clients
```

Summary reports contain amounts and lifecycle metadata but omit line-item
descriptions. Use `--redact-clients` before sharing list, show, or due reports.

## Move invoices through their lifecycle

```bash
invoiceflow status ~/private/invoiceflow-ledger.json EXAMPLE-001 sent

invoiceflow status ~/private/invoiceflow-ledger.json EXAMPLE-001 paid \
  --on-date 2026-09-25
```

Allowed transitions are draft to sent or void, and sent to paid or void. Paid
and void states are terminal. A paid transition requires an explicit ISO date.
Invalid or repeated transitions leave the ledger unchanged.

## Review due work

```bash
invoiceflow due ~/private/invoiceflow-ledger.json \
  --as-of 2026-09-21 --days 30

invoiceflow due ~/private/invoiceflow-ledger.json \
  --as-of 2026-09-21 --days 30 \
  --json --redact-clients \
  --output ~/private/reports/due-review.json
```

Only sent invoices enter due reviews. The bounded horizon can range from 0 to
3,650 days. Reports classify overdue, due-today, and upcoming invoices in a
deterministic order.

Status 0 means the command succeeded and a due review has no overdue invoices.
Status 1 means a due review contains overdue invoices. Status 2 means an input,
transition, ledger, or output request is invalid. Exports cannot overwrite
existing files.

Read [privacy-and-safety.md](privacy-and-safety.md) before storing real customer
or financial data.
