# Backup and recovery

InvoiceFlow backups are local, versioned JSON envelopes containing a complete
validated ledger plus a SHA-256 checksum of its canonical ledger data. They are
intended for copying a ledger into separate protected storage and recovering it
to a new file.

## Safety guarantees

- the source must be an existing, valid, non-symbolic-link ledger;
- backup destinations are created with owner-only permissions where supported;
- an existing or symbolic-link destination is never overwritten;
- verification checks the backup schema, embedded ledger schema, invoice count,
  canonical form, and SHA-256 checksum;
- checksum comparison uses a constant-time comparison;
- restore verifies the complete backup before creating a destination;
- restore requires the exact CLI acknowledgment `--confirm RESTORE`;
- restored ledgers use the standard strict ledger format and can be loaded by
  normal InvoiceFlow commands;
- backup input is limited to 64 MiB.

## Important limits

A backup contains every invoice value in the ledger, including customer names,
invoice numbers, dates, line descriptions, amounts, and statuses. It is as
sensitive as the original ledger. The checksum detects accidental changes and
unsophisticated tampering; it is not encryption, a digital signature, proof of
authenticity, or protection from someone who can replace both content and
checksum.

InvoiceFlow does not encrypt, upload, rotate, schedule, retain, or securely
delete backups. It does not inspect parent-directory permissions or verify that
the destination is on independent storage. Keep backups outside the repository
in approved encrypted storage and apply operating-system access controls.

Restore never merges data and never replaces an existing ledger. Choose a new
destination, inspect the restored ledger, and deliberately move it into service
using your normal operational controls.
