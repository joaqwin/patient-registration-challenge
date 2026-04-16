"""FastAPI router for patient registration and retrieval endpoints."""

import logging
import uuid
from dataclasses import dataclass

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_notifiers, get_session
from src.models.domain import PatientDetail, PatientSummary
from src.notifiers.base import BaseNotifier
from src.repositories.audit_repository import AuditRepository
from src.repositories.patient_repository import PatientRepository
from src.services.patient_service import PatientService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients", tags=["patients"])


@dataclass(slots=True)
class PatientCreatePayload:
    """Validated form data required to register a patient."""

    name: str
    email: str
    phone: str
    document_photo: UploadFile


async def get_patient_create_payload(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    document_photo: UploadFile = File(...),
) -> PatientCreatePayload:
    """Collect multipart form data into a single dependency object."""
    return PatientCreatePayload(
        name=name,
        email=email,
        phone=phone,
        document_photo=document_photo,
    )


def get_patient_service(
    notifiers: list[BaseNotifier] = Depends(get_notifiers),
) -> PatientService:
    """Build the patient service with repository and notifier dependencies."""
    return PatientService(repo=PatientRepository(), notifiers=notifiers)


@router.post("", response_model=PatientDetail, status_code=status.HTTP_201_CREATED)
async def create_patient(
    request: Request,
    background_tasks: BackgroundTasks,
    payload: PatientCreatePayload = Depends(get_patient_create_payload),
    session: AsyncSession = Depends(get_session),
    service: PatientService = Depends(get_patient_service),
) -> PatientDetail:
    """Register a new patient and return the full patient record."""
    logger.info("POST /patients - registering patient with email=%s", payload.email)

    result = await service.register(
        session,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        file=payload.document_photo,
        background_tasks=background_tasks,
    )

    audit_repo = AuditRepository()
    await audit_repo.create(
        session,
        action="CREATE",
        resource_id=result.id,
        ip_address=request.client.host if request.client else "unknown",
    )

    return result


@router.get("", response_model=list[PatientSummary])
async def list_patients(
    request: Request,
    session: AsyncSession = Depends(get_session),
    service: PatientService = Depends(get_patient_service),
) -> list[PatientSummary]:
    """Return a summary list of all patients (no phone or document_photo)."""
    logger.info("GET /patients - fetching all patients")
    results = await service.get_all(session)

    audit_repo = AuditRepository()
    for patient in results:
        await audit_repo.create(
            session,
            action="READ",
            resource_id=patient.id,
            ip_address=request.client.host if request.client else "unknown",
        )

    return results


@router.get("/{patient_id}", response_model=PatientDetail)
async def get_patient(
    patient_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    service: PatientService = Depends(get_patient_service),
) -> PatientDetail:
    """Return the full detail record for a single patient."""
    logger.info("GET /patients/%s - fetching patient", patient_id)
    result = await service.get_by_id(session, patient_id=patient_id)

    audit_repo = AuditRepository()
    await audit_repo.create(
        session,
        action="READ",
        resource_id=result.id,
        ip_address=request.client.host if request.client else "unknown",
    )

    return result
