import argparse
import csv
import re
import sys
from pathlib import Path
import pdb
from rich import print
from typing import Any, Iterator

import json
from supabase import create_client
from urllib.parse import quote
import os
from dotenv import load_dotenv

load_dotenv()


databse_url = os.getenv("SUPABASE_URL")
supabase_key = quote(os.getenv("SUPABASE_KEY") or "", safe="")

supabase = create_client(databse_url, supabase_key)


if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.database import get_engine
from app.models import Store

TABLE_COLUMNS = {
    "record_id",
    "store_name",
    "store_street_address",
    "additional_address",
    "city",
    "state",
    "zip_code",
    "zip4",
    "county",
    "store_type",
    "latitude",
    "longitude",
    "incentive_program",
    "grantee_name",
    "object_id",
}

INTEGER_COLUMNS = {"record_id", "object_id"}
FLOAT_COLUMNS = {"latitude", "longitude"}

HEADER_OVERRIDES = {
    "additonal_address": "additional_address",
    "objectid": "object_id",
}


def normalize_header(value: str) -> str:
    normalized = value.strip().replace("\ufeff", "")
    normalized = re.sub(r"[^0-9a-zA-Z]+", "_", normalized).strip("_").lower()
    return HEADER_OVERRIDES.get(normalized, normalized)


def clean_value(key: str, value: str | None) -> Any:
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return None
    if key in INTEGER_COLUMNS:
        return int(float(value))
    if key in FLOAT_COLUMNS:
        return float(value)
    if key == "state":
        return value.upper()
    return value


def clean_row(row: dict[str, str | None]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for raw_key, value in row.items():
        key = normalize_header(raw_key)
        if key not in TABLE_COLUMNS:
            continue
        cleaned[key] = clean_value(key, value)
    return cleaned


def batched(
    rows: Iterator[dict[str, Any]], batch_size: int
) -> Iterator[list[dict[str, Any]]]:
    batch: list[dict[str, Any]] = []
    for row in rows:
        batch.append(row)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def upsert_batch(file_path: str) -> None:
    rows = []
    json_path = Path(file_path)
    with json_path.open("r", encoding="utf-8") as f:
        stores = json.load(f)
        for store in stores:
            # rows.append({
            #     'record_id': store.get('record_id'),
            #     'primary_food_category': store.get('primary_food_category')
            # })
            record_id = store.get("record_id")
            supabase.table("stores").update(store).eq("record_id", record_id).execute()


def insert_batch(
    session: Session,
    rows: Iterator[dict[str, Any]],
    batch_size: int,
) -> int:
    imported = 0
    for batch in batched(rows, batch_size):
        stmt = insert(Store).values(batch)
        update_columns = {
            col.name: stmt.excluded[col.name]
            for col in Store.__table__.columns
            if col.name not in {"id", "record_id"}
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=[Store.record_id],
            set_=update_columns,
        )
        session.execute(stmt)
        session.commit()
        imported += len(batch)
    return imported


def import_csv(csv_path: Path, batch_size: int) -> int:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = (clean_row(row) for row in csv.DictReader(file))
        with Session(get_engine()) as session:
            imported = insert_batch(session, rows, batch_size)
    print(f"Imported {imported:,} rows")
    return imported


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import EBT store CSV rows into Postgres."
    )
    parser.add_argument(
        "csv_path",
        type=Path,
        nargs="?",
        default=Path("ebt_stores.csv"),
        help="Path to the EBT stores CSV file.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of rows to upsert per database transaction.",
    )
    args = parser.parse_args()

    total = import_csv(args.csv_path, args.batch_size)
    print(f"Done. Imported {total:,} rows.")


if __name__ == "__main__":
    upsert_batch("enriched_stores.json")
