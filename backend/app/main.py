"""
Esclavizador - Time Tracking System
Main FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import lifespan


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Corporate time tracking utility with multi-tenant support",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    debug=settings.debug,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get(
    "/health",
    tags=["Health"],
    response_model=dict,
    summary="Health check endpoint",
    description="Check if the API is running and database is accessible"
)
async def health_check() -> JSONResponse:
    """
    Health check endpoint.

    Returns:
        JSONResponse: Health status
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "app_name": settings.app_name,
            "version": settings.app_version,
            "environment": "development" if settings.debug else "production"
        },
        status_code=200
    )


# Root endpoint
@app.get(
    "/",
    tags=["Root"],
    response_model=dict,
    summary="API root endpoint",
    description="Get API information"
)
async def root() -> JSONResponse:
    """
    Root endpoint with API information.

    Returns:
        JSONResponse: API info
    """
    return JSONResponse(
        content={
            "message": f"Welcome to {settings.app_name} API",
            "version": settings.app_version,
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health"
        },
        status_code=200
    )


# API Routers
from app.api.v1 import auth, projects, tasks, time_entries, tags, users

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(time_entries.router, prefix="/api/v1/time-entries", tags=["Time Entries"])
app.include_router(tags.router, prefix="/api/v1/tags", tags=["Tags"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
