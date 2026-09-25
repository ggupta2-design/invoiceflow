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

## Review receivables aging

```bash
invoiceflow aging ~/private/invoiceflow-ledger.json \
  --as-of 2026-09-23

invoiceflow aging ~/private/invoiceflow-ledger.json \
  --as-of 2026-09-23 --json \
  --output ~/private/reports/aging.json
```

Aging includes sent invoices only and groups aggregate counts and amounts by
currency and by current, 1–30, 31–60, 61–90, and 91+ day buckets. Reports omit
client names, invoice numbers, individual dates, and line descriptions. The
ledger is never modified.

Status 1 means at least one open invoice is overdue, 0 means no overdue
receivable was found, and 2 means the ledger, date, or output request is
invalid. See [receivables-aging.md](receivables-aging.md) for boundaries,
currency handling, disclosure limits, and interpretation guidance.

## Forecast collection windows

```bash
invoiceflow forecast ~/private/invoiceflow-ledger.json \
  --as-of 2026-09-25 --days 90

invoiceflow forecast ~/private/invoiceflow-ledger.json \
  --as-of 2026-09-25 --days 90 --json \
  --output ~/private/reports/collection-forecast.json
```

Only sent invoices enter forecasts. Aggregate counts and exact amounts remain
separate by currency across overdue, due-today, 1–7 day, 8–30 day, and later
windows. Sent invoices beyond the selected horizon are counted but their
amounts are excluded. Reports omit clients, invoice identifiers, individual
dates, descriptions, and per-invoice balances, and the ledger is never
modified.

Status 1 means at least one included invoice is overdue, 0 means no overdue
invoice was found, and 2 means the input or output request is invalid. Exports
cannot overwrite existing files. See
[collection-forecasting.md](collection-forecasting.md) for semantics, privacy
boundaries, and interpretation limits.

## Plan customer reminders

Validate a reminder policy independently before using it:

```bash
invoiceflow reminder-policy-validate \
  examples/reminder-policy.json --json
```

Create a read-only plan from sent invoices:

```bash
invoiceflow reminders ~/private/invoiceflow-ledger.json \
  ~/private/reminder-policy.json \
  --as-of 2026-09-22 --json --redact-clients \
  --output ~/private/reports/reminder-plan.json
```

The policy selects exact upcoming offsets, a grace period, an overdue repeat
interval, and a global action limit. The command does not modify the ledger or
send messages. It returns status 1 when one or more actions are scheduled or
the eligible set was truncated, 0 when no action is due, and 2 for invalid
input or an unsafe output request.

See [reminder-policies.md](reminder-policies.md) for cadence semantics,
prioritization, bounds, and human-review requirements.

## Back up and recover a ledger

Create a protected backup without changing the source:

```bash
invoiceflow backup-create \
  ~/private/invoiceflow-ledger.json \
  ~/encrypted-backups/invoiceflow.backup.json --json
```

Verify the complete schema, invoice count, canonical ledger, and checksum
without restoring:

```bash
invoiceflow backup-verify \
  ~/encrypted-backups/invoiceflow.backup.json --json
```

Restore only to a new destination with explicit confirmation:

```bash
invoiceflow backup-restore \
  ~/encrypted-backups/invoiceflow.backup.json \
  ~/private/restored-ledger.json \
  --confirm RESTORE
```

Creation and restore never overwrite existing files. A failed verification
cannot create a restored ledger. Backup command output contains only the
operation, invoice count, and ledger checksum, but the backup file itself
contains the complete private ledger.

See [backup-and-recovery.md](backup-and-recovery.md) for storage requirements,
checksum limitations, recovery safeguards, and operational guidance.

Read [privacy-and-safety.md](privacy-and-safety.md) before storing real customer
or financial data.
