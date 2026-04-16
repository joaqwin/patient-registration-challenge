# Patient Registration API — Project Documentation

## Table of Contents

1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [Endpoints](#endpoints)
4. [Database Table](#database-table)
5. [Alembic Migrations](#alembic-migrations)
6. [Validators](#validators)
7. [Logging](#logging)
8. [Notifications & Observer Pattern](#notifications--observer-pattern)
9. [Email — Mailtrap Sandbox](#email--mailtrap-sandbox)
10. [Tests](#tests)
11. [Scalability Considerations](#scalability-considerations)
12. [HIPAA Compliance](#hipaa-compliance)

---

## Project Overview

A RESTful API built with **FastAPI** and **PostgreSQL** that allows registering patients with their
name, email address, phone number, and a document photo. Each successful registration triggers
a background email notification. The notification system is designed so that additional channels
(e.g. SMS, push) can be added with minimal effort — see [Notifications & Observer Pattern](#notifications--observer-pattern).

---

## Project Structure

```
.
├── alembic/                    # Migration scripts and Alembic env
│   ├── env.py
│   └── versions/
│       ├── 0001_create_patients_table.py
│       └── 0002_add_unique_index_on_phone.py
├── docs/
│   └── project.md              # This file
├── scripts/
│   └── init-test-db.sh         # Creates patients_test_db on first Postgres startup
├── src/
│   ├── api/
│   │   └── routes/
│   │       └── patients.py     # FastAPI router — HTTP boundary
│   ├── core/
│   │   ├── config.py           # Pydantic-settings (reads .env)
│   │   └── dependencies.py     # FastAPI dependency providers (session, notifiers)
│   ├── models/
│   │   ├── db.py               # SQLAlchemy ORM model (Patient table)
│   │   └── domain.py           # Pydantic schemas (PatientCreate, PatientResponse)
│   ├── notifiers/
│   │   ├── base.py             # Abstract BaseNotifier (Observer interface)
│   │   └── email_notifier.py   # Sends confirmation email via Mailtrap SMTP
│   ├── repositories/
│   │   └── patient_repository.py  # All database queries (create, get_by_id, etc.)
│   ├── services/
│   │   └── patient_service.py  # Business logic — orchestrates validators, repo, notifiers
│   ├── tests/
│   │   ├── conftest.py         # Shared fixtures (test engine, client, migrations)
│   │   ├── integration/
│   │   │   ├── conftest.py     # DB cleanup between tests
│   │   │   └── test_patient_routes.py
│   │   └── unit/
│   │       ├── test_patient_service.py
│   │       └── test_notifiers.py
│   └── validators/
│       ├── email_validator.py
│       ├── name_validator.py
│       ├── phone_validator.py
│       └── photo_validator.py
├── main.py                     # FastAPI app entry point
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/patients` | Register a new patient (`multipart/form-data`) |
| `GET` | `/patients` | List all patients, ordered by registration date (newest first) |
| `GET` | `/patients/{id}` | Retrieve a single patient by UUID |
| `GET` | `/health` | Health check — returns `{"status": "ok"}` |

Interactive Swagger docs are available at `http://localhost:8000/docs` when the server is running.

### POST /patients — request fields

| Field | Type | Rules |
|-------|------|-------|
| `name` | `string` (form) | Min 2, max 100 chars; letters, spaces, hyphens, apostrophes only |
| `email` | `string` (form) | Valid format; must be unique across all patients |
| `phone` | `string` (form) | `+1` followed by exactly 10 digits (NANP); must be unique |
| `document_photo` | `file` | `.jpg`, `.jpeg`, `.png`, or `.webp`; validated by extension and `Content-Type` |

A successful registration returns `HTTP 201` with the full `PatientResponse` JSON body.

---

## Database Table

The single table `patients` is defined in `src/models/db.py` as a SQLAlchemy ORM model:

```
patients
├── id             UUID        PRIMARY KEY  (generated with uuid4)
├── name           VARCHAR     NOT NULL
├── email          VARCHAR     NOT NULL  UNIQUE  INDEX
├── phone          VARCHAR     NOT NULL  UNIQUE  INDEX
├── document_photo VARCHAR     NOT NULL  (relative path to the saved file)
└── created_at     TIMESTAMPTZ NOT NULL  DEFAULT now()
```

- `email` and `phone` both carry a unique constraint and a database-level index so that
  uniqueness is enforced at the storage layer and lookups are fast.
- `created_at` is set server-side (`DEFAULT now()`) so the timestamp always reflects the
  database server clock regardless of what the application passes.
- `document_photo` stores the relative path to the uploaded file (e.g. `uploads/<uuid>.jpg`).
  At the moment files are stored on the local filesystem inside the `uploads/` directory which
  is mounted as a Docker volume. See [Scalability Considerations](#scalability-considerations)
  for how this should change before production.

---

## Alembic Migrations

### Why Alembic?

SQLAlchemy alone can create tables with `Base.metadata.create_all()`, but that approach has
serious limitations in a real project:

- **No history** — there is no record of what changed, when, or why.
- **No rollback** — you cannot undo a schema change if something goes wrong.
- **No incremental changes** — adding a column or index to an existing table requires manual SQL
  or destructive operations.
- **No team coordination** — two developers changing the schema simultaneously will produce
  conflicts with no structured resolution.

Alembic solves all of this by treating database schema changes the same way Git treats code:
each change is a versioned, reviewable, revertable migration script.

### Benefits

| Feature | What it means for this project |
|---------|-------------------------------|
| **Versioned history** | Every schema change is a numbered file in `alembic/versions/`. |
| **Auto-generation** | `alembic revision --autogenerate` compares the ORM model against the live DB and generates the SQL for you. |
| **Up / down migrations** | Every migration has an `upgrade()` and a `downgrade()` function so you can roll back safely. |
| **Async support** | `alembic/env.py` is wired up with `run_async_migrations` so it runs on the same async engine as the application. |
| **CI / Docker integration** | The `Dockerfile` runs `alembic upgrade head` before starting the server, so the DB schema is always up to date on deploy. |

### Migrations in this project

| File | What it does |
|------|-------------|
| `0001_create_patients_table.py` | Creates the `patients` table with all columns. |
| `0002_add_unique_index_on_phone.py` | Adds a unique index on the `phone` column (added after the initial table was created). |

### Common commands

```bash
# Apply all pending migrations
alembic upgrade head

# Roll back the last migration
alembic downgrade -1

# Generate a new migration after changing a model
alembic revision --autogenerate -m "describe your change"

# Show current migration state
alembic current
```

---

## Validators

All input validation logic lives in `src/validators/`. Each validator is a small class with a
single public `validate()` method that raises `HTTPException` on failure. Keeping validation
separate from the service and the route means:

- Rules are easy to find, read, and change in isolation.
- They can be unit-tested without spinning up the full service.
- New validators can be added without touching existing code.

### NameValidator (`name_validator.py`)

Checks performed in order:

1. **Minimum length** — at least 2 characters.
2. **Maximum length** — at most 100 characters.
3. **No digits** — numbers are rejected (a name like `John2` is invalid).
4. **Valid characters** — only Unicode letters, spaces, hyphens (`-`), and apostrophes (`'`)
   are allowed. This supports names like `O'Brien` or `Mary-Jane` while rejecting symbols
   such as `_`, `+`, `*`, `()`, etc.

### EmailValidator (`email_validator.py`)

Checks performed in order:

1. **Format** — validated against a simplified RFC 5322 regex (`user@domain.tld`).
2. **Uniqueness** — queries the database; raises `HTTP 409 Conflict` if the email is already
   registered.

### PhoneValidator (`phone_validator.py`)

Checks performed in order:

1. **Format** — must match `+1` followed by exactly 10 digits (North American Numbering Plan,
   e.g. `+14155552671`). No spaces or dashes are accepted.
2. **Uniqueness** — queries the database; raises `HTTP 409 Conflict` if the number is already
   registered.

### PhotoValidator (`photo_validator.py`)

Checks performed in order:

1. **File extension** — must be one of `.jpg`, `.jpeg`, `.png`, `.webp`.
2. **Content-Type** — the MIME type reported by the client must be one of `image/jpeg`,
   `image/png`, `image/webp`.

Both checks are required because a malicious client could rename a file to bypass the extension
check alone.

---

## Logging

The project uses Python's standard `logging` module. Every module obtains its own logger with:

```python
logger = logging.getLogger(__name__)
```

This means log records carry the exact module path (e.g. `src.services.patient_service`) so you
can filter by component in any log aggregator.

### What is logged

| Level | Where | Examples |
|-------|-------|---------|
| `INFO` | Service layer | "Validating email for new patient", "Patient registered successfully: id=… email=…" |
| `INFO` | Validators | "Checking email format", "Checking phone uniqueness" |
| `INFO` | Routes | "POST /patients - registering patient with email=…" |
| `INFO` | Notifiers | "Confirmation email sent to …" |
| `WARNING` | Validators | "Invalid email format", "Email already registered" |
| `WARNING` | Service | "Patient not found: id=…" |
| `ERROR` / `EXCEPTION` | Notifiers | "Failed to send confirmation email to …" |

Log level and format are configured at startup via `logging.basicConfig`. In production these
should be routed to a structured log sink (e.g. CloudWatch, Datadog, or a JSON formatter).

---

## Notifications & Observer Pattern

### Design

The notification system follows the **Observer pattern**:

- `BaseNotifier` (`src/notifiers/base.py`) is the abstract *observer* interface. It declares one
  method: `async def notify(patient: PatientResponse) -> None`.
- `PatientService` is the *subject*. It holds a list of `BaseNotifier` instances injected at
  construction time via `get_notifiers()` in `src/core/dependencies.py`.
- After a patient is successfully persisted, the service iterates over its notifiers and schedules
  each one as a FastAPI `BackgroundTask`, so the HTTP response is returned immediately without
  waiting for notifications to complete.

```
PatientService
  └── notifiers: list[BaseNotifier]
        └── EmailNotifier   ← currently active
```

### Adding a new notification channel

1. Create `src/notifiers/my_notifier.py`, subclass `BaseNotifier`, implement `notify()`.
2. Add an instance to the list returned by `get_notifiers()` in `src/core/dependencies.py`.
3. That is all — no changes required in the service or the route.

### Adding SMS notifications

SMS is not implemented yet, but the architecture makes it straightforward to add:

1. Create `src/notifiers/sms_notifier.py`, subclass `BaseNotifier`, and implement `notify()`
   using a provider of your choice (e.g. Twilio, AWS SNS, Vonage).
2. Add the required credentials to `Settings` in `src/core/config.py` and to `.env`
   (e.g. `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`).
3. Install the provider SDK and add it to `requirements.txt`.
4. Add `SmsNotifier()` to the list returned by `get_notifiers()` in `src/core/dependencies.py`.

Because the service only knows about `BaseNotifier`, this change is completely isolated — nothing
else in the codebase needs to be touched.

---

## Email — Mailtrap Sandbox

The email notifier sends messages via **SMTP with STARTTLS** using the `aiosmtplib` library.
In development and testing the project is configured to use **Mailtrap**, which is an email
sandbox service.

**Mailtrap does not deliver emails to real inboxes.** Instead it captures outgoing SMTP traffic
and displays the messages inside a web dashboard at `https://mailtrap.io`. This means:

- No real users receive test emails during development.
- You can verify the email content, headers, and SMTP handshake from the Mailtrap inbox
  dashboard — confirming that the notification pipeline works end-to-end.
- The credentials (`MAILTRAP_HOST`, `MAILTRAP_PORT`, `MAILTRAP_USER`, `MAILTRAP_PASS`) come
  from your Mailtrap project's SMTP settings and are stored in `.env`.

To use a real email provider in production, update the four `MAILTRAP_*` variables in `.env`
with the SMTP credentials of your chosen provider (SendGrid, AWS SES, Postmark, etc.) — no
code changes are needed.

---

## Tests

The test suite is split into two layers:

### Unit tests (`src/tests/unit/`)

Unit tests run in memory with no database or network access. All external dependencies are
replaced with `unittest.mock` mocks or `AsyncMock` objects.

| File | What it tests |
|------|--------------|
| `test_patient_service.py` | `PatientService` — happy path registration, duplicate-email rejection (409), patient-not-found (404). |
| `test_notifiers.py` | `EmailNotifier` — verifies `aiosmtplib.send` is called with the correct SMTP credentials. |

### Integration tests (`src/tests/integration/`)

Integration tests run against a real PostgreSQL database (`patients_test_db`). The full HTTP
stack is exercised via `httpx.AsyncClient` with `ASGITransport`, so FastAPI routing, dependency
injection, validators, the service, and the repository all run as they would in production.

| File | What it tests |
|------|--------------|
| `test_patient_routes.py` | `POST /patients` — success (201), duplicate email (409), missing fields (422), invalid email format (422). |

### Fixtures and infrastructure

- **`src/tests/conftest.py`** — creates a separate async SQLAlchemy engine pointing at
  `patients_test_db`, provides the `client` fixture, and exposes the `apply_migrations` fixture
  that runs `alembic upgrade head` once per test session.
- **`src/tests/integration/conftest.py`** — pulls in `apply_migrations` (session-scoped,
  autouse) and provides `clean_patients` (function-scoped, autouse) which `DELETE`s all rows
  after every test so tests are fully isolated.
- **`NullPool`** — the test engine uses `NullPool` so SQLAlchemy never reuses connections across
  pytest-asyncio's function-scoped event loops, which would cause `InterfaceError`.

### Running the tests

```bash
# All tests (from project root, with Postgres running)
pytest

# Unit tests only (no database required)
pytest src/tests/unit

# Integration tests only
pytest src/tests/integration

# With verbose output
pytest -v
```

---

## Scalability Considerations

### File storage

At the moment uploaded document photos are written to a local `uploads/` directory that is
mounted as a Docker named volume. This works for a single-container deployment but **will not
scale** once you run more than one application instance, because each instance has its own
filesystem and files written by one container are not visible to others.

**Before deploying to a multi-instance or cloud environment, replace local file storage with an
object storage service:**

| Cloud | Service | Notes |
|-------|---------|-------|
| AWS | S3 | Use `boto3` / `aiobotocore`; generate pre-signed URLs for secure access. |
| GCP | Cloud Storage | Use `google-cloud-storage`; supports signed URLs. |
| Azure | Blob Storage | Use `azure-storage-blob`. |
| Self-hosted | MinIO | S3-compatible, easy to run in Docker. |

The change is isolated to `PatientService._save_upload()`. Replace the `aiofiles.open` block
with an async upload call to the chosen SDK, and store the returned object key / URL in the
`document_photo` column instead of the local path.

### Database

- Add a **connection pooler** (PgBouncer or RDS Proxy) in front of PostgreSQL when the number of
  application instances grows, to avoid exhausting Postgres connection limits.
- Consider **read replicas** for the list/get endpoints if read traffic becomes a bottleneck.

### Notifications

Because notifications are dispatched as FastAPI `BackgroundTask`s they run in the same process.
For high-throughput scenarios, push them onto a proper task queue (Celery + Redis, AWS SQS,
etc.) so the web workers are not blocked and failed notifications can be retried.

### Configuration

All secrets and environment-specific values are already in `.env` / `pydantic-settings`, so
migrating to a secrets manager (AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault) only
requires changing where the `.env` values come from — no code changes needed.

---

## HIPAA Compliance

This API handles Protected Health Information (PHI): patient names, email addresses, phone
numbers, and document photos. As such, it is subject to HIPAA's Technical Safeguard requirements,
which mandate controls over how PHI is accessed, transmitted, and stored.

Five technical safeguards were identified and implemented on a separate branch:

1. **Encryption at rest** — document photos are encrypted with Fernet (symmetric encryption from
   the `cryptography` library) before being written to disk, so raw files are never stored in
   plaintext.
2. **Encryption in transit** — all traffic should be routed through an nginx reverse proxy
   configured with TLS, ensuring PHI is never sent over an unencrypted connection.
3. **Audit logging** — every PHI access (POST and GET requests) is recorded in an `audit_logs`
   database table, capturing the action, resource ID, IP address, and timestamp.
4. **Data minimization** — response schemas are scoped by endpoint: `PatientSummary` (name and
   email only) for `GET /patients`, and `PatientDetail` (full record) for `GET /patients/{id}`,
   limiting exposure of sensitive fields.
5. **Secret management** — the `ENCRYPTION_KEY` is managed as an environment variable via
   `pydantic-settings`, keeping cryptographic material out of the codebase.

These changes are implemented on the `feature/hipaa-compliance` branch. Due to time constraints,
the branch has not been fully tested and **should not be merged to main** until proper test
coverage is in place.

Before merging, the following should be verified: that files are correctly encrypted on upload
and can be decrypted on retrieval, that an audit log entry is written for every PHI request, and
that all existing integration tests continue to pass with the new schema split and the
`ENCRYPTION_KEY` variable present in the test environment.
