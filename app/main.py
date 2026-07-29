from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import health, stories, trace, ask, hot_topics, topics

app = FastAPI(title="SourceTrace API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(stories.router, prefix="/api/v1")
app.include_router(trace.router, prefix="/api/v1")
app.include_router(ask.router, prefix="/api/v1")
app.include_router(hot_topics.router, prefix="/api/v1")
app.include_router(topics.router, prefix="/api/v1")
