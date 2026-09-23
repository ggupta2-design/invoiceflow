# Privacy and financial-data safety

InvoiceFlow is local-first. It does not make network requests, send invoices,
process payments, upload files, or require credentials.

## Sensitive data

Invoice inputs, ledgers, and reports may contain customer names, invoice
numbers, dates, descriptions, prices, tax information, and payment status. Keep
real files outside this public repository. Common ledger, invoice, private, and
report locations are excluded by `.gitignore`, but ignore rules are not access
control or encryption.

Do not store bank details, card numbers, government identifiers, authentication
tokens, passwords, or unnecessary personal data in InvoiceFlow records. The
schema intentionally does not provide fields for those values.

## Local storage boundaries

Ledgers and exported reports are written with owner-only permissions where the
operating system supports them. Ledger updates use a temporary file and atomic
replacement. Report exports never overwrite an existing destination. Symbolic
link ledgers and output destinations are rejected.

These safeguards do not encrypt files, verify directory permissions, create
backups, or prevent another process running as the same user from reading data.
Use operating-system access controls and approved encrypted storage when
required.

## Calculation and workflow limits

InvoiceFlow uses decimal arithmetic and rounds monetary line values to cents
with half-up rounding. It does not determine legally correct taxes, currency
conversion, accounting treatment, late fees, or regulatory compliance. Review
all calculations before issuing an invoice.

Lifecycle transitions preserve a small audit-friendly state model:

- draft invoices can become sent or void;
- sent invoices can become paid or void;
- paid and void invoices are terminal;
- paid transitions require an explicit payment date.

The ledger stores current state, not a complete tamper-evident accounting audit
log.

## Reporting privacy

Invoice summaries omit line-item descriptions. List and due reports can replace
client names with `[redacted]`, but invoice numbers, dates, currencies, amounts,
and status patterns may still identify a customer or business relationship.
Review every report before sharing it.

## Aging report boundaries

Receivables aging reports use aggregate counts and amounts by currency and age
bucket. They omit customer names, invoice numbers, individual dates, line
descriptions, and per-invoice balances. Aggregation reduces exposure but does
not guarantee anonymity: a distinctive total, currency, or small count can
still disclose commercially sensitive information.

The aging command is local and read-only. It does not modify invoice status,
estimate collectability, convert currencies, calculate late fees, or reconcile
payments. Store exports with the same protections as the ledger and review them
before sharing.

## Reminder planning boundaries

Reminder policies describe timing and limits, not message content or recipients.
Plans contain invoice numbers, client names unless redacted, due dates,
currencies, and amounts. They omit line-item descriptions and never contain
email addresses or phone numbers because the invoice schema does not support
those fields. Treat plans as sensitive financial records and prefer
`--redact-clients` for review outside the private working directory.

Planning is read-only: it does not modify the ledger, record that a reminder was
sent, or suppress a later action based on prior communication. A scheduled
action is not evidence that contact is appropriate. Before communicating,
confirm the invoice status, recipient, contractual terms, local requirements,
and prior correspondence in an approved system.

InvoiceFlow does not send reminders, contact clients, schedule itself, calculate
late fees, reconcile payments, or verify recipients.
