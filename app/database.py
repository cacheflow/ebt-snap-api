from functools import lru_cache
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from app.config import get_settings


def get_ssl_connect_args() -> dict[str, str | None]:
    settings = get_settings()
    url = make_url(settings.database_url)
    sslmode = url.query.get("sslmode")
    sslrootcert = url.query.get("sslrootcert")

    if not (url.host and url.host.endswith(".pooler.supabase.com")):
        return {}

    ssl_args = {"sslmode": sslmode or "require"}
    if sslrootcert:
        ssl_args["sslrootcert"] = sslrootcert
    return ssl_args


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    engine_options = {"pool_pre_ping": True}

    engine_options["poolclass"] = NullPool
    engine_options["connect_args"] = {
        "prepare_threshold": None,
        **get_ssl_connect_args(),
    }

    return create_engine(settings.database_url, **engine_options)


def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session
