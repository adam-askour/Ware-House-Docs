# Document Management System — Implementation and Test Roadmap

## Working method

- Build vertical, testable increments.
- Keep the application runnable after every phase.
- Use fictional or anonymized PDFs only.
- Do not connect real scanners until their capabilities are verified.
- Do not claim OCR or classifier accuracy without a labelled evaluation set.
- Apply authorization in services/querysets, not only by hiding buttons.

## Phase 0 — Project foundation

### Build

- Django project and modular apps
- PostgreSQL and Redis
- Celery worker and scheduler
- Docker Compose development environment
- environment-variable configuration and example file
- structured logging
- health checks
- test framework, formatting, and static checks
- protected media directories

### Exit criteria

- One command starts the development stack.
- Web application, database, queue, and worker report healthy.
- Tests run in an isolated test configuration.
- No secrets are committed.

## Phase 1 — Identity, organization, and authorization

### Build

- custom user model
- local login/logout and password management
- departments and multi-department memberships
- employee, department chief, superuser administrator, and confidential authorizations
- active/deactivated accounts
- scanner codes
- reusable document-access policy service
- administrator management screens

### Tests

- password is hashed
- deactivated user cannot log in
- user can belong to several departments
- ordinary member cannot perform chief actions
- administrator does not automatically receive confidential content access
- unauthorized direct URL and file requests return no content

### Exit criteria

- Role and department rules are enforced server-side.

## Phase 2 — Document core and manual upload

### Build

- document, department assignment, metadata, storage, version, and status models
- protected original storage
- PDF-only upload validation
- manual upload page
- document list and basic filters
- protected file-serving endpoint
- audit events for upload, view, and download

### Tests

- renamed non-PDF is rejected
- encrypted/corrupt PDF is rejected or quarantined
- original checksum remains unchanged
- unauthorized user cannot preview or download
- one primary department is required before normal department publication

### Exit criteria

- Authorized employees can upload, list, preview, and download test PDFs safely.

## Phase 3 — Scanner simulator and ingestion

### Build

- scanner records and intake configuration
- simulator submitting PDF, employee code, scanner ID, and scan time
- file stability/completion detection
- ingestion ledger and idempotency key
- checksum and exact-duplicate detection
- processing/processed/failed/quarantine source areas
- immediate `Processing` document appearance

### Tests

- partially written file is not consumed
- unknown/inactive employee code is quarantined or reviewed
- ordinary employees cannot submit a confidential classification, including through
  a crafted request; known confidential documents must be scanned by a user with the
  matching explicit authorization
- a scan later suspected to be confidential is withheld from publication and routed
  to an appropriately authorized review queue without leaking restricted metadata
- repeated event does not create a second unintended document
- transient failure retries without data loss
- successful import associates the correct employee and scanner

### Exit criteria

- Simulated scans appear automatically for the correct employee.

## Phase 4 — OCR and searchable PDF

### Build

- OCR job pipeline
- existing-text detection
- orientation and deskew
- conservative image preprocessing
- French, Arabic, and English Tesseract configuration
- OCRmyPDF searchable derivative
- OCR text stored by page
- quality/warning information
- PDF.js viewer
- processing status updates and failure retry

### Tests

- printed French sample is searchable
- printed Arabic sample is searchable
- printed English sample is searchable
- rotated/skewed sample improves or produces a warning
- original remains unchanged
- page text is correctly associated with its page
- OCR failure retains the source and creates an administrator-visible failure

### Exit criteria

- Representative printed samples become searchable and viewable page by page.

## Phase 5 — Search

### Build

- PostgreSQL full-text index
- weighted title, metadata, and OCR search
- access-filtered search query
- page number and highlighted snippet
- document filters
- direct viewer link to matching page
- empty and permission-safe result behavior

### Tests

- title outranks body-only match when appropriate
- body match returns the right page
- unauthorized document does not appear or affect visible counts
- French, Arabic exact-token, and English samples return expected results
- filters combine correctly

### Exit criteria

- Users can find authorized PDFs by content without knowing filenames.

## Phase 6 — Classification and publication

### Build

- configurable document types and metadata fields
- keyword/pattern rules
- template fingerprints
- source-signal scoring
- separate confidence and explanation per output
- suggested title, type, departments, sensitivity, and fields
- automatic publication thresholds
- employee and authorized review tasks
- human correction history
- optional local TF-IDF classifier behind a feature flag when labelled data exists

### Tests

- reliable invoice rule produces expected suggestion and explanation
- uncertain normal case creates employee review
- sensitive rule creates authorized review
- department conflict does not publish broadly
- correction preserves original suggestion and actor
- disabling the optional classifier leaves deterministic rules functional

### Exit criteria

- Automation publishes only cases meeting configured safety rules.

## Phase 7 — Sharing, versions, reviews, and notifications

### Build

- employee/department shares and expiration
- confidential-sharing restrictions
- review inbox and decisions
- neutral notification after access removal
- replacement versions and restoration
- duplicate comparison decisions
- notifications page

### Tests

- ordinary document can be shared within policy
- confidential document cannot be shared by unauthorized employee
- expired share stops access
- scanning employee loses access after restricted classification when required
- notification leaks no restricted metadata
- version replacement preserves previous version

### Exit criteria

- Collaboration does not bypass document sensitivity.

## Phase 8 — Retention, audit, backup, and dashboards

### Build

- immutable application audit service
- deletion requests
- retention rules and daily expiry task
- recycle bin, restore, and delayed purge
- daily PostgreSQL and media backup jobs
- backup status
- employee, chief, and administrator dashboards
- queue and scanner health

### Tests

- ordinary employee cannot permanently delete directly
- restore works during recovery period
- purge removes all configured file derivatives
- audit records actor and before/after values
- backup failure is visible
- dashboard figures are permission-scoped

### Exit criteria

- Operational and lifecycle controls are demonstrable end to end.

## Phase 9 — Hardening and company demonstration

### Build/check

- threat and permission review
- file-size/page-count limits
- rate limits
- secure headers and cookie settings
- CSRF protection
- backup restoration rehearsal
- accessibility and browser checks
- performance test using a realistic daily batch
- operator and administrator documentation
- scanner integration interface documented

### Exit criteria

- A fresh machine can reproduce the prototype.
- A scripted demonstration covers scanning, OCR, search, review, sharing, and deletion.
- Known limitations are documented.

## Test document set

Create only fictional/anonymized files:

1. French invoice, 2 pages, clear print
2. Arabic administrative letter, 1 page, clear print
3. English contract, 4 pages
4. French/Arabic mixed document
5. Rotated invoice
6. Skewed low-contrast purchase order
7. PDF already containing text
8. Exact duplicate PDF
9. Similar but legitimate repeated invoice
10. Corrupt PDF
11. Password-protected PDF
12. HR document containing fictional salary/CIN-like patterns
13. Multi-department purchasing/accounting document
14. Mostly handwritten page, expected to warn rather than guarantee extraction

Each sample needs expected:

- OCR keywords and page numbers
- type
- primary/additional departments
- sensitivity
- metadata values
- expected publication/review decision
- users allowed and denied

## Prototype success demonstration

1. Administrator creates departments and users.
2. Simulator sends a French invoice for an employee code.
3. Employee sees `Processing` immediately.
4. OCR completes and rules classify it reliably.
5. Document publishes automatically to Accounting.
6. Accounting employee searches a word inside page 2 and opens that page.
7. Unauthorized HR-only user cannot discover the invoice.
8. A fictional sensitive HR scan removes unauthorized scanner access and enters authorized review.
9. A manual upload follows the same pipeline.
10. A duplicate is flagged.
11. A replacement creates version 2.
12. A deletion request enters the recycle-bin workflow.
13. Audit and dashboard views show the events.

## Information still needed before real scanner integration

- scanner make and model
- supported SMB/network-folder, email, SFTP, log, or API features
- exact place where the entered employee code is exposed
- scanner authentication capabilities
- file completion/rename behavior
- maximum and typical PDF size
- network details and protected destination
