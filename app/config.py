import os
from dataclasses import dataclass

from dotenv import load_dotenv
from sqlalchemy.engine import URL, make_url

load_dotenv()


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def apply_database_password_override(database_url: str, password: str | None) -> str:
    if not password:
        return database_url

    url = make_url(database_url)
    query = dict(url.query)
    updated_url = URL.create(
        drivername=url.drivername,
        username=url.username,
        password=password,
        host=url.host,
        port=url.port,
        database=url.database,
        query=query,
    )
    return updated_url.render_as_string(hide_password=False)


@dataclass(frozen=True)
class Settings:
    database_url: str
    app_name: str = "EBT Store API"
    app_version: str = "0.1.0"


def get_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")
    database_url = normalize_database_url(database_url)
    database_url = apply_database_password_override(
        database_url,
        os.getenv("DATABASE_PASSWORD"),
    )
    return Settings(database_url=database_url)
