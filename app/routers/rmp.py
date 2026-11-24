from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import queries
from app.database import get_session
from app.models import Store
from app.schemas import StoreListResponse, StoreRead

router = APIRouter(prefix="/rmp", tags=["rmp"])


@router.get(
    "", response_model=StoreListResponse, operation_id="list_rmp_restaurants"
)
def list_rmp_restaurants(
    session: Annotated[Session, Depends(get_session)],
    state: Annotated[
        str | None, Query(description="Two-letter state code, e.g. CA")
    ] = None,
    city: Annotated[
        str | None, Query(description="City name, e.g. Los Angeles")
    ] = None,
    zip_code: Annotated[str | None, Query(description="Five-digit ZIP code")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    q: Annotated[str | None, Query(description="Full-text search query")] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> StoreListResponse:
    """Search Restaurant Meals Program (RMP) locations, where eligible SNAP
    recipients can buy prepared meals with EBT. Results are paginated; use
    `total` with `limit`/`offset` to page."""
    return queries.search_stores(
        session,
        state=state,
        city=city,
        zip_code=zip_code,
        store_type=queries.RMP_STORE_TYPE,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{record_id}", response_model=StoreRead, operation_id="get_rmp_restaurant"
)
def get_restaurant(
    record_id: int, session: Annotated[Session, Depends(get_session)]
) -> Store:
    """Get one Restaurant Meals Program location by its USDA record_id."""
    store = queries.get_store(session, record_id, store_type=queries.RMP_STORE_TYPE)
    if store is None:
        raise HTTPException(status_code=404, detail="Store not found")
    return store
