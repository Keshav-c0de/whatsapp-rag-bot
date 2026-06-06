from fastapi import FastAPI
from .router.whatsapp import router as whatsapp_router
import logfire


def create_app():
    app = FastAPI()
    app.include_router(whatsapp_router, prefix="/whatsapp", tags=["whatsapp"])
    return app

app = create_app()
logfire.configure()
try:
    logfire.instrument_fastapi(app)
except RuntimeError:
    pass