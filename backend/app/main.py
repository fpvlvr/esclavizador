"""
Esclavizador - Time Tracking System
Main FastAPI application entry point.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import lifespan
from app.core.logging_config import configure_logging

# Configure logging at module import
configure_logging()
logger = logging.getLogger(__name__)


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


# Custom exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch all unhandled exceptions and log them with full stacktrace."""
    logger.error(
        f"Unhandled exception during {request.method} {request.url.path}",
        exc_info=exc,
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None,
        },
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Log validation errors with details."""
    errors = exc.errors()

    # Convert non-JSON-serializable error objects to strings
    for error in errors:
        if "ctx" in error and "error" in error["ctx"]:
            # Convert ValueError/Exception objects to strings
            error_obj = error["ctx"]["error"]
            if isinstance(error_obj, Exception):
                error["ctx"]["error"] = str(error_obj)

    logger.warning(
        f"Validation error during {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "errors": errors,
        },
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
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
from app.api.v1 import auth, projects, tasks, time_entries, tags, users, reports

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(time_entries.router, prefix="/api/v1/time-entries", tags=["Time Entries"])
app.include_router(tags.router, prefix="/api/v1/tags", tags=["Tags"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
