from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import Store
from app.schemas import StoreListResponse, StoreRead
from app.routers.utils import apply_store_filters

router = APIRouter(prefix="/stores", tags=["stores"])


@router.get("/health", response_model=StoreListResponse)
def health():
    return {"status": 200, "message": "OK"}
