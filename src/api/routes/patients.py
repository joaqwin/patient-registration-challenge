"""HTTP routes for patient registration and retrieval."""

import logging
import uuid
from dataclasses import dataclass

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_notifiers, get_session
from src.notifiers.base import BaseNotifier
from src.repositories.patient_repository import PatientRepository
from src.services.patient_service import PatientService
from src.models.domain import PatientResponse

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


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    background_tasks: BackgroundTasks,
    payload: PatientCreatePayload = Depends(get_patient_create_payload),
    session: AsyncSession = Depends(get_session),
    service: PatientService = Depends(get_patient_service),
) -> PatientResponse:
    """Register a new patient and schedule notifications."""
    logger.info("POST /patients - registering patient with email=%s", payload.email)

    return await service.register(
        session,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        file=payload.document_photo,
        background_tasks=background_tasks,
    )


@router.get("", response_model=list[PatientResponse])
async def list_patients(
    session: AsyncSession = Depends(get_session),
    service: PatientService = Depends(get_patient_service),
) -> list[PatientResponse]:
    """Return all registered patients."""
    logger.info("GET /patients - fetching all patients")
    return await service.get_all(session)


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    service: PatientService = Depends(get_patient_service),
) -> PatientResponse:
    """Return a single patient by UUID."""
    logger.info("GET /patients/%s - fetching patient", patient_id)
    return await service.get_by_id(session, patient_id=patient_id)
