import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

E164_PHONE = re.compile(r"^\+[1-9]\d{1,14}$")


class PatientCreate(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    phone: str

    @field_validator("phone")
    @classmethod
    def _validate_phone(cls, v: str) -> str:
        if not E164_PHONE.match(v):
            raise ValueError("phone must be in E.164 format, e.g. +14155552671")
        return v


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    phone: str
    document_photo: str
    created_at: datetime
