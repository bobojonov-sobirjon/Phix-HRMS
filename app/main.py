"""
Main FastAPI application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

from .core.logging_config import logger
from .core.middleware import RequestLoggingMiddleware, ErrorLoggingMiddleware, CORSHeaderMiddleware
from .core.exception_handlers import http_exception_handler, general_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from .core.router_setup import register_routers
from .core.database_setup import create_all_tables
from .utils.admin_setup import ensure_admin_user_exists

load_dotenv()

if not os.path.exists('.env') and os.path.exists('env.example'):
    import shutil
    shutil.copy('env.example', '.env')
    load_dotenv()

app = FastAPI(
    title="Phix HRMS API", 
    version="1.0.0", 
    redirect_slashes=False,  # Redirect'lar CORS header'larni yo'qotadi, shuning uchun False
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware birinchi bo'lishi kerak (middleware'lar teskari tartibda ishlaydi)
# Environment variable'dan CORS origin'larni o'qish
cors_origins = os.getenv("CORS_ORIGINS", "*")
if cors_origins == "*":
    # Agar "*" bo'lsa, credentials bilan ishlamaydi
    allow_origins = ["*"]
    allow_credentials = False
else:
    # Agar aniq origin'lar bo'lsa, ularni listga aylantiramiz
    allow_origins = [origin.strip() for origin in cors_origins.split(",")]
    allow_credentials = True

# CORS middleware birinchi bo'lishi kerak
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Preflight cache vaqti (1 soat)
)

# Qo'shimcha CORS header middleware - barcha response'larda CORS header'larini ta'minlash uchun
app.add_middleware(CORSHeaderMiddleware)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorLoggingMiddleware)

app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

register_routers(app)

app.mount("/static", StaticFiles(directory="static"), name="static")

create_all_tables()

logger.info("Checking admin user...")
ensure_admin_user_exists()

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

logger.info("Phix HRMS API application initialized")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Phix HRMS API is running"}
