import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from chatbot.domain.exceptions import AltibbiError
from chatbot.infrastructure.settings import Settings
from chatbot.presentation.api.routers.chat_router import router as chat_router
from chatbot.presentation.api.routers.config_router import router as config_router
from chatbot.presentation.api.routers.sessions_router import router as sessions_router
from chatbot.presentation.api.schemas import ErrorResponse, HealthResponse

logger = logging.getLogger(__name__)


class ApiApplicationFactory:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings.from_env()

    def create(self) -> FastAPI:
        app = FastAPI(
            title="Altibbi Medical Chatbot API",
            version="1.0.0",
            docs_url="/api/docs",
            redoc_url="/api/redoc",
            openapi_url="/api/openapi.json",
        )

        self._register_middleware(app)
        self._register_exception_handlers(app)
        self._register_routes(app)
        self._register_static_frontend(app)
        return app

    def _register_middleware(self, app: FastAPI) -> None:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self._settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _register_exception_handlers(self, app: FastAPI) -> None:
        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(
            _request: Request,
            exc: RequestValidationError,
        ) -> JSONResponse:
            return JSONResponse(
                status_code=422,
                content=ErrorResponse(
                    detail="Request validation failed.",
                    code="validation_error",
                ).model_dump()
                | {"errors": exc.errors()},
            )

        @app.exception_handler(AltibbiError)
        async def altibbi_exception_handler(
            _request: Request,
            exc: AltibbiError,
        ) -> JSONResponse:
            logger.exception("Domain error: %s", exc)
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(detail=str(exc), code="domain_error").model_dump(),
            )

    def _register_routes(self, app: FastAPI) -> None:
        @app.get("/health", response_model=HealthResponse, tags=["health"])
        def health_check() -> HealthResponse:
            return HealthResponse()

        api_prefix = "/api/v1"
        app.include_router(config_router, prefix=api_prefix)
        app.include_router(sessions_router, prefix=api_prefix)
        app.include_router(chat_router, prefix=api_prefix)

    def _register_static_frontend(self, app: FastAPI) -> None:
        dist_path = self._settings.frontend_dist_path
        if not dist_path.exists():
            logger.warning("Frontend build not found at %s — API-only mode.", dist_path)
            return

        assets_path = dist_path / "assets"
        if assets_path.exists():
            app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

        index_file = dist_path / "index.html"

        @app.get("/", include_in_schema=False)
        def serve_root() -> FileResponse:
            return FileResponse(index_file)

        @app.get("/{full_path:path}", include_in_schema=False)
        def serve_spa(full_path: str) -> Response:
            if full_path.startswith("api/"):
                return JSONResponse(status_code=404, content={"detail": "Not found"})
            candidate = dist_path / full_path
            if candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(index_file)


def create_app() -> FastAPI:
    return ApiApplicationFactory().create()
