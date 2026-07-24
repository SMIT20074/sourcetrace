from fastapi import FastAPI
from app.routes import health, stories, trace, ask

app = FastAPI(title="SourceTrace API")

app.include_router(health.router, prefix="/api/v1")
app.include_router(stories.router, prefix="/api/v1")
app.include_router(trace.router, prefix="/api/v1")
app.include_router(ask.router, prefix="/api/v1")
