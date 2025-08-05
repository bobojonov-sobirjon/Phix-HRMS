from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from .api import auth, profile, contact_us, faq, skills, roles, languages, locations, user_skills, data_management
from .api import job_post_type, job
from .database import engine
from .models import user, role, user_role, skill, user_skill, education, experience, certification, project, project_image, language, location, contact_us as contact_us_model, faq as faq_model, job_post_type as job_post_type_model, job as job_model, job_skill as job_skill_model
import traceback

app = FastAPI(title="Phix HRMS API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler for standardized error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "msg": exc.detail
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Log the full error for debugging
    print(f"Unhandled exception: {str(exc)}")
    print(f"Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "msg": "Internal server error"
        }
    )

# Include routers with /api/v1/ prefix
app.include_router(auth, prefix="/api/v1")
app.include_router(profile, prefix="/api/v1")
app.include_router(contact_us, prefix="/api/v1")
app.include_router(faq, prefix="/api/v1")
app.include_router(skills, prefix="/api/v1")
app.include_router(roles, prefix="/api/v1")
app.include_router(languages, prefix="/api/v1")
app.include_router(locations, prefix="/api/v1")
app.include_router(user_skills, prefix="/api/v1")
app.include_router(data_management, prefix="/api/v1")
app.include_router(job_post_type.router, prefix="/api/v1")
app.include_router(job.router, prefix="/api/v1")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create database tables
user.Base.metadata.create_all(bind=engine)
role.Base.metadata.create_all(bind=engine)
user_role.Base.metadata.create_all(bind=engine)
skill.Base.metadata.create_all(bind=engine)
user_skill.Base.metadata.create_all(bind=engine)
education.Base.metadata.create_all(bind=engine)
experience.Base.metadata.create_all(bind=engine)
certification.Base.metadata.create_all(bind=engine)
project.Base.metadata.create_all(bind=engine)
project_image.Base.metadata.create_all(bind=engine)
language.Base.metadata.create_all(bind=engine)
location.Base.metadata.create_all(bind=engine)
contact_us_model.Base.metadata.create_all(bind=engine)
faq_model.Base.metadata.create_all(bind=engine)
job_post_type_model.Base.metadata.create_all(bind=engine)
job_model.Base.metadata.create_all(bind=engine)
job_skill_model.Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {"message": "Phix HRMS API is running"}
