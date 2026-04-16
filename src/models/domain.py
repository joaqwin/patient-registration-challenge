"""Pydantic schemas for request input and API responses."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PatientCreate(BaseModel):
    """Input schema. Format and uniqueness validation is handled by the validator classes."""

    name: str = Field(..., min_length=2)
    email: str
    phone: str


class PatientSummary(BaseModel):
    """Minimal API response schema for patient list — omits sensitive fields."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    created_at: datetime


class PatientDetail(BaseModel):
    """Full API response schema for a single patient record — includes all fields."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    phone: str
    document_photo: str
    created_at: datetime
