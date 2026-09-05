# Stewardence Collector — version 0.1.0

The one-shot Collector observes supported Windows installed-program registry
entries. The existing Django application receives and interprets bundles. No
additional Railway service is required. Installer/release delivery and automatic
catalog/rule reconciliation remain Phases 19C–19D.

## Evidence boundary

Only `DisplayName`, `DisplayVersion` and `Publisher` are read under the HKLM/HKCU
uninstall registry roots, in 32-bit and 64-bit views. The bundle contains these
bounded values and their source locator. There is no browser-history, cookie,
password, credential, project-content or recursive filesystem reader.

Records preserve detector ID/version, observation time, source type/locator,
identifier, version, publisher and a SHA-256 over RFC8785 canonical content.
The enclosing versioned bundle also has a canonical SHA-256. Strict validation
rejects additional fields, unsupported versions, duplicate fields/observations,
tampering, malformed dates, nested values and bundles over 2 MB or 2,000 records.
Coverage is complete, partial or unsupported. Partial/unsupported scans must never
be used as evidence of absence.

Device IDs are stable pseudonymous UUIDs selected in the installation profile or
provided explicitly. They contain no hostname or Windows username. Use the same
UUID for rescans of the same device. Observation time changes across runs; source
fingerprints remain stable. Hashes detect content changes, not device authenticity.
An uploaded bundle is Collector-reported evidence, not remotely attested truth.

## Current execution and ingestion

From this checkout, run `python -m collector --device-id UUID --output NEW_JSON_PATH`
with the locked dependencies installed. The output path must be new. Review the
bundle before submitting it through `/inventory/discovery/` while signed in to the
appropriate workspace. OWNER, ADMIN or ASSESSOR membership is required to upload;
the same session, CSRF and tenant checks as inventory apply.

Scans and observations are stored in `discovery_scans` and `detection_evidence`.
Repeated identical bundles return the existing scan. Historical rows remain when
subsequent scans omit observations. Both tables force RLS; app has SELECT/INSERT,
worker SELECT only. Runtime UPDATE/DELETE are absent. A composite foreign key
prevents evidence from referencing a different tenant's scan. Policy and cost
decisions do not execute in the Collector.

## Phase 19B proof

Verified 2026-09-05 UTC / 2026-09-04 America/Chicago:

- Collector/ingestion tests: 13 passed.
- Collector/ingestion plus actual restricted-role evidence tests: 19 passed.
- Ruff format/lint and migration drift: clean.
- Real Windows scan: 222 observations, complete coverage.
- Two reads at the same supplied observation timestamp returned identical records;
  canonical observations hash `6ac60e5a5fec89c49b1e49d1157ff16677b00e99196ebab78dd2bf3141ad8e8e`.
- Raw real-device bundle retained only under ignored local `work/`; file hash
  `B273CCEF8FF9F0EF153DCBB5FBB71AEC9426FD1D5645D89773E31CD097F386DC`.
  No real device inventory was committed to the public repository.

The current deliverable is the executable Python Collector core and validated
upload/storage path. Windows packaging, signed installation profiles, versioned
release publication, deterministic reconciliation and report lineage are open
gates. This document does not claim those later capabilities are complete.
