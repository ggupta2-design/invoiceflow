# Payment performance analytics

InvoiceFlow provides a deterministic, read-only summary of how long paid
invoices took to move from issue date to recorded payment date. This is an
operational review aid, not a credit score, accounting opinion, customer
ranking, or prediction of future payment behavior.

## Scope and windows

Every run requires inclusive `--from-date` and `--through-date` boundaries.
The window may span at most 3,650 days. Only invoices whose status is `paid`
and whose payment date falls inside the window are included. Draft, sent, void,
and out-of-window paid invoices are ignored.

Settlement time is grouped into:

- same day;
- 1–7 days;
- 8–30 days;
- 31–60 days;
- 61 days or more.

An explicit target from 0 through 3,650 days controls automation status. A
payment exceeds the target only when its settlement time is strictly greater
than the target.

## Money and averages

Amounts use InvoiceFlow's exact Decimal totals and conventional half-up cent
rounding. Currencies are never converted or combined. Average settlement days
are calculated independently for each currency and rounded half-up to two
decimal places. They are descriptive aggregates, not payment forecasts.

## Privacy

Reports contain window boundaries, bucket counts, aggregate amounts, average
settlement days, and target-miss counts by currency. They omit customer names,
invoice numbers, individual issue, due, and payment dates, line descriptions,
per-invoice balances, payment details, and paths. Aggregate values and small
counts can still be commercially sensitive.

## Automation behavior

The command returns status 1 when at least one included invoice took longer
than the selected target, 0 otherwise, and 2 for invalid input or an unsafe
output request. It never changes the ledger or contacts customers. Exports
never overwrite an existing file. A person should review the private source
records and business context before acting on the report.
