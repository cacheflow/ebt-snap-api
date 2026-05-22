from fastapi import FastAPI

from app.config import Settings
from app.routers.stores import router as stores_router
from app.routers.rmp import router as rmp_router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings(database_url="")
    app = FastAPI(
        title=settings.app_name,
        description="API for querying USDA EBT-authorized retailers.",
        version=settings.app_version,
    )
    app.include_router(stores_router)
    app.include_router(rmp_router)

    @app.get("/")
    def root() -> dict[str, str]:
        return {"message": "EBT API running"}

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
