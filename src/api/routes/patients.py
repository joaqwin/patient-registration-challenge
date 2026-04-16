import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_notifiers, get_session
from src.models.domain import PatientResponse

logger = logging.getLogger(__name__)
from src.notifiers.base import BaseNotifier
from src.repositories.patient_repository import PatientRepository
from src.services.patient_service import PatientService

router = APIRouter(prefix="/patients", tags=["patients"])


def get_patient_service(
    notifiers: list[BaseNotifier] = Depends(get_notifiers),
) -> PatientService:
    return PatientService(repo=PatientRepository(), notifiers=notifiers)


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    document_photo: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    service: PatientService = Depends(get_patient_service),
) -> PatientResponse:
    logger.info("POST /patients - registering patient with email=%s", email)

    return await service.register(
        session,
        name=name,
        email=email,
        phone=phone,
        file=document_photo,
        background_tasks=background_tasks,
    )


@router.get("", response_model=list[PatientResponse])
async def list_patients(
    session: AsyncSession = Depends(get_session),
    service: PatientService = Depends(get_patient_service),
) -> list[PatientResponse]:
    logger.info("GET /patients - fetching all patients")
    return await service.get_all(session)


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    service: PatientService = Depends(get_patient_service),
) -> PatientResponse:
    logger.info("GET /patients/%s - fetching patient", patient_id)
    return await service.get_by_id(session, patient_id)
