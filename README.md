# EBT SNAP API

A FastAPI backend for searching EBT/SNAP-authorized retailers and Restaurant Meals Program locations stored in Supabase Postgres.

## Features

- Search EBT/SNAP stores by state, city, ZIP code, and store type
- Fetch individual stores by `record_id`
- Import USDA CSV data into Postgres
- Upsert store records by `record_id`
- Interactive API docs with FastAPI at `/docs`

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