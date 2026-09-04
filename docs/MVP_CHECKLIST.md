# AgentLedger Sellable MVP Checklist

**Control baseline:** SPEC-1-AgentLedger-v1.8 plus the owner-approved Railway hosting amendment dated 2026-09-04.
**Specification SHA-256:** `E42E9D400D93B269A968322C988A9CDE5B0F244484E81641206CC092DA4AA401`
**Implementation-handoff SHA-256:** `770AE605E4C71C4C23379748CC64D7D4EEFF9A9CA700756A5118017B2279F17A`

This is the release ledger, not a feature wish list. A checked item means its stated automated tests and required manual verification passed against the named environment. Code existence alone is not proof.

Status syntax:

- `[ ]` not started
- `[~]` in progress
- `[x]` verified

Evidence for every verified implementation item must name the date, environment, command/test or manual procedure, and durable evidence location. Production-only claims cannot be closed with local evidence.

## Phase 0 — Implementation control files

- [x] The exact supplied `SPEC-1-AgentLedger-v1.8.md` is present and its SHA-256 matches the control baseline. Evidence: exact-copy hash verified locally on 2026-09-04.
- [x] `MVP_CHECKLIST.md` contains the MVP phases, exit conditions, Railway amendment, exclusions, and freeze gate. Evidence: `python scripts/verify_mvp.py --control-files` passed locally on 2026-09-04.
- [x] `DEPLOYMENT_RAILWAY.md`, `SECURITY_INVARIANTS.md`, and `CUSTOMER_PILOT_RUNBOOK.md` are present. Evidence: control-file verification passed locally on 2026-09-04.
- [x] `scripts/verify_mvp.py` validates the control-file set and reports incomplete MVP status without treating file existence as product verification. Evidence: syntax and behavior checks passed locally on 2026-09-04.

## Phase 1 — Repository and Python baseline

- [x] A fresh clone can install the locked dependencies successfully.
- [x] With PostgreSQL available, all migrations run successfully.
- [x] The single selected automated-test strategy runs and passes.
- [x] The Django development server starts.
- [x] Production settings import successfully without weakening production security.
- [x] The server-rendered Django baseline uses minimal vanilla JavaScript and has no Node backend or frontend framework.
- [x] Current official documentation has been checked for Python 3.14, Django 5.2 LTS, PostgreSQL 18, Psycopg 3, Gunicorn, Playwright, `uv`, and Railway; any conflict is documented before an accepted baseline changes.
- [x] The Railway configuration mechanism is explicitly resolved before files are created: current Railway documentation says new services cannot opt into the requested `railway/*.toml` Config-as-Code mechanism.

Phase 1 evidence, 2026-09-04: a Git-metadata-free clean source copy installed 31 locked packages under CPython 3.14.7 and passed Django checks; PostgreSQL 18.6 accepted the two minimal `contenttypes` migrations in the isolated `agentledger-development` container; Ruff and format checks passed; 9 pytest tests passed with 93.42% measured coverage; the live development server returned HTTP 200 from `/healthz` and PostgreSQL/migration-aware `/readyz`; production-settings import and wildcard-host rejection are automated tests. The current Railway Config-as-Code conflict is documented in `DEPLOYMENT_RAILWAY.md` and `railway/README.md`; executable Railway IaC remains correctly deferred to the deployment milestone.

## Phase 2 — Custom user, organization, and tenant control plane

- [x] The custom email-based User model exists before the first permanent migration and uses UUID primary keys where specified.
- [x] Organization and OrganizationMember support owner, admin, assessor, and viewer roles and the enumerated industries.
- [x] User A belongs to Firm A and User B belongs to Firm B in the canonical isolation fixture.
- [x] User A cannot activate Firm B.
- [x] A malformed workspace UUID produces a safe response and never a server error.
- [x] A valid user can switch between two organizations to which that user legitimately belongs.
- [x] Workspace activation is POST-only, CSRF-protected, and revalidates membership before setting organization context.
- [x] User and organization context setters are alias-aware and transaction-local; no persistent session-level tenant setting is used.
- [x] Logout clears the active organization state.

Phase 2 evidence, 2026-09-04, local development against the isolated PostgreSQL 18.6 service: the initial `accounts`, `organizations`, `auth`, and `sessions` migrations applied successfully; `python manage.py makemigrations --check --dry-run` reported no model drift; Ruff format and lint gates passed; and 31 pytest tests passed with 94.19% branch coverage. The automated suite includes case-insensitive email identity and uniqueness, the canonical Firm A/Firm B membership fixture, cross-firm activation denial with session clearing, malformed UUID denial, POST-only and CSRF enforcement, membership revalidation, legitimate two-firm switching, logout state clearing, transaction-local PostgreSQL settings, context-name allowlisting, and explicit database-alias routing.

## Phase 3 — PostgreSQL row-level security (release blocking)

- [x] `agentledger_owner`, `agentledger_app`, and `agentledger_worker` exist with separate credentials and the specified ownership boundary.
- [x] App and worker runtime roles are NOSUPERUSER, NOBYPASSRLS, and do not own tenant business tables.
- [x] Every tenant-owned table has non-null `organization_id`, ENABLE RLS, FORCE RLS, and correct USING and WITH CHECK policies.
- [x] Restricted `app_runtime` and `worker_runtime` aliases prove their actual database identities with `SELECT current_user`.
- [x] Tenant A plus an unfiltered ORM query cannot see Tenant B.
- [x] Tenant A plus raw `SELECT *` cannot see Tenant B.
- [x] Tenant A cannot retrieve Tenant B by a directly supplied primary key.
- [x] An insert carrying Tenant B's organization ID is rejected by PostgreSQL.
- [x] An update aimed at Tenant B affects zero rows or is rejected by PostgreSQL.
- [x] Missing tenant context fails closed.
- [x] Context set on the default connection does not unlock `app_runtime`.
- [x] Worker context cannot access the wrong tenant's business data.
- [x] All tenant-isolation tests pass under the real restricted database roles. Development must stop at this gate if they fail.

Phase 3 evidence, 2026-09-04, local integration against the isolated PostgreSQL 18.6 service: `scripts/verify_rls.py` generated separate high-entropy role credentials in memory, provisioned three LOGIN/NOSUPERUSER/NOBYPASSRLS/NOINHERIT roles without printing those credentials, applied the security migration, and ran the complete suite through distinct `owner_runtime`, `app_runtime`, and `worker_runtime` connections. All 44 tests passed with 93.98% branch coverage, including 13 restricted-role RLS tests. Database introspection proved each alias's `current_user`, `agentledger_owner` ownership of `inventory_items`, forced RLS and non-null organization keys on all current organization-scoped tables, and the tenant policy's USING/WITH CHECK boundary. Canonical A/B rows then proved self-membership bootstrap, unfiltered ORM and raw-SQL isolation, direct-key denial, database rejection of cross-tenant inserts, zero-row cross-tenant updates, missing-context failure, connection-local alias separation, and worker isolation. The development database migration head is `inventory.0002_database_security`; no production state is claimed.

## Phase 4 — Manual inventory

- [ ] Inventory supports the specified vendor, owner, department, users, purpose, cost, systems, data, permissions, autonomy, approval, status, and source fields.
- [ ] Inventory supports add, edit, archive, search, filter, and detail without Django admin.
- [ ] Customer-facing autonomy choices use plain-language behavior descriptions rather than numbered technical levels.
- [ ] The required data categories are available.
- [ ] A realistic demo bookkeeping company contains at least 10 software/AI inventory items created without Django admin.

## Phase 5 — Small deterministic product catalog

- [ ] Roughly 30–50 common AI-enabled products are seeded; the catalog has not expanded into a giant SaaS database.
- [ ] Matching uses the accepted exact priority and never uses fuzzy automatic AI classification.
- [ ] Known identifiers match deterministically and unknown identifiers remain unknown and require review.
- [ ] Mixed-case opaque OAuth identifiers are preserved.
- [ ] UUID provider identifiers are canonicalized as UUIDs.
- [ ] Unicode hostnames have deterministic IDNA normalization.
- [ ] IPv6 addresses with ports normalize correctly.
- [ ] Hostname trailing dots normalize correctly.
- [ ] `api.example.com` remains distinct from `example.com` unless an explicit alias exists.
- [ ] Redirect-URI path and query data are not silently discarded.

## Phase 6 — Three-step CSV import

- [ ] The UI has exactly the three required conceptual steps: select, check/correct, and final approval.
- [ ] Parsing and validation write only to tenant-isolated staging, never directly to production inventory.
- [ ] Errors use row-specific, nontechnical corrective language.
- [ ] Tests cover a valid CSV, invalid row, missing required value, duplicates, cancellation, 100 rows, and cross-tenant staging isolation.
- [ ] A 100-row CSV can be uploaded, validated, previewed, corrected, confirmed, and imported transactionally with no partial production writes.

## Phase 7 — Deterministic policy engine

- [ ] The engine is pure Python and performs no database writes, network calls, current-time reads, LLM calls, executable expressions, `eval`, or `exec`.
- [ ] Only the accepted operators, results, result fields, and precedence rules are supported.
- [ ] Published platform and industry rules are versioned and immutable; a change creates a new version.
- [ ] Regression tests prove the same context, rule version, and engine version produce the same output.

## Phase 8 — Accounting/bookkeeping risk pack

- [ ] The only MVP industry pack covers payroll, tax, banking, financial actions, accounting-data modification, client exports, communications/transmission, autonomy, approval, retention, model-training behavior, and vendor-review status.
- [ ] Findings use plain business language and never claim AgentLedger blocked or enforced a third-party action.
- [ ] A realistic bookkeeping inventory produces findings a nontechnical bookkeeper can understand without technical documentation.

## Phase 9 — Deterministic risk engine

- [ ] The eight dimensions, weights, 0–100 scales, weighted sum, and Low/Moderate/High/Critical bands match the approved baseline.
- [ ] Mandatory-rule severity/risk floors apply deterministically.
- [ ] Every contribution stores reason, rule, dimension, and points.
- [ ] Every score visible in the UI answers “Why did this receive this score?” without source-code inspection.

## Phase 10 — ROI engine

- [ ] Inputs, assumption provenance, and formulas match the approved baseline.
- [ ] The UI displays the arithmetic used for every result.
- [ ] Zero-cost denominators never produce infinity or divide-by-zero failures.
- [ ] A customer can reproduce every displayed ROI number with a calculator.

## Phase 11 — Immutable assessment snapshots

- [ ] A snapshot captures inventory, evidence references, platform/industry and organization rule versions, risk configuration, ROI assumptions, timestamp, and engine version.
- [ ] Canonical input and result SHA-256 hashes are stored with assessment identity and version metadata.
- [ ] Inventory, rules, or ROI edits cannot mutate historical assessments.
- [ ] Yesterday's assessment remains identical after today's changes.

## Phase 12 — Visual no-code rule builder

- [ ] Sentence-style controls can create, edit, duplicate, disable, delete, test, and explain rules.
- [ ] Only the approved non-enforcement effects are available; blocking, revocation, permission changes, and other enforcement effects are unavailable.
- [ ] Structured JSON is hidden behind “View technical details” and contains no executable code.
- [ ] State-changing operations are POST-only and CSRF-protected.
- [ ] A nontechnical user can create the payroll plus external-transmission human-approval/High-floor example without code.

## Phase 13 — PostgreSQL background jobs

- [ ] Durable jobs use PostgreSQL LISTEN/NOTIFY, SKIP LOCKED, claim tokens, leases, fencing, retry schedule, and recovery scans; Redis and Celery are absent.
- [ ] Only the approved MVP job types are present; Microsoft and Google discovery jobs are absent.
- [ ] Retry timing uses the locked database row, never caller-provided attempts.
- [ ] Two workers racing for one job yield one winner.
- [ ] An expired lease can be reclaimed by a second worker.
- [ ] Stale-worker completion and failure are rejected.
- [ ] A missed notification is recovered by periodic scanning.
- [ ] A job created before LISTEN is found by the initial scan.
- [ ] Jobs remain correct across concurrency, worker crash, connection restart, and missed notification.

## Phase 14 — Audit events and Merkle sealing

- [ ] All enumerated business and security-relevant events are recorded independently of later sealing.
- [ ] Complete event envelopes use RFC 8785 canonicalization, domain-separated SHA-256, AL-MERKLE-1, tenant chain heads, block metadata, and a verification command.
- [ ] Only the tenant's chain-head row is locked while sealing; different tenants can seal concurrently.
- [ ] Modifying, deleting, or reordering a sealed event makes verification fail.
- [ ] Concurrent same-tenant sealers produce one chain advancement.
- [ ] Different tenants can seal concurrently.
- [ ] UI claims only tamper evidence/valid verification, never magical immutability, blockchain protection, or unhackability.

## Phase 15 — Canonical browser reporting

- [ ] One canonical report context drives browser and PDF reports.
- [ ] The report contains every required section and version/identity field.
- [ ] Report identifiers use the accepted deterministic sequence.
- [ ] The report is titled as an AI Risk & ROI Assessment and makes no unsupported compliance or security guarantee.

## Phase 16 — Isolated PDF renderer

- [ ] A separate renderer has no public domain and receives no database, OAuth, KEK, or unnecessary bucket credentials.
- [ ] The renderer accepts validated structured data and fixed templates, never customer-provided arbitrary HTML or output paths.
- [ ] Chromium runs non-root with its sandbox enabled; JavaScript is off, service workers are blocked, and every browser request is aborted.
- [ ] Customer strings are escaped and payload, time, output size, process, and memory limits are enforced where supported.
- [ ] Script, remote image/CSS, `file://`, and traversal payloads cannot execute, fetch, or read sensitive local files.

## Phase 17 — Private report storage

- [ ] PDFs and future exports/certificates are stored in the private `reports` object bucket, never ephemeral application storage.
- [ ] PostgreSQL records object key, content type, SHA-256, size, report ID, creation time, and assessment snapshot ID.
- [ ] Object keys use organization/assessment/report scoping and are never sufficient authorization.
- [ ] Authenticated membership, tenant RLS, and report ownership are checked before a short-lived presigned GET or authenticated proxy response.
- [ ] Tenant A cannot retrieve Tenant B's report even with Tenant B's report UUID and object key.
- [ ] Before customer data, the absence of bucket API server-side-encryption controls, versioning, object locks, and lifecycle rules in current Railway documentation has a documented, owner-approved security disposition.

## Phase 18 — Credential cryptography module

- [ ] The connector-ready module implements versioned KEKs, per-record DEKs, AES-256-GCM, tenant/record AAD binding, normal rotation, and compromised-key rotation without creating production OAuth credentials.
- [ ] Wrong tenant AAD, record AAD, or key causes decryption failure.
- [ ] Normal rotation keeps existing ciphertext recoverable.
- [ ] Compromised-key rotation creates a new DEK and ciphertext.
- [ ] Old KEKs cannot be removed while an active envelope references them.

## Phase 19 — Security and production settings

- [ ] Production uses `DEBUG=False`, secure cookies, CSRF, HTTPS awareness, appropriate HSTS, explicit hosts/origins, strong secrets, clickjacking/content-type defenses, and secret-safe request logging.
- [ ] `ALLOWED_HOSTS = ["*"]` is absent; actual Railway/custom hosts and Railway's healthcheck hostname are handled explicitly.
- [ ] `/healthz` proves process liveness without tenant context.
- [ ] `/readyz` proves application readiness, database connectivity, and required migration state without tenant context.
- [ ] Production security validation and Django deployment checks pass.

## Phase 20 — Railway production deployment

- [ ] 20.1: A private GitHub repository exists, `main` is protected from force pushes, release candidates are tagged, and no secrets are committed.
- [ ] 20.2: The Railway project and production environment exist with Railway PostgreSQL and no public database TCP proxy.
- [ ] 20.3: Separate owner/app/worker database credentials are provisioned; long-running web and worker services never receive owner credentials.
- [ ] 20.4: `web` is the only publicly reachable application service, binds Gunicorn to Railway's injected port, and uses `/readyz` as deployment healthcheck.
- [ ] 20.5: `worker` has no public domain and reaches PostgreSQL privately.
- [ ] 20.6: `renderer` has no public domain, exposes only its private application port, and receives no useful application secrets.
- [ ] 20.7: The private `reports` bucket exists; only web/worker receive credentials as required.
- [ ] 20.8: Production variables are present in Railway, secrets are not committed or copied into `.env`, and `.env.example` contains names only.
- [ ] 20.9: Owner-credential migrations run only in a bounded migration operation, before incompatible code, using expand/contract compatibility.
- [ ] 20.10: The Railway domain is fully verified before an approved custom domain is attached; customer outreach never uses a local address.
- [ ] 20.11: Scheduled volume backups and PITR are enabled as approved, a custom-format logical dump is encrypted off-platform, and an actual clean restore drill passes before customer data.
- [ ] 20.12: A smoke test from an unrelated network verifies HTTPS, login, workspace, inventory, CSV, assessment, ROI, rule builder, browser/PDF reports, logout/login, authorized download, and cross-tenant isolation.
- [ ] Production availability has no dependency on the founder's computer, WSL2, router, home Internet, or personal availability; Caddy is not deployed.
- [ ] Railway deployment IDs are recorded as release evidence.

## Phase 21 — Demo data

- [ ] Demo Bookkeeping Company contains the specified realistic manual inventory, including one unknown tool, without implying live connectors.
- [ ] Demo scenarios cover payroll, banking, external transfer, missing approval, unknown retention, low risk, poor ROI, and strong ROI.
- [ ] A polished demo assessment and PDF contain at least one genuinely justified Low, Moderate, High, and Critical finding.

## Phase 22 — MVP UX walkthrough

- [ ] The complete 18-step customer workflow passes without Django admin, including historical assessment retrieval after logout/login.
- [ ] A small organization reaches its first useful manual assessment in under 30 minutes.
- [ ] Required verbal explanations are recorded; repeated explanations are treated as UX defects.

## Phase 23 — Final MVP release gate

- [ ] The full automated suite passes, including tenant RLS, raw SQL, worker leases, rules, risk, ROI, CSV, snapshots, Merkle, renderer security, and report ownership.
- [ ] Django deployment checks and repository production-security validation pass.
- [ ] No cross-tenant data access is possible under the tested web and worker roles.
- [ ] Identical assessment input produces identical output and identical input/ruleset/engine produces identical hashes.
- [ ] Historical assessments remain unchanged.
- [ ] Manual inventory is never silently overwritten.
- [ ] Unknown products remain unknown.
- [ ] The PDF matches its immutable assessment snapshot.
- [ ] Worker crash recovery passes.
- [ ] Report downloads are tenant-authorized.
- [ ] Backup restoration passes on a clean target.

## Sellable MVP acceptance matrix

- [ ] Authentication
- [ ] Organizations and organization membership
- [ ] PostgreSQL RLS
- [ ] Manual AI/software inventory
- [ ] CSV import with preview
- [ ] Small deterministic product catalog
- [ ] Accounting/bookkeeping rules pack
- [ ] Deterministic policy engine
- [ ] Deterministic risk engine
- [ ] ROI calculator
- [ ] Visual no-code rule builder
- [ ] Findings and remediation UI
- [ ] Immutable assessment snapshots
- [ ] Browser report
- [ ] PDF report
- [ ] Audit trail
- [ ] Merkle audit sealing
- [ ] PostgreSQL background jobs
- [ ] Tenant-isolation tests
- [ ] Security release gates
- [ ] Railway deployment
- [ ] Verified backups
- [ ] Health and readiness checks
- [ ] Demo organization
- [ ] Founder-assisted onboarding path

## Explicitly excluded from the MVP

Microsoft and Google connectors, QuickBooks/Xero connectors, continuous/scheduled discovery, continuous monitoring, browser extension, SIEM integration, automated enforcement, automated permission changes, LLM risk decisions, subscription billing, public signup, additional industry packs, mobile application, Node backend, React SPA, Redis, Celery, RabbitMQ, Kafka, Elasticsearch, Kubernetes, and Caddy are not MVP work.

## Freeze gate

- [ ] All Phase 23 items and every Sellable MVP acceptance-matrix item are verified with durable evidence.
- [ ] Git tag `v0.1.0` identifies the frozen release.
- [ ] The release record contains commit hash, migration head, dependency-lock hash, Railway deployment IDs, and date.
- [ ] Development has stopped except for defects that prevent security, correctness, onboarding, assessment, reporting, payment, or customer use.
- [ ] The project has switched from BUILD MODE to SELL MODE.

When and only when the freeze gate is fully verified, the controlling declaration is:

```text
MVP CODE FREEZE REACHED.
THE NEXT TASK IS CUSTOMER VALIDATION.
```
