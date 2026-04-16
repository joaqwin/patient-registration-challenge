# Patient Registration API

FastAPI + PostgreSQL service for registering patients with document photo upload.

## Tech stack

| Component | Version |
|-----------|---------|
| Python | 3.12 |
| FastAPI | >= 0.115 |
| PostgreSQL | 16 |
| pylint | >= 3.0 |

For the full list see `requirements.txt`.

---

## Requirements

- Docker & Docker Compose

---

## Environment setup

Copy the template below into a `.env` file at the project root and fill in your values:

```env
DATABASE_URL=postgresql+asyncpg://patients_user:patients_pass@postgres:5432/patients_db
TEST_DATABASE_URL=postgresql+asyncpg://patients_user:patients_pass@postgres:5432/patients_test_db
APP_ENV=development

MAILTRAP_HOST=sandbox.smtp.mailtrap.io
MAILTRAP_PORT=2525
MAILTRAP_USER=your_mailtrap_username
MAILTRAP_PASS=your_mailtrap_password
```

### Getting Mailtrap credentials

The API uses [Mailtrap](https://mailtrap.io) as an email sandbox — sent emails are captured in
a web dashboard instead of being delivered to real inboxes, which is safe for development.

1. Go to [mailtrap.io](https://mailtrap.io) and log in.
2. Go to your sandbox (or create one).
3. Get your credentials and copy them into your `.env`.

---

## Running with Docker

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`.
Migrations run automatically before the server starts.

Interactive docs: `http://localhost:8000/docs`

---

## Running tests

Tests require a separate `patients_test_db` database. When using Docker Compose the
database is created automatically on first startup via `scripts/init-test-db.sh`.
If you are running Postgres locally, create it once:

```bash
psql -U patients_user -c "CREATE DATABASE patients_test_db;"
```

Install dependencies and run the full suite from the project root:

```bash
pip install -r requirements.txt
pytest
```

Run only unit or integration tests:

```bash
pytest src/tests/unit
pytest src/tests/integration
```

The `TEST_DATABASE_URL` in `.env` points to `localhost` by default, so run pytest
from your host machine (not inside the container) while the Postgres container is up.

---

## Running the linter

```bash
pylint src
```

To lint a single file:

```bash
pylint src/services/patient_service.py
```

---

## Alembic migrations

Migrations run automatically on container startup. To manage them manually:

```bash
# Apply all pending migrations (inside the container)
docker-compose exec app alembic upgrade head

# Or locally (requires a running Postgres and a valid .env)
alembic upgrade head

# Roll back the last migration
alembic downgrade -1

# Generate a new migration after changing a model
alembic revision --autogenerate -m "describe your change"

# Show current migration state
alembic current
```

---

## Documentation

See [`docs/project.md`](docs/project.md) for a full explanation of the project structure,
database schema, validators, logging, notification system (Observer pattern), Mailtrap sandbox
setup, tests, and scalability considerations.
