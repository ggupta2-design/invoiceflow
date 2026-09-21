# InvoiceFlow

InvoiceFlow is a local-first command-line tool for creating, tracking, and
reviewing invoices without sending financial or customer data to a hosted
service.

The first milestone focuses on predictable invoice fundamentals:

- validated invoice and line-item records;
- exact decimal subtotal, tax, and total calculations;
- strict JSON inputs and local ledgers;
- atomic ledger updates;
- safe draft, sent, paid, and void lifecycle transitions;
- due and overdue invoice reviews;
- readable and JSON reports with optional client-name redaction;
- automation-friendly exit statuses;
- no accounts, API keys, payment processor, or network access.

InvoiceFlow is being built as part of an eight-week automation project
challenge. Public examples use fictional data. Real customer and payment
information must remain in private local files.
