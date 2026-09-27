# Invoice integrity audits

InvoiceFlow can review an already valid ledger for suspicious relationships
that strict schema validation alone cannot resolve. Audits are deterministic,
local, and read-only. A finding is a prompt for human review, not proof of an
error, duplicate charge, fraud, or accounting problem.

## Findings

The audit emits stable codes and aggregate counts:

- `possible_duplicate_invoice`: additional records with the same normalized
  client, dates, currency, line items, status, and payment date but a different
  invoice number;
- `duplicate_line_item`: repeated identical normalized line items beyond the
  first occurrence within an invoice;
- `future_issue_date`: an issue date after the explicit as-of date;
- `future_payment_date`: a recorded payment date after the as-of date;
- `zero_total_active`: a zero-total draft, sent, or paid invoice. Void
  invoices are excluded from this check.

Possible duplicates and repeated lines may be intentional. Future dates can be
valid in prepared records. Zero-value invoices may document legitimate work.
Review the private source records before making any correction.

## Privacy

Reports contain only the as-of date, number of records checked, finding codes,
and aggregate counts. They omit clients, invoice numbers, individual invoice
dates, descriptions, prices, amounts, payment details, statuses, currencies,
and file paths. The audit computes normalized fingerprints in memory and never
stores them in its result.

## Safety and automation

The command validates the ledger normally before auditing it. Invalid schemas,
broken lifecycle records, symbolic-link ledgers, and duplicate invoice numbers
remain hard input errors. The audit does not repair, delete, merge, renumber, or
transition any record.

Exit status 1 means one or more findings require review, 0 means no findings
were detected, and 2 means the input or output request was invalid. Exports
never overwrite an existing file. Keep reports private even though they omit
record values, because counts can still reveal operational information.
