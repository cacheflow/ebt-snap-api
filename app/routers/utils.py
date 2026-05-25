import json

from sqlalchemy import Select, or_
from app.models import Store
import json
import pdb
import re

from app.routers import stores


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


def food_map():
    return {
        "mcdonalds": "burgers",
        "burger": "burgers",
        "burger king": "burgers",
        "wendys": "burgers",
        "in n out": "burgers",
        "jack in the box": "burgers",
        "whataburger": "burgers",
        "five guys": "burgers",
        "tacos": "mexican",
        "taco": "mexican",
        "chicken": "chicken",
        "cafe": "cafe",
        "juice": "juice_bar",
        "taqueria": "mexican",
        "deli": "sandwiches",
        "bakers": "burgers",
        "kfc": "chicken",
        "popeyes": "chicken",
        "raising canes": "chicken",
        "chick fil a": "chicken",
        "el pollo loco": "chicken",
        "wingstop": "wings",
        "buffalo wild wings": "wings",
        "subway": "sandwiches",
        "jersey mikes": "sandwiches",
        "jimmy johns": "sandwiches",
        "quiznos": "sandwiches",
        "dominos": "pizza",
        "pizza": "pizza",
        "Hamburgers": "burgers",
        "wingz": "chicken",
        "wings": "chicken",
        "mexican": "mexican",
        "arbys": "sandwiches",
        "jamaican": "chicken",
        "pizza hut": "pizza",
        "little caesars": "pizza",
        "papa johns": "pizza",
        "taco bell": "mexican",
        "del taco": "mexican",
        "chipotle": "mexican",
        "qdoba": "mexican",
        "panda express": "chinese",
        "pf changs": "chinese",
        "starbucks": "coffee",
        "dunkin": "coffee",
        "peets": "coffee",
        "dairy queen": "desserts",
        "baskin robbins": "desserts",
        "krispy kreme": "desserts",
    }


def add_food_category_to_store(stores: Store) -> Store:
    data = []
    for entry in stores:
        if entry.get("primary_food_category") is None:
            entry["primary_food_category"] = ""
            data.append(entry)
    return data


def dedupe_stores(stores: Store) -> Store:
    seen = set()
    deduped = []
    for store in stores:
        record_id = store.get("record_id")
        if record_id not in seen:
            deduped.append(store)
            seen.add(record_id)
    return deduped


def create_store_file(stores: Store) -> None:
    with open("enriched_stores.json", "w") as f:
        json.dump(stores, f, indent=2)

    return stores


def map_store_to_food_category():
    data = []
    data_set = set()

    with open("store_names.json") as f:
        store_data = json.load(f)
        dedupeded_stores = dedupe_stores(store_data)
        stoers_with_food_cats = add_food_category_to_store(dedupeded_stores)

        for entry in stoers_with_food_cats:
            store_name = entry.get("store_name", "").lower()
            store_name_list = store_name.split(" ")
            found_match = False
            for word in store_name_list:
                record_id = entry.get("record_id")
                if not record_id in data_set:
                    lowered_word = word.strip().lower()
                    normalized_word = re.sub("[^A-Za-z0-9]+", "", lowered_word)
                    word_match = normalized_word in food_map()

                    if word_match and not found_match:
                        entry["primary_food_category"] = food_map()[normalized_word]
                        data.append(entry)
                        data_set.add(record_id)
                        found_match = True

            data.append(entry)
    return dedupe_stores(data)


def count_missing_food_category(file_path: str) -> int:
    with open(file_path) as f:
        store_data = json.load(f)
        missing_count = 0

        for entry in store_data:
            if entry.get("primary_food_category") is None:
                missing_count += 1
        return missing_count


mapepd_rmp_stores = map_store_to_food_category()
create_store_file(mapepd_rmp_stores)

missing_count = count_missing_food_category("enriched_stores.json")
