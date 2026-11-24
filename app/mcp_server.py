"""MCP tools for the EBT/SNAP store data.

Tools call the same query functions as the HTTP routes (app.queries) directly,
not via the HTTP API. The server is served over Streamable HTTP at /mcp; see
main.create_app for how it's mounted.
"""

import os
from typing import Annotated, Callable, TypeVar

import anyio.to_thread
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from pydantic import Field
from sqlalchemy.orm import Session

from app import queries
from app.database import session_scope
from app.schemas import StoreListResponse, StoreRead

T = TypeVar("T")

# All tools only read public data.
READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
)

State = Annotated[
    str | None, Field(description="Two-letter US state code, e.g. 'CA'.")
]
City = Annotated[str | None, Field(description="City name, e.g. 'Los Angeles'.")]
ZipCode = Annotated[str | None, Field(description="Five-digit ZIP code, e.g. '90001'.")]
Query = Annotated[
    str | None,
    Field(
        description="Free-text search across name, address, city, state, ZIP, "
        "county, and store type, e.g. 'tacos'."
    ),
]
Limit = Annotated[int, Field(ge=1, le=100, description="Max results to return.")]
Offset = Annotated[
    int, Field(ge=0, description="Results to skip, for paging past `limit`.")
]
RecordId = Annotated[int, Field(description="USDA record_id of the location.")]


def _transport_security() -> TransportSecuritySettings:
    # DNS-rebinding protection: only these Host headers may reach /mcp. Local
    # hosts are always allowed; set MCP_ALLOWED_HOSTS (comma-separated, e.g.
    # "api.example.com,api.example.com:*") for a deployed hostname, or every
    # /mcp request there gets 421 Misdirected Request.
    extra = [h.strip() for h in os.getenv("MCP_ALLOWED_HOSTS", "").split(",")]
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*", *filter(None, extra)],
        allowed_origins=["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"],
    )


async def _run(fn: Callable[[Session], T]) -> T:
    # SQLAlchemy here is synchronous; FastMCP would call a sync tool directly on
    # the event loop, so run the query on a worker thread instead.
    def call() -> T:
        with session_scope() as session:
            return fn(session)

    return await anyio.to_thread.run_sync(call)


def create_mcp_server() -> FastMCP:
    mcp = FastMCP(
        "EBT SNAP API",
        instructions=(
            "Look up USDA EBT/SNAP-authorized retailers and Restaurant Meals "
            "Program (RMP) locations in the US. Use the RMP tools when the user "
            "wants a prepared/restaurant meal paid with EBT; use the store tools "
            "for groceries and all other retailers. List tools return `total`, "
            "so page with `offset` if total > limit."
        ),
        # Read-only, no server-initiated messages: no need for sessions, and
        # plain JSON responses are simpler for clients and load balancers.
        stateless_http=True,
        json_response=True,
        # Mounted at the app root; this is the full public path.
        streamable_http_path="/mcp",
        transport_security=_transport_security(),
    )

    @mcp.tool(annotations=READ_ONLY)
    async def search_stores(
        state: State = None,
        city: City = None,
        zip_code: ZipCode = None,
        store_type: Annotated[
            str | None,
            Field(
                description="USDA store type, e.g. 'Supermarket', 'Convenience "
                "Store', 'Farmers and Markets'. Partial matches allowed."
            ),
        ] = None,
        query: Query = None,
        limit: Limit = 20,
        offset: Offset = 0,
    ) -> StoreListResponse:
        """Search EBT/SNAP-authorized retailers (grocery stores, supermarkets,
        convenience stores, farmers markets, etc.). Filters combine with AND."""
        return await _run(
            lambda s: queries.search_stores(
                s,
                state=state,
                city=city,
                zip_code=zip_code,
                store_type=store_type,
                q=query,
                limit=limit,
                offset=offset,
            )
        )

    @mcp.tool(annotations=READ_ONLY)
    async def get_store(record_id: RecordId) -> StoreRead:
        """Get full details for one EBT/SNAP-authorized retailer by record_id
        (from search_stores results)."""
        store = await _run(lambda s: queries.get_store(s, record_id))
        if store is None:
            raise ToolError(f"No store with record_id {record_id}.")
        return StoreRead.model_validate(store)

    @mcp.tool(annotations=READ_ONLY)
    async def search_rmp_restaurants(
        state: State = None,
        city: City = None,
        zip_code: ZipCode = None,
        query: Query = None,
        limit: Limit = 20,
        offset: Offset = 0,
    ) -> StoreListResponse:
        """Search Restaurant Meals Program (RMP) locations: restaurants where
        eligible SNAP recipients (e.g. elderly, disabled, or homeless) can buy
        prepared meals with EBT. Filters combine with AND."""
        return await _run(
            lambda s: queries.search_stores(
                s,
                state=state,
                city=city,
                zip_code=zip_code,
                store_type=queries.RMP_STORE_TYPE,
                q=query,
                limit=limit,
                offset=offset,
            )
        )

    @mcp.tool(annotations=READ_ONLY)
    async def get_rmp_restaurant(record_id: RecordId) -> StoreRead:
        """Get full details for one Restaurant Meals Program location by
        record_id (from search_rmp_restaurants results)."""
        store = await _run(
            lambda s: queries.get_store(
                s, record_id, store_type=queries.RMP_STORE_TYPE
            )
        )
        if store is None:
            raise ToolError(f"No Restaurant Meals Program location with record_id {record_id}.")
        return StoreRead.model_validate(store)

    return mcp
