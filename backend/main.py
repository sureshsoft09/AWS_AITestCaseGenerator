"""
MedAssureAI Backend API Entry Point.
FastAPI application with health check endpoint.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import config
from backend.logger import logger
from backend.api.upload import router as upload_router
from backend.api.generate import router as generate_router
from backend.api.enhance import router as enhance_router
from backend.api.migrate import router as migrate_router
from backend.api.projects import router as projects_router
from backend.api.analytics import router as analytics_router

# Create FastAPI application
app = FastAPI(
    title="MedAssureAI API",
    description="AI-driven test automation framework for healthcare software",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload_router)
app.include_router(generate_router)
app.include_router(enhance_router)
app.include_router(migrate_router)
app.include_router(projects_router)
app.include_router(analytics_router)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting MedAssureAI Backend API", extra={
        "environment": config.ENVIRONMENT,
        "aws_region": config.AWS_REGION
    })
    
    # Validate configuration
    try:
        config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration validation failed: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down MedAssureAI Backend API")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "medassure-api",
        "environment": config.ENVIRONMENT
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "MedAssureAI API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.ENVIRONMENT == "development"
    )
