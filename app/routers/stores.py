from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import queries
from app.database import get_session
from app.models import Store
from app.schemas import StoreListResponse, StoreRead

router = APIRouter(prefix="/stores", tags=["stores"])


@router.get("", response_model=StoreListResponse, operation_id="list_stores")
def list_stores(
    session: Annotated[Session, Depends(get_session)],
    state: Annotated[
        str | None, Query(description="Two-letter state code, e.g. CA")
    ] = None,
    city: Annotated[
        str | None, Query(description="City name, e.g. Los Angeles")
    ] = None,
    zip_code: Annotated[str | None, Query(description="Five-digit ZIP code")] = None,
    store_type: Annotated[str | None, Query(description="USDA store type")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    q: Annotated[str | None, Query(description="Full-text search query")] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> StoreListResponse:
    """Search USDA EBT/SNAP-authorized retailers. Filters combine with AND;
    `q` matches name, address, city, state, ZIP, county, or store type.
    Results are paginated; use `total` with `limit`/`offset` to page."""
    return queries.search_stores(
        session,
        state=state,
        city=city,
        zip_code=zip_code,
        store_type=store_type,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.get("/{record_id}", response_model=StoreRead, operation_id="get_store")
def get_store(
    record_id: int, session: Annotated[Session, Depends(get_session)]
) -> Store:
    """Get one EBT-authorized retailer by its USDA record_id."""
    store = queries.get_store(session, record_id)
    if store is None:
        raise HTTPException(status_code=404, detail="Store not found")
    return store
