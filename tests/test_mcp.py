"""End-to-end tests for the MCP server.

These speak JSON-RPC to the real /mcp Streamable HTTP endpoint. The database is
an in-memory SQLite stand-in for Postgres so the real query code runs; it's
swapped in at app.database.get_engine, which both the HTTP routes and the MCP
tools go through.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import database
from app.models import Base, Store
from main import create_app

MCP_HEADERS = {
    "accept": "application/json, text/event-stream",
    "content-type": "application/json",
}
TOOL_NAMES = {
    "search_stores",
    "get_store",
    "search_rmp_restaurants",
    "get_rmp_restaurant",
}


class McpClient:
    def __init__(self, client: TestClient) -> None:
        self._client = client
        self._next_id = 1
        init = self.request(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "pytest", "version": "0"},
            },
        )
        assert "result" in init, init

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "id": self._next_id, "method": method}
        if params is not None:
            payload["params"] = params
        self._next_id += 1
        response = self._client.post("/mcp", headers=MCP_HEADERS, json=payload)
        assert response.status_code == 200, response.text
        return response.json()

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict:
        return self.request("tools/call", {"name": name, "arguments": arguments})[
            "result"
        ]


def make_store(id: int, record_id: int, name: str, store_type: str, **kw) -> Store:
    return Store(
        id=id,
        record_id=record_id,
        store_name=name,
        store_type=store_type,
        state=kw.get("state", "CA"),
        city=kw.get("city", "Los Angeles"),
        zip_code=kw.get("zip_code", "90001"),
    )


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(
            [
                make_store(1, 100, "Taco Spot", "rmp"),
                make_store(2, 101, "Burger Hut", "rmp", state="NY", city="Albany"),
                make_store(3, 200, "Big Market", "Supermarket"),
            ]
        )
        session.commit()
    monkeypatch.setattr(database, "get_engine", lambda: engine)

    # The MCP transport's DNS-rebinding protection only allows local Hosts.
    with TestClient(create_app(), base_url="http://localhost:8000") as client:
        yield client


@pytest.fixture
def mcp(client: TestClient) -> McpClient:
    return McpClient(client)


def structured(result: dict) -> Any:
    assert result.get("isError") is not True, result
    return result["structuredContent"]


def test_lists_tools_with_schemas_and_read_only_hints(mcp: McpClient) -> None:
    tools = {t["name"]: t for t in mcp.request("tools/list")["result"]["tools"]}

    assert set(tools) == TOOL_NAMES
    assert all(t["annotations"]["readOnlyHint"] is True for t in tools.values())
    assert all(t["description"] for t in tools.values())

    search = tools["search_stores"]["inputSchema"]
    assert {"state", "city", "zip_code", "store_type", "query", "limit", "offset"} == set(
        search["properties"]
    )
    assert search["properties"]["limit"]["maximum"] == 100
    # RMP search can't be widened to other store types.
    assert "store_type" not in tools["search_rmp_restaurants"]["inputSchema"]["properties"]
    assert tools["get_store"]["inputSchema"]["required"] == ["record_id"]
    assert "outputSchema" in tools["get_store"]


def test_search_stores_applies_filters(mcp: McpClient) -> None:
    body = structured(mcp.call_tool("search_stores", {"state": "CA"}))

    assert body["total"] == 2
    assert {s["record_id"] for s in body["items"]} == {100, 200}


def test_search_stores_pages_with_limit_and_offset(mcp: McpClient) -> None:
    first = structured(mcp.call_tool("search_stores", {"limit": 2}))
    second = structured(mcp.call_tool("search_stores", {"limit": 2, "offset": 2}))

    assert first["total"] == second["total"] == 3
    assert len(first["items"]) == 2 and len(second["items"]) == 1


def test_search_rmp_restaurants_returns_only_rmp(mcp: McpClient) -> None:
    body = structured(mcp.call_tool("search_rmp_restaurants", {}))

    assert body["total"] == 2
    assert {s["store_type"] for s in body["items"]} == {"rmp"}


def test_get_store_returns_record(mcp: McpClient) -> None:
    body = structured(mcp.call_tool("get_store", {"record_id": 200}))

    assert body["store_name"] == "Big Market"


def test_get_rmp_restaurant_reports_non_rmp_as_tool_error(mcp: McpClient) -> None:
    # 200 exists but is not an RMP location.
    result = mcp.call_tool("get_rmp_restaurant", {"record_id": 200})

    assert result["isError"] is True
    assert "200" in result["content"][0]["text"]


def test_invalid_arguments_are_rejected(mcp: McpClient) -> None:
    result = mcp.call_tool("search_stores", {"limit": 1000})

    assert result["isError"] is True


def test_rejects_unlisted_host_header(client: TestClient) -> None:
    response = client.post(
        "/mcp",
        headers={**MCP_HEADERS, "host": "evil.example.com"},
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
    )

    assert response.status_code == 421


def test_http_routes_still_work(client: TestClient) -> None:
    # The routes and tools share app.queries; guard the refactor.
    assert client.get("/stores", params={"state": "CA"}).json()["total"] == 2
    assert client.get("/rmp").json()["total"] == 2
    assert client.get("/rmp/200").status_code == 404
    assert client.get("/stores/200").json()["store_name"] == "Big Market"
    assert client.get("/health").json() == {"status": "ok"}
