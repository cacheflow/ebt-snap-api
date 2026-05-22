from app.config import apply_database_password_override, normalize_database_url


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


def test_apply_database_password_override_url_encodes_password() -> None:
    url = "postgresql+psycopg://user:old@example.com:5432/postgres?sslmode=require"

    assert (
        apply_database_password_override(url, "p@ss/word#1")
        == "postgresql+psycopg://user:p%40ss%2Fword%231@example.com:5432/postgres?sslmode=require"
    )


def test_apply_database_password_override_ignores_empty_password() -> None:
    url = "postgresql+psycopg://user:old@example.com:5432/postgres"

    assert apply_database_password_override(url, "") == url
