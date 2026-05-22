from sqlalchemy import Select, or_
from app.models import Store


def clean(value: str | None) -> str | None:
    if value is None:
        return ""
    if isinstance(value, str):
        value = value.strip()
    if isinstance(value, list):
        value = []
        for v in value:
            if isinstance(v, str):
                v = v.strip()
                if v:
                    value.append(v)
    return value or None


def apply_store_filters(
    stmt: Select[tuple[Store]] | Select[tuple[int]],
    *,
    state: str | None,
    city: str | None,
    zip_code: str | None,
    q: str | None = None,
    store_type: str | None,
) -> Select[tuple[Store]] | Select[tuple[int]]:
    state = clean(state)
    city = clean(city)
    zip_code = clean(zip_code)
    store_type = clean(store_type)
    q = clean(q)

    if state:
        stmt = stmt.where(Store.state.ilike(f"%{state}%"))
    if city:
        stmt = stmt.where(Store.city.ilike(f"%{city}%"))
    if zip_code:
        stmt = stmt.where(Store.zip_code == zip_code)
    if store_type:
        stmt = stmt.where(Store.store_type.ilike(f"%{store_type}%"))

    if q:
        query_pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Store.store_name.ilike(query_pattern),
                Store.store_street_address.ilike(query_pattern),
                Store.city.ilike(query_pattern),
                Store.state.ilike(query_pattern),
                Store.zip_code.ilike(query_pattern),
                Store.zip4.ilike(query_pattern),
                Store.county.ilike(query_pattern),
                Store.store_type.ilike(query_pattern),
            )
        )
    return stmt
