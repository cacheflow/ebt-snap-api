from app.config import normalize_database_url


def test_normalize_database_url_converts_supabase_postgres_scheme() -> None:
    assert (
        normalize_database_url("postgres://user:pass@example.com:5432/postgres")
        == "postgresql+psycopg://user:pass@example.com:5432/postgres"
    )


def test_normalize_database_url_converts_plain_postgresql_scheme() -> None:
    assert (
        normalize_database_url("postgresql://user:pass@example.com:5432/postgres")
        == "postgresql+psycopg://user:pass@example.com:5432/postgres"
    )


def test_normalize_database_url_leaves_driver_url_alone() -> None:
    url = "postgresql+psycopg://user:pass@example.com:5432/postgres"
    assert normalize_database_url(url) == url
