import pytest
from httpx import AsyncClient

VALID_FORM = {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+14155552671",
}
VALID_FILE = {"document_photo": ("photo.jpg", b"fake-image-data", "image/jpeg")}


async def test_post_patient_success(client: AsyncClient) -> None:
    response = await client.post("/patients", data=VALID_FORM, files=VALID_FILE)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == VALID_FORM["name"]
    assert body["email"] == VALID_FORM["email"]
    assert body["phone"] == VALID_FORM["phone"]
    assert "id" in body
    assert "created_at" in body
    assert body["document_photo"] is not None


async def test_post_patient_duplicate_email(client: AsyncClient) -> None:
    await client.post("/patients", data=VALID_FORM, files=VALID_FILE)

    response = await client.post("/patients", data=VALID_FORM, files=VALID_FILE)

    assert response.status_code == 400


async def test_post_patient_missing_fields(client: AsyncClient) -> None:
    response = await client.post(
        "/patients",
        data={"name": "John Doe"},
        files=VALID_FILE,
    )

    assert response.status_code == 422


async def test_post_patient_invalid_email(client: AsyncClient) -> None:
    response = await client.post(
        "/patients",
        data={**VALID_FORM, "email": "not-an-email"},
        files=VALID_FILE,
    )

    assert response.status_code == 422
