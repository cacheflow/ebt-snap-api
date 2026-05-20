import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


@dataclass(frozen=True)
class Settings:
    database_url: str
    app_name: str = "EBT Store API"
    app_version: str = "0.1.0"


def get_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")
    return Settings(database_url=normalize_database_url(database_url))
