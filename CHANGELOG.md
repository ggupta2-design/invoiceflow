# Changelog

## 0.3.0 — 2026-09-23

- Added read-only receivables aging for sent invoices.
- Added current, 1–30, 31–60, 61–90, and 91+ day buckets.
- Added exact boundary handling using an explicit reproducible as-of date.
- Added exact Decimal counts and totals kept separate by currency.
- Added aggregate reports that omit customers, invoice identifiers, individual
  dates, line descriptions, and per-invoice balances.
- Added readable and JSON aging formats with protected non-overwriting exports.
- Added automation-friendly overdue, clear, and invalid exit statuses.
- Added tests for bucket boundaries, lifecycle eligibility, multiple currencies,
  exact totals, privacy, ledger immutability, exports, CLI behavior, and public
  APIs.
- Documented aging semantics, disclosure limits, workflow usage, and accounting
  interpretation boundaries.

## 0.2.0 — 2026-09-22

- Added strict schema-version-1 local reminder policies.
- Added exact upcoming-day, grace-period, and overdue-cadence rules.
- Added sent-only reminder eligibility with paid, void, and draft exclusions.
- Added stable overdue-first prioritization and global plan bounds.
- Added readable and JSON reminder plan reports with client-name redaction.
- Added explicit eligible, scheduled, state-count, and truncation summaries.
- Added standalone policy validation and read-only reminder planning commands.
- Added protected, non-overwriting reminder plan exports.
- Added automation-friendly no-action, action-required, and invalid statuses.
- Added tests for policy schemas, bounds, cadence, priority, privacy, exports,
  immutability, and end-to-end CLI behavior.
- Added a conservative fictional policy example and operational guidance.
- Documented human-review, financial-data, and communication boundaries.

## 0.1.0 — 2026-09-21

- Added validated invoice, line-item, currency, date, and lifecycle models.
- Added exact Decimal subtotal, tax, and total calculations.
- Added strict schema-version-1 invoice JSON loading and serialization.
- Added private, atomic, deterministic local ledger storage.
- Added case-insensitive invoice-number uniqueness safeguards.
- Added safe draft, sent, paid, and void lifecycle transitions.
- Added explicit payment-date validation and terminal-state protections.
- Added bounded overdue, due-today, and upcoming invoice reviews.
- Added readable and JSON summaries with optional client-name redaction.
- Added protected report exports that never overwrite existing files.
- Added automation-friendly success, attention, and invalid exit statuses.
- Added tests across models, calculations, schemas, storage, workflows, reports,
  exports, due reviews, and end-to-end CLI behavior.
- Added continuous integration for Python 3.10 through 3.13.
- Documented privacy, financial-data, calculation, and workflow boundaries.
