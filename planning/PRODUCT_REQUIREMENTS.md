# Document Management System — Product Requirements

## 1. Document status

- Product type: company prototype
- Interface language: English
- Deployment target: one company building on one local network
- Expected users: approximately 100 employees
- Expected workload: approximately 200 scanned pages per day
- Budget for prototype: no paid services or paid licenses
- File scope for prototype: PDF only
- Scan rule: one scan job represents one document
- Hardware dependency: the real scanner integration remains replaceable until the scanner model and the way it exposes the employee code are confirmed

## 2. Product vision

Build a browser-based document management system in which an employee scans a document once and does not manually upload it afterward. The platform detects the PDF, associates it with the scanning employee, preserves the original, runs OCR, classifies it, applies access rules, and makes it searchable by words appearing inside the document.

The primary product promise is:

> Scan once; the authorized document appears automatically in the platform and becomes searchable, with human work required only for uncertain, sensitive, or failed cases.

## 3. Goals

1. Automatically ingest PDFs produced by shared scanners.
2. Identify the scanning employee using a permanent scanner identification code.
3. Preserve an unmodified original of every accepted PDF.
4. Extract French, Arabic, and English text using local OCR.
5. Preprocess rotated, skewed, noisy, or low-contrast pages before OCR.
6. Search document content, titles, metadata, departments, and extracted business fields.
7. Open a search result on the matching page and show a highlighted excerpt.
8. Classify documents by type, one primary department, additional departments, and sensitivity.
9. Automatically publish reliable ordinary documents.
10. Route uncertain normal documents to the scanning employee.
11. Route sensitive or conflicting cases to the responsible department chief.
12. Enforce access before returning search results, previews, or files.
13. Allow manual PDF uploads through the same processing pipeline.
14. Maintain versions, notifications, retention, a recycle bin, daily backups, and an immutable audit trail.

## 4. Non-goals for the first prototype

- Mobile application
- External/public sharing links
- Electronic signatures
- General approval workflows
- Multiple documents inside one scan job
- Guaranteed handwriting recognition
- Advanced Arabic morphological or fuzzy search
- Cloud deployment
- Single sign-on
- Generative-AI chat or summaries
- High-availability infrastructure
- Automatic classification claimed as accurate without evaluation data

## 5. Product principles

### 5.1 Immediate personal availability

After safe validation, a new scan appears in the scanning employee's dashboard as `Processing`. OCR and classification continue in the background.

### 5.2 Separate ingestion from publication

Importing a document does not automatically grant department-wide access. Wider publication occurs only after the document's department, sensitivity, and permissions are reliable.

### 5.3 Preserve originals

The original PDF is immutable. Searchable PDFs, previews, thumbnails, OCR text, and later versions are stored separately.

### 5.4 Deny by default

Documents are visible only through explicit ownership, department membership, role authorization, or a valid share. Search must not reveal that an unauthorized document exists.

### 5.5 Human review by exception

Reliable ordinary documents publish automatically. Humans intervene only for uncertainty, sensitivity, conflicts, duplicates, deletion, or processing failure.

### 5.6 Explainable automation

The system records which rules, templates, source signals, and classifier outputs produced every suggestion and confidence score.

## 6. Actors and roles

### Employee

- View authorized personal, department, and shared documents
- See their scans immediately
- Scan and upload documents as normal only; employees must give known confidential
  documents to a person with the corresponding explicit confidential authorization
- Search authorized content
- Confirm or correct uncertain normal classifications
- Correct permitted metadata
- Share permitted documents
- Request deletion
- View their notifications and relevant history

### Department chief

- All normal employee capabilities
- Manage ordinary documents for their department
- Review department conflicts and assigned sensitive cases
- Grant editing rights to additional departments
- Approve deletion requests
- Restore department documents
- View department dashboards and department-scoped audit activity
- Resolve sensitive, duplicate, conflicting, or access-ambiguous cases for the department

### System administrator

- Create, update, deactivate, and transfer accounts
- Manage departments, roles, document types, metadata fields, scanner mappings, classification rules, retention, and processing settings
- Monitor and retry technical failures
- View system/security audit records
- Does not automatically receive access to confidential document contents

### Confidential authorization

Additional authorization such as `HR confidential`, `Accounting confidential`, or `Legal confidential` can be granted independently of a user's normal department role.
Only a user holding the matching active authorization may select or confirm a
confidential classification. The option is hidden from ordinary employees and the
same rule is enforced server-side. If processing later suspects that a normal scan
is confidential, publication stops and the document is routed to an appropriately
authorized review queue without exposing its content or metadata.

## 7. Authentication and scanner identity

### Platform authentication

- Local username or email plus password
- Secure password hashing
- Session expiration
- Login rate limiting and temporary lockout
- Administrator password reset
- Account activation and deactivation
- The permanent scanner code is not a platform password

### Scanner identification

The permanent code identifies who performed a scan. The real scanner must expose the code through at least one supported mechanism:

- employee-specific destination
- email subject or recipient
- scanner activity log
- accompanying metadata file
- API request
- configurable scan profile

Until confirmed, the prototype uses a scanner simulator that submits a PDF, employee code, scanner ID, and scan time.

## 8. Access model

### Sensitivity levels

1. `Personal`
2. `Department`
3. `Restricted`
4. `Confidential`
5. `Highly restricted`

There is no company-wide category visible automatically to all employees.

### Department assignment

- Every document has one primary department.
- A document may have zero or more additional departments.
- The primary department receives management rights.
- Additional departments receive view access by default.
- An authorized department chief may grant an additional department metadata-editing rights.

### Sharing

- Shares target an employee or department.
- Permissions are `View`, `Edit metadata`, or `Manage`.
- Shares may expire and may be revoked.
- Employees may share ordinary documents within allowed policy.
- Confidential and highly restricted documents require special sharing authorization.
- No external or anonymous links are supported.

### Confidential scan behavior

If an employee scans a confidential document but is not authorized to keep access:

1. The system records them permanently as the scanning employee.
2. Their content access is removed after sensitive classification.
3. They receive a neutral receipt confirming secure processing.
4. The receipt must not reveal the title, OCR text, or sensitive metadata.

### Employee departure

- Deactivate the account and active sessions.
- Revoke special confidential authorizations.
- Transfer current ownership to the primary department chief.
- Preserve the historical scanning employee.
- Review active shares.
- Never delete documents merely because an employee leaves.

## 9. Document lifecycle

### Processing status

`Waiting → Validating → Preprocessing → Running OCR → Classifying → Indexing → Completed`

Exceptional processing states:

- `Retrying`
- `Failed`
- `Quarantined`

### Business status

- `Provisional`
- `Needs employee review`
- `Needs authorized review`
- `Ready`
- `Pending deletion`
- `Recycle bin`
- `Permanently deleted`

Processing status and business status are separate fields.

### Ingestion workflow

1. Receive PDF plus source identity.
2. Wait until the file is complete and stable.
3. Claim the source event idempotently.
4. Validate actual PDF type, size, readability, encryption, and page count.
5. Scan for malware when ClamAV is available.
6. Calculate a cryptographic checksum.
7. Detect exact duplicates.
8. Preserve the original in protected storage.
9. Create a document record and show it as `Processing`.
10. Queue preprocessing, OCR, classification, and indexing.
11. Archive the source in a restricted processed area after success.
12. Retry transient failures; quarantine unsafe or unreadable files.

### Publication decision

- Reliable, ordinary, permitted: publish automatically as `Ready`.
- Uncertain but ordinary: `Needs employee review`.
- Sensitive, conflicting, or access-ambiguous: department-chief review.
- Technical failure: retain safely, retry, then notify administrator.
- Quarantined: no preview or content access for ordinary users.

Starting configurable thresholds:

- type confidence at least 90 for automatic acceptance
- primary department confidence at least 90 for automatic acceptance
- scores from 70 through 89 require employee confirmation
- score below 70, unknown template, sensitivity warning, or conflicting departments requires authorized review

Thresholds are initial values, not claims of statistical calibration.

## 10. OCR requirements

- Accept PDF only.
- Extract existing digital text before deciding whether OCR is required.
- Process text page by page.
- Support installed French, Arabic, and English OCR language packs.
- Apply orientation correction, deskewing, basic denoising, contrast improvement, and blank-page detection where appropriate.
- Produce a searchable PDF without modifying the original.
- Store extracted text, detected language, quality information, and page number.
- Record warnings for low-quality or handwritten pages.
- Typical 1–10 page printed documents should become searchable within 60 seconds under normal queue conditions.
- The document must appear as `Processing` within seconds even if OCR takes longer.
- Handwriting is best-effort and must not be presented as guaranteed.

## 11. Classification requirements

### Inputs

- scanning employee and their department
- scanner identity/location
- OCR text
- template recognition
- keyword and pattern rules
- known organizations and reference formats
- manual upload selections
- historical confirmed examples

### Outputs

- suggested title
- document type
- primary department
- additional departments
- sensitivity
- document date
- type-specific metadata
- separate confidence score and explanation for each suggestion

### Initial classifier

Use a hybrid of deterministic rules, standard-template recognition, source information, and an optional local text classifier trained only when enough labelled examples exist. Do not call rule-based scoring “machine learning.”

All human corrections must retain:

- original suggestion
- original confidence and reason
- confirmed/corrected value
- correcting actor
- correction time

## 12. Configurable document types

Initial examples:

- Invoice
- Contract
- Tax document
- Purchase order
- Delivery note
- Employee document
- Payslip
- Administrative letter
- Other

Administrators can add document types and fields without code changes. Supported field types include text, long text, number, money, date, employee, department, selection, and yes/no.

Example invoice fields:

- supplier
- invoice number
- invoice date
- due date
- subtotal
- tax
- total
- currency
- purchase-order number

## 13. Search requirements

Search across:

- title
- original filename
- internal reference
- OCR text by page
- digital PDF text
- document type
- assigned departments
- tags
- extracted metadata

Results must:

- be permission-filtered before presentation
- rank title and metadata matches above ordinary OCR matches
- show a highlighted excerpt
- show the matching page
- open the viewer at that page
- support filters for department, type, date, status, sensitivity, source, scanning employee, and language
- return no metadata or existence signal for unauthorized documents

PostgreSQL full-text search is sufficient for the prototype. Advanced Arabic morphology, fuzzy OCR matching, and OpenSearch are deferred.

## 14. User interface

Main navigation:

- Dashboard
- Documents
- Review
- Upload
- Notifications
- Administration, when authorized

### Employee dashboard

- processing count
- needs-review count
- ready-today count
- shared-with-me count
- recent scans and statuses
- action-required notifications
- quick upload and search

### Documents

Saved views:

- All accessible
- My scans
- My documents
- Department documents
- Shared with me
- Recently added
- Needs my attention
- Expiring soon
- Favorites

Default list columns:

- title/reference
- type
- departments
- document date
- status
- scanning employee

### Document viewer

- PDF.js preview with page navigation, zoom, rotation, and in-document search
- open directly on a matching page
- details, extracted text, access, history, and versions tabs
- actions shown only when authorized

### Review

- My confirmations
- Department review
- Sensitive review
- Processing problems, technical roles only

### Administration

- users and roles
- departments
- document types and metadata
- scanners and employee codes
- processing queue and failures
- classification rules and thresholds
- retention
- audit logs
- backup status

## 15. Versions and duplicates

- Replacing a PDF creates a new document version.
- Previous files remain recoverable according to retention policy.
- Metadata-only changes are recorded in audit history.
- Exact checksum matches and probable content duplicates are flagged.
- A user may compare and choose `Keep both`, `Discard new`, or `Create version` when authorized.
- The system must not automatically destroy a possible duplicate.

## 16. Notifications

Categories:

- action required
- processing
- access

Initial prototype notifications are in-platform. Messages must not leak content after access is removed.

## 17. Audit requirements

Audit at minimum:

- login attempts and logout
- scan detection and manual upload
- preview/view
- download
- metadata and classification changes
- permission and sharing changes
- review decisions
- deletion, restoration, and permanent purge
- version replacement
- account and role changes
- administrative and retry actions

Audit records are append-only through the application. Visibility is scoped by role.

## 18. Retention and deletion

- Retention rules are configurable by document type and sensitivity.
- A daily task identifies expired documents.
- Expired documents move to `Pending deletion`, then the recycle bin.
- A configurable recovery period precedes permanent deletion.
- Permanent deletion removes original, searchable derivative, previews, and versions according to policy.
- Minimal audit evidence may remain.
- Deletion is never a one-click immediate destructive action for ordinary employees.

## 19. Backup

- Daily database backup.
- Daily protected document-storage backup.
- Backup destination must be a separate disk or protected network location.
- Record backup success, size, time, and failure.
- Document a restoration procedure and periodically test it.

## 20. Dashboards

### Employee

- recent scans
- processing
- action required
- ready today
- shared with me
- expiring documents

### Department chief

- pending reviews
- sensitive cases
- deletion requests
- expiring documents
- volume by type and employee
- average processing time
- classification correction rate
- cross-department shares
- OCR failures

### Administrator

- queue health
- OCR success/failure
- average duration
- stuck jobs
- duplicates
- scanner activity
- storage usage
- failed login attempts
- backup status

Do not expose “most searched words.”

## 21. Free prototype architecture

- Python and Django
- Django templates, HTMX, and Tailwind CSS
- PostgreSQL
- Celery and Redis
- OCRmyPDF and Tesseract
- OpenCV
- PDF.js
- ClamAV when available
- protected local filesystem storage
- Docker Compose
- Nginx for production-style local deployment

Recommended Django modules:

- accounts
- organization
- documents
- ingestion
- ocr
- classification
- search
- access
- reviews
- notifications
- audit
- retention
- dashboards

## 22. Acceptance criteria

The prototype is acceptable when:

1. An administrator can create departments, users, roles, document types, metadata fields, scanners, and employee-code mappings.
2. A simulated scan appears for the correct employee without manual upload.
3. An incomplete source file is not imported prematurely.
4. Reprocessing the same source event does not create unintended duplicates.
5. The original PDF remains byte-for-byte unchanged.
6. A French, Arabic, or English printed sample produces page-level searchable text.
7. Searching a content word returns the permitted document with page and excerpt.
8. An unauthorized user receives neither the document nor its metadata in search.
9. A reliable ordinary document can become `Ready` automatically.
10. An uncertain normal document creates an employee review.
11. A sensitive document removes unauthorized scanning-employee access and creates an authorized review.
12. Primary and additional department access behaves as specified.
13. Manual upload uses the same OCR/classification pipeline.
14. A replacement creates a recoverable version.
15. A duplicate produces a reviewable warning.
16. Deletion uses the retention/recycle-bin path.
17. Important actions create audit records.
18. Failed processing retries safely and is visible to the administrator.
19. Daily backup jobs report success or failure.
20. Core automated tests pass and setup documentation can reproduce the prototype.
