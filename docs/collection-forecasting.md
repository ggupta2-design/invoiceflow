# Collection forecasting

InvoiceFlow produces a deterministic, read-only view of when currently sent
invoice balances are expected to become due. It is a scheduling aid, not a
cash-flow guarantee, accounting statement, collection recommendation, or
prediction that a customer will pay.

## Windows

Every run requires an explicit `--as-of YYYY-MM-DD` date and accepts a horizon
from 0 through 3,650 days. Sent invoices are grouped into:

- overdue: due before the as-of date;
- due today;
- due in 1–7 days;
- due in 8–30 days;
- later: due in 31 days through the chosen horizon.

Sent invoices beyond the horizon are excluded from currency totals and counted
only in `excluded_after_horizon`. Draft, paid, and void invoices are ignored.
A zero-day horizon intentionally includes only overdue and due-today balances.

## Money and currencies

Amounts use InvoiceFlow's exact Decimal totals and conventional half-up
cent rounding. Currencies are never converted or combined. Each currency is
reported independently and ordered by its three-letter code.

## Privacy

Reports contain only bucket counts and aggregate amounts by currency. They do
not contain client names, invoice numbers, issue or due dates, line
descriptions, per-invoice balances, payment details, or file paths. The source
ledger is not modified. Treat aggregate totals as private financial data even
though identity fields are absent.

## Automation behavior

The command returns status 1 when at least one included sent invoice is
overdue, 0 otherwise, and 2 for invalid inputs or unsafe output requests.
Exports are private and never overwrite an existing file. InvoiceFlow does not
send reminders, contact customers, move money, estimate payment probability,
or make collection decisions; a person must review the result and source
records.
