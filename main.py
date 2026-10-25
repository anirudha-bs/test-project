from fastapi import FastAPI
from api.routes import alerts

app = FastAPI()

app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
