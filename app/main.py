from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import engine, get_db, Base
from .api import auth, roles, locations, skills, profile, users, user_skills, faq, contact_us, languages, data_management
from .config import settings
from .repositories.role_repository import RoleRepository

from . import models
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Phix HRMS Authentication API"
)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add CORS middleware for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(roles.router, prefix="/api/v1")
app.include_router(locations.router, prefix="/api/v1")
app.include_router(skills.router, prefix="/api/v1")
app.include_router(profile.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(user_skills.router, prefix="/api/v1")
app.include_router(faq.router, prefix="/api/v1")
app.include_router(contact_us.router, prefix="/api/v1")
app.include_router(languages.router, prefix="/api/v1")
app.include_router(data_management.router, prefix="/api/v1")

@app.on_event("startup")
def startup_event():
    db = next(get_db())
    repo = RoleRepository(db)
    repo.seed_initial_roles()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    safe_detail = [{"loc": error["loc"], "msg": error["msg"], "type": error["type"]} for error in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": safe_detail})

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
