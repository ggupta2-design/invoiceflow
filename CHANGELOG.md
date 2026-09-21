# Changelog

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
