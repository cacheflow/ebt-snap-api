from pydantic import BaseModel, ConfigDict


class StoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    record_id: int | None
    store_name: str | None
    store_street_address: str | None
    additional_address: str | None
    city: str | None
    state: str | None
    zip_code: str | None
    zip4: str | None
    county: str | None
    store_type: str | None
    latitude: float | None
    longitude: float | None
    incentive_program: str | None
    grantee_name: str | None
    object_id: int | None


class StoreListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[StoreRead]
