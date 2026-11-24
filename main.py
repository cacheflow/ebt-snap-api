from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings
from app.mcp_server import create_mcp_server
from app.routers.rmp import router as rmp_router
from app.routers.stores import router as stores_router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings(database_url="")
    mcp = create_mcp_server()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # The Streamable HTTP session manager must be running to serve /mcp.
        async with mcp.session_manager.run():
            yield

    app = FastAPI(
        title=settings.app_name,
        description="API for querying USDA EBT-authorized retailers.",
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.include_router(stores_router)
    app.include_router(rmp_router)

    @app.get("/")
    def root() -> dict[str, str]:
        return {"message": "EBT API running"}

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # MCP at /mcp. Mounted at the root (after all routes, so they match first)
    # rather than at "/mcp": a Starlette Mount at "/mcp" only matches "/mcp/...",
    # and POST /mcp would get a 307 redirect that many MCP clients won't follow.
    app.mount("/", mcp.streamable_http_app())

    return app


app = create_app()
