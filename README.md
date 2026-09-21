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


## Quick start

```bash
python -m pip install -e .

invoiceflow validate examples/invoice.json
invoiceflow create ~/private/invoiceflow-ledger.json examples/invoice.json
invoiceflow status ~/private/invoiceflow-ledger.json EXAMPLE-001 sent
invoiceflow due ~/private/invoiceflow-ledger.json \
  --as-of 2026-09-21 --days 30 --redact-clients
```

InvoiceFlow calculates each line with exact decimal arithmetic, stores invoices
in a strict versioned JSON ledger, and performs no network requests. Ledgers are
updated atomically. Report exports are private and non-overwriting.

Exit status 0 means the requested operation succeeded. A due review returns 1
when overdue invoices need attention. Invalid data, unsafe transitions, and
conflicting outputs return 2.

See the [usage guide](docs/usage.md) and
[privacy and safety guide](docs/privacy-and-safety.md) before working with real
customer or financial data.

## Status

InvoiceFlow 0.1.0 provides private local invoice tracking, lifecycle controls,
exact totals, and due-date automation.
