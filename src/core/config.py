from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    APP_ENV: Literal["development", "production"] = "development"

    MAILTRAP_HOST: str
    MAILTRAP_PORT: int
    MAILTRAP_USER: str
    MAILTRAP_PASS: str


settings = Settings()
