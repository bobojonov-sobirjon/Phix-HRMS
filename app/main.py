from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from .api import auth, profile, contact_us, faq, skills, roles, languages, locations, user_skills, data_management
from .api import company, education_facility, certification_center, gig_jobs, proposals
from .api import saved_jobs
from .api import corporate_profile, full_time_job, team_member, category, chat, corporate_profile_follow, notifications
from .database import engine
from .models import user, role, user_role, skill, user_skill, education, experience, certification, project, project_image, language, location, contact_us as contact_us_model, faq as faq_model, company as company_model, education_facility as education_facility_model, certification_center as certification_center_model, gig_job, proposal, saved_job, corporate_profile as corporate_profile_model, full_time_job as full_time_job_model, team_member as team_member_model, category as category_model, chat as chat_model, corporate_profile_follow as corporate_profile_follow_model, notification as notification_model
import traceback
import os

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
app.include_router(company.router, prefix="/api/v1")
app.include_router(education_facility.router, prefix="/api/v1")
app.include_router(certification_center.router, prefix="/api/v1")
app.include_router(gig_jobs, prefix="/api/v1")
app.include_router(proposals, prefix="/api/v1")
app.include_router(saved_jobs.router, prefix="/api/v1")
app.include_router(corporate_profile.router, prefix="/api/v1")
app.include_router(corporate_profile_follow.router, prefix="/api/v1")
app.include_router(full_time_job.router, prefix="/api/v1")
app.include_router(team_member.router, prefix="/api/v1")
app.include_router(category.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1/chat")
app.include_router(notifications.router, prefix="/api/v1")

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
company_model.Base.metadata.create_all(bind=engine)
education_facility_model.Base.metadata.create_all(bind=engine)
certification_center_model.Base.metadata.create_all(bind=engine)
gig_job.Base.metadata.create_all(bind=engine)
proposal.Base.metadata.create_all(bind=engine)
saved_job.Base.metadata.create_all(bind=engine)
corporate_profile_model.Base.metadata.create_all(bind=engine)
full_time_job_model.Base.metadata.create_all(bind=engine)
team_member_model.Base.metadata.create_all(bind=engine)
category_model.Base.metadata.create_all(bind=engine)
chat_model.Base.metadata.create_all(bind=engine)
corporate_profile_follow_model.Base.metadata.create_all(bind=engine)
notification_model.Base.metadata.create_all(bind=engine)


from dotenv import load_dotenv

# Load .env file
load_dotenv()

# If .env doesn't exist, create it from env.example
if not os.path.exists('.env') and os.path.exists('env.example'):
    import shutil
    shutil.copy('env.example', '.env')
    
    # Reload environment variables
    load_dotenv()

FIREBASE_TYPE = os.getenv("TYPE")
FIREBASE_PROJECT_ID = os.getenv("PROJECT_ID")
FIREBASE_PRIVATE_KEY_ID = os.getenv("PRIVATE_KEY_ID")
FIREBASE_PRIVATE_KEY = os.getenv("PRIVATE_KEY")
FIREBASE_CLIENT_EMAIL = os.getenv("CLIENT_EMAIL")
FIREBASE_CLIENT_ID = os.getenv("CLIENT_ID")
FIREBASE_AUTH_URI = os.getenv("AUTH_URI")
FIREBASE_TOKEN_URI = os.getenv("TOKEN_URI")
FIREBASE_AUTH_PROVIDER_CERT_URL = os.getenv("AUTH_PROVIDER_CERT_URL")
FIREBASE_CLIENT_CERT_URL = os.getenv("CLIENT_CERT_URL")
FIREBASE_UNIVERSE_DOMAIN = os.getenv("UNIVERSE_DOMAIN")

@app.get("/")
async def root():
    return {"message": "Phix HRMS API is running"}
