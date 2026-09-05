# app/main.py
from fastapi import FastAPI
from app.api.routes import profiles, runs, queries, recommendations
from app.db.session import create_tables
from app.observability.logger import setup_logging
from app.config import settings

# Setup JSON logging on startup
setup_logging(settings.log_level)

# Create FastAPI app
app = FastAPI(
    title="Search Intelligence Agent API",
    description="Agentic DAG pipeline for brand search and AI visibility analysis",
    version="1.0.0"
)

# Create DB tables on startup
create_tables()

# Register all routes
app.include_router(profiles.router, prefix="/api/v1", tags=["Profiles"])
app.include_router(runs.router, prefix="/api/v1", tags=["Pipeline Runs"])
app.include_router(queries.router, prefix="/api/v1", tags=["Queries"])
app.include_router(recommendations.router, prefix="/api/v1", tags=["Recommendations"])


@app.get("/")
def root():
    return {"message": "Search Intelligence Agent API is running"}