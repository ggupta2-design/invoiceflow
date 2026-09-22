# Reminder policies

InvoiceFlow reminder policies are strict, local JSON files that describe when an
invoice is eligible for human follow-up. They create plans only. InvoiceFlow
does not send email, text messages, payment requests, or notifications.

A schema-version-1 policy contains exactly these fields:

- `name`: a label of 1 to 100 safe characters;
- `upcoming_days`: 1 to 32 unique day offsets from 0 through 365;
- `overdue_grace_days`: completed overdue days to skip, from 0 through 365;
- `overdue_interval_days`: repeat cadence from 1 through 365 days;
- `maximum_reminders`: plan limit from 1 through 500 actions.

Upcoming actions occur only at an exact configured offset. Offset 0 means the
due date. Overdue cadence starts on the first day after the grace period and
repeats at the configured interval. For example, grace 2 and interval 7 selects
overdue days 3, 10, 17, and so on.

Only sent invoices are eligible. Draft, paid, and void invoices are excluded.
Plans prioritize the oldest overdue invoices, then invoices due today, then
upcoming invoices. Ties use due date and case-insensitive invoice number.
The global maximum is applied after sorting, and reports explicitly show both
the eligible and scheduled counts plus whether the result was truncated.

Policy loading rejects unknown or missing fields, unsupported schema versions,
duplicate offsets, unsafe bounds, symbolic links, invalid UTF-8, invalid JSON,
and files larger than 64 KiB. Policy validation and plan creation are
deterministic and make no network requests or ledger changes.

Use the fictional [example policy](../examples/reminder-policy.json) as a
starting point. Review every plan and verify the recipient, amount, status, and
communication context outside InvoiceFlow before contacting a customer.
