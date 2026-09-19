# AUDIT TRAIL & REPRODUCIBILITY — S.P.O.T.

**Date**: September 4, 2026  
**Status**: IMPLEMENTED & TESTED  

---

## 1. Cryptographic SHA-256 Hash Chain

Every audit event is persisted to the `audit_events` table as an immutable record. The SHA-256 digest is computed as:

$$\text{event\_hash} = \text{SHA256}(\text{previous\_event\_hash} \parallel \text{timestamp} \parallel \text{entity\_type} \parallel \text{entity\_id} \parallel \text{event\_type} \parallel \text{actor\_id} \parallel \text{payload\_json})$$

If no prior event exists, `previous_event_hash` defaults to `"GENESIS_BLOCK_HASH"`.

---

## 2. Append-Only Immutability

- `AuditRepository` only exposes `log_event()` and `list_by_entity()`.
- Updates and deletions on `audit_events` are strictly prohibited by application policy and database constraints.
- Any attempt to tamper with past audit events invalidates subsequent hashes in the chain.

---

## 3. Historical Reproducibility Formula

To ensure historical lot grading disputes can be audited and reproduced years later:

$$\text{Inspection} + \text{Input Images} + \text{Model Version} + \text{Vision Results} + \text{Grading Profile Version} = \text{Reproducible Record}$$

Historical inspection rows reference specific `ModelVersion` (e.g. `MOD-0.1.0-MOCK`) and `GradingProfileModel` (e.g. `prototype-procurement-v1`) primary keys. Modifying default profile rules or deploying a new vision model update will never mutate historical inspection outputs.
