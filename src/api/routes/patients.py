import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_session
from src.models.domain import PatientCreate, PatientResponse
from src.repositories.patient_repository import PatientRepository
from src.services.patient_service import PatientService

router = APIRouter(prefix="/patients", tags=["patients"])


def get_patient_service() -> PatientService:
    return PatientService(repo=PatientRepository(), notifiers=[])


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    name: str = Form(..., min_length=2),
    email: str = Form(...),
    phone: str = Form(...),
    document_photo: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    service: PatientService = Depends(get_patient_service),
) -> PatientResponse:
    payload = PatientCreate(name=name, email=email, phone=phone)
    return await service.register(
        session,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        file=document_photo,
    )


@router.get("", response_model=list[PatientResponse])
async def list_patients(
    session: AsyncSession = Depends(get_session),
    service: PatientService = Depends(get_patient_service),
) -> list[PatientResponse]:
    return await service.get_all(session)


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    service: PatientService = Depends(get_patient_service),
) -> PatientResponse:
    return await service.get_by_id(session, patient_id)
