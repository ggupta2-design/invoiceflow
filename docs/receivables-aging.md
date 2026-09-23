# Receivables aging

InvoiceFlow produces read-only receivables aging from the current local ledger.
Only invoices in the `sent` state are treated as open receivables. Draft,
paid, and void invoices are excluded.

The report uses standard deterministic buckets:

- current: due today or later;
- 1–30 days overdue;
- 31–60 days overdue;
- 61–90 days overdue;
- 91 or more days overdue.

The due date is compared with an explicit `--as-of` date, so repeated runs
with the same ledger and date produce the same result. Boundary days remain in
the lower bucket: day 30 is in 1–30, day 60 is in 31–60, and day 90 is in
61–90.

Amounts are calculated with InvoiceFlow's existing exact Decimal rules. Results
are grouped separately by three-letter currency code. InvoiceFlow never adds
different currencies together or performs exchange-rate conversion.

Aging reports intentionally contain aggregate counts and amounts only. They
exclude client names, invoice numbers, issue dates, due dates, line
descriptions, individual balances, and payment dates. These omissions reduce
disclosure but do not make the report anonymous: totals and currency patterns
may still reveal business information.

Aging is informational and is not an accounting reconciliation, allowance
estimate, collections recommendation, tax calculation, or legal determination.
Review ledger accuracy and organizational accounting policy before relying on
the report.
