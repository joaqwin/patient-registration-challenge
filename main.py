from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from src.api.routes.patients import router as patients_router

UPLOAD_DIR = Path("uploads")


@asynccontextmanager
async def lifespan(app: FastAPI):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Patient Registration API", lifespan=lifespan)
app.include_router(patients_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
