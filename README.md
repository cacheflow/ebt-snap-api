Absolutely. Here’s a cleaner README you can drop in.

````md
# EBT Restaurant Meal Program (RMP) API

A FastAPI backend for searching EBT/SNAP-authorized retailers and Restaurant Meals Program locations stored in Supabase Postgres.

The API supports filtered store search, pagination, full-text search, and individual store lookup by USDA `record_id`.

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Supabase
- Uvicorn
- Pytest

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
````

## Running the API

```bash
uvicorn app.main:app --reload
```

Once running, visit:

```txt
http://localhost:8000/docs
```

FastAPI will expose interactive Swagger docs at `/docs`.

---

# Endpoints

## List Stores

```http
GET /stores
```

Returns a paginated list of stores.

This endpoint supports filtering by state, city, ZIP code, store type, and search query.

### Query Parameters

| Parameter    |    Type | Required | Description                                                      |
| ------------ | ------: | -------: | ---------------------------------------------------------------- |
| `state`      |  string |       No | Two-letter state code. Example: `CA`                             |
| `city`       |  string |       No | City name. Example: `Los Angeles`                                |
| `zip_code`   |  string |       No | Five-digit ZIP code                                              |
| `store_type` |  string |       No | USDA store type                                                  |
| `q`          |  string |       No | Full-text search query                                           |
| `limit`      | integer |       No | Number of results to return. Min: `1`, Max: `500`, Default: `50` |
| `offset`     | integer |       No | Number of records to skip. Default: `0`                          |

### Example Requests

```http
GET /stores?state=CA
```

```http
GET /stores?city=Los Angeles&state=CA
```

```http
GET /stores?zip_code=90001
```

```http
GET /stores?store_type=Supermarket
```

```http
GET /stores?q=hot food&state=CA
```

```http
GET /stores?state=CA&limit=25&offset=50
```

### Response Shape

```json
{
  "total": 1234,
  "limit": 50,
  "offset": 0,
  "items": [
    {
      "id": 1,
      "record_id": 123456,
      "store_name": "Example Market",
      "city": "Los Angeles",
      "state": "CA",
      "zip_code": "90001",
      "store_type": "Supermarket"
    }
  ]
}
```

The exact fields inside `items` depend on the `StoreRead` schema.

---

## Get Store by Record ID

```http
GET /stores/{record_id}
```

Returns a single store by its USDA `record_id`.

### Path Parameters

| Parameter   |    Type | Required | Description          |
| ----------- | ------: | -------: | -------------------- |
| `record_id` | integer |      Yes | USDA store record ID |

### Example Request

```http
GET /stores/123456
```

### Successful Response

```json
{
  "id": 1,
  "record_id": 123456,
  "store_name": "Example Market",
  "city": "Los Angeles",
  "state": "CA",
  "zip_code": "90001",
  "store_type": "Supermarket"
}
```

### Error Response

If no store exists with the requested `record_id`, the API returns:

```json
{
  "detail": "Store not found"
}
```

Status code:

```http
404 Not Found
```

---

# Pagination

The `/stores` endpoint supports offset-based pagination.

Use `limit` to control page size.

Use `offset` to skip records.

Example:

```http
GET /stores?limit=50&offset=0
GET /stores?limit=50&offset=50
GET /stores?limit=50&offset=100
```

The response includes `total`, so clients can calculate the number of pages.

---

# Filtering

Filters can be combined.

Example:

```http
GET /stores?state=CA&city=Los Angeles&store_type=Supermarket&q=market
```

This returns stores matching all provided filters.

Supported filters:

* `state`
* `city`
* `zip_code`
* `store_type`
* `q`

---

# Development Notes

Store filtering is handled by `apply_store_filters`.

The list endpoint builds two SQL statements:

1. A filtered store query for the current page of results.
2. A filtered count query for the total number of matching records.

Results are ordered by:

```txt
store_name, id
```

This keeps pagination stable across requests.

---

# Project Goals

This API is designed to make EBT/SNAP retailer data easier to search and expose through a clean backend interface.

It can support:

* Public store lookup tools
* Restaurant Meals Program directories
* Local food access apps
* Internal civic data tools
* Search interfaces for SNAP-authorized retailers

```

One tiny note: your `GET /stores/{record_id}` route looks up by `Store.record_id`, not database `id`. That’s good, but the README should keep saying `record_id` clearly so future-you doesn’t curse present-you.
```

# Live Site
The site can be accessed at https://ebt-rmp-api-production.up.railway.app/stores