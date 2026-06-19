from fastapi import FastAPI

from app.api.routes import auth, users
from app.core.config import get_settings
from app.core.errors import AppError, app_error_handler


settings = get_settings()

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    debug=settings.app_debug,
)
app.add_exception_handler(AppError, app_error_handler)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
