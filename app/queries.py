"""Store queries shared by the HTTP routes and the MCP tools."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session
import json
from app.models import Store
from app.routers.utils import apply_store_filters
from app.schemas import StoreListResponse

RMP_STORE_TYPE = "rmp"


def search_stores(
    session: Session,
    *,
    state: str | None = None,
    city: str | None = None,
    zip_code: str | None = None,
    store_type: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> StoreListResponse:
    filters = dict(
        state=state, city=city, zip_code=zip_code, store_type=store_type, q=q
    )
    total = (
        session.scalar(
            apply_store_filters(select(func.count()).select_from(Store), **filters)
        )
        or 0
    )
    stores = session.scalars(
        apply_store_filters(select(Store), **filters)
        .order_by(Store.store_name, Store.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return StoreListResponse(total=total, limit=limit, offset=offset, items=stores)


def get_store(
    session: Session, record_id: int, *, store_type: str | None = None
) -> Store | None:
    stmt = select(Store).where(Store.record_id == record_id)
    if store_type is not None:
        stmt = stmt.where(Store.store_type == store_type)
    return session.scalar(stmt)
