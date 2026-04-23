from fastapi import FastAPI

from app.core.config import settings
from app.api.v1.health import router as health_router


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

app.include_router(health_router)