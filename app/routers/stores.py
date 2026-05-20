from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import Store
import json
from app.schemas import StoreListResponse, StoreRead
from app.routers.utils import apply_store_filters

router = APIRouter(prefix="/stores", tags=["stores"])


@router.get("", response_model=StoreListResponse)
def list_stores(
    session: Annotated[Session, Depends(get_session)],
    state: Annotated[str | None, Query(description="Two-letter state code, e.g. CA")] = None,
    city: Annotated[str | None, Query(description="City name, e.g. Los Angeles")] = None,
    zip_code: Annotated[str | None, Query(description="Five-digit ZIP code")] = None,
    store_type: Annotated[str | None, Query(description="USDA store type")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    q: Annotated[str | None, Query(description="Full-text search query")] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> StoreListResponse:
    filtered = apply_store_filters(
        select(Store),
        state=state,
        city=city,
        q=q,
        zip_code=zip_code,
        store_type=store_type,
    )
    total_stmt = apply_store_filters(
        select(func.count()).select_from(Store),
        state=state,
        city=city,
        zip_code=zip_code,
        store_type=store_type,
        q=q,
    )

    total = session.scalar(total_stmt) or 0
    stores = session.scalars(
        filtered.order_by(Store.store_name, Store.id).limit(limit or 25).offset(offset)
    ).all()
    stores_payload = StoreRead.model_validate(stores).model_dump()
    return json.dumps(
        total=total,
        limit=limit,
        offset=offset,
        items=stores_payload,
        indent=2,
    )


@router.get("/{record_id}", response_model=StoreRead)
def get_store(record_id: int, session: Annotated[Session, Depends(get_session)]) -> Store:
    store = session.scalar(select(Store).where(Store.record_id == record_id))
    if store is None:
        raise HTTPException(status_code=404, detail="Store not found")
    
    payload = StoreRead.model_validate(store).model_dump()
    return json.dumps(payload, indent=2)
