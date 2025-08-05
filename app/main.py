from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import engine, get_db, Base
from .api import auth, roles, locations, skills, profile, user_skills, faq, contact_us, languages, data_management
from .config import settings
from .repositories.role_repository import RoleRepository

from . import models
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import time
import asyncio
from .utils.email import cleanup_email_executor
from .utils.performance import performance_monitor, monitor_performance_async

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app with optimized settings
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Phix HRMS Authentication API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add CORS middleware for mobile app with optimized settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Performance monitoring middleware
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    """Monitor request performance"""
    start_time = time.time()
    
    # Add request ID for tracking
    request_id = f"{int(start_time * 1000)}"
    request.state.request_id = request_id
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add performance headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        raise

# Include routers
app.include_router(auth, prefix="/api/v1")
app.include_router(roles, prefix="/api/v1")
app.include_router(locations, prefix="/api/v1")
app.include_router(skills, prefix="/api/v1")
app.include_router(profile, prefix="/api/v1")                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
app.include_router(user_skills, prefix="/api/v1")
app.include_router(faq, prefix="/api/v1")
app.include_router(contact_us, prefix="/api/v1")
app.include_router(languages, prefix="/api/v1")
app.include_router(data_management, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Application startup event with optimized initialization"""
    try:
        # Initialize database and seed data
        db = next(get_db())
        repo = RoleRepository(db)
        repo.seed_initial_roles()
        
        # Start performance monitoring
        asyncio.create_task(monitor_performance_async())
        
    except Exception as e:
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event with cleanup"""
    try:
        # Cleanup email executor
        cleanup_email_executor()
    except Exception as e:
        pass

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed logging"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    safe_detail = [{"loc": error["loc"], "msg": error["msg"], "type": error["type"]} for error in exc.errors()]
    return JSONResponse(
        status_code=422, 
        content={
            "detail": safe_detail,
            "request_id": request_id
        }
    )

@app.get("/")
async def root():
    """Root endpoint with performance info"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "status": "running",
        "performance": {
            "database_pool_size": engine.pool.size(),
            "database_checked_in": engine.pool.checkedin(),
            "database_checked_out": engine.pool.checkedout()
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint with detailed status"""
    try:
        # Test database connection
        db = next(get_db())
        db.execute("SELECT 1")
        db.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": time.time()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": time.time()
            }
        )

@app.get("/performance")
async def get_performance_stats():
    """Get detailed performance statistics"""
    try:
        stats = performance_monitor.get_performance_stats()
        return {
            "status": "success",
            "data": stats,
            "timestamp": time.time()
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Failed to get performance statistics",
                "error": str(e)
            }
        )

@app.post("/performance/reset")
async def reset_performance_stats():
    """Reset performance statistics"""
    try:
        performance_monitor.reset_stats()
        return {
            "status": "success",
            "message": "Performance statistics reset successfully"
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Failed to reset performance statistics",
                "error": str(e)
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info",
        access_log=True
    )
