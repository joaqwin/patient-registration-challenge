# Patient Registration API

FastAPI + PostgreSQL service for registering patients with document photo upload.

## Requirements

- Docker & Docker Compose

## Running with Docker

```bash
cp .env.example .env
docker-compose up --build
```

The API will be available at `http://localhost:8000`.  
Migrations run automatically before the server starts.

## Applying migrations manually

```bash
# inside the container
docker-compose exec app alembic upgrade head

# or locally (requires a running Postgres and a valid .env)
alembic upgrade head
```

To create a new migration after changing a model:

```bash
alembic revision --autogenerate -m "describe your change"
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/patients` | Register a new patient (multipart/form-data) |
| `GET` | `/patients` | List all patients |
| `GET` | `/patients/{id}` | Get a patient by UUID |
| `GET` | `/health` | Health check |

Interactive docs: `http://localhost:8000/docs`
