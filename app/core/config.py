import os
import json
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

if not os.path.exists('.env') and os.path.exists('env.example'):
    import shutil
    shutil.copy('env.example', '.env')
    
    load_dotenv()


def load_firebase_credentials() -> Optional[Dict[str, Any]]:
    """
    Load Firebase credentials from JSON file or environment variables.
    
    Priority:
    1. FIREBASE_CREDENTIALS_JSON file path
    2. Individual environment variables
    
    Returns:
        Dict with Firebase service account credentials or None
    """
    # Try to load from JSON file first
    json_path = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if json_path and os.path.exists(json_path):
        try:
            with open(json_path, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    
    # Fallback to environment variables
    try:
        private_key = os.getenv("PRIVATE_KEY", "")
        if private_key:
            # Replace escaped newlines with actual newlines
            private_key = private_key.replace('\\n', '\n')
        
        credentials = {
            "type": os.getenv("TYPE", "service_account"),
            "project_id": os.getenv("PROJECT_ID"),
            "private_key_id": os.getenv("PRIVATE_KEY_ID"),
            "private_key": private_key,
            "client_email": os.getenv("CLIENT_EMAIL"),
            "client_id": os.getenv("CLIENT_ID"),
            "auth_uri": os.getenv("AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": os.getenv("TOKEN_URI", "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"),
            "client_x509_cert_url": os.getenv("CLIENT_CERT_URL"),
            "universe_domain": os.getenv("UNIVERSE_DOMAIN", "googleapis.com")
        }
        
        # Check if required fields are present
        if credentials.get("project_id") and credentials.get("private_key") and credentials.get("client_email"):
            return credentials
        
        return None
        
    except Exception:
        return None


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:0576@localhost:5432/phix_hrms")
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    SMTP_OUTLOOK_SERVER: str = os.getenv("SMTP_OUTLOOK_SERVER", "smtp-mail.outlook.com")
    SMTP_OUTLOOK_PORT: int = int(os.getenv("SMTP_OUTLOOK_PORT", "587"))
    SMTP_OUTLOOK_USERNAME: str = os.getenv("SMTP_OUTLOOK_USERNAME", "")
    SMTP_OUTLOOK_PASSWORD: str = os.getenv("SMTP_OUTLOOK_PASSWORD", "")
    
    SMTP_YAHOO_SERVER: str = os.getenv("SMTP_YAHOO_SERVER", "smtp.mail.yahoo.com")
    SMTP_YAHOO_PORT: int = int(os.getenv("SMTP_YAHOO_PORT", "587"))
    SMTP_YAHOO_USERNAME: str = os.getenv("SMTP_YAHOO_USERNAME", "")
    SMTP_YAHOO_PASSWORD: str = os.getenv("SMTP_YAHOO_PASSWORD", "")
    
    BREVO_API_KEY: str = os.getenv("BREVO_API_KEY", "")
    BREVO_FROM_EMAIL: str = os.getenv("BREVO_FROM_EMAIL", "noreply@yourdomain.com")
    
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_FROM_EMAIL: str = os.getenv("SENDGRID_FROM_EMAIL", "noreply@yourdomain.com")
    
    OTP_EXPIRE_MINUTES: int = int(os.getenv("OTP_EXPIRE_MINUTES", "5"))
    OTP_LENGTH: int = int(os.getenv("OTP_LENGTH", "6"))
    
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "")
    
    FACEBOOK_CLIENT_ID: str = os.getenv("FACEBOOK_CLIENT_ID", "")
    FACEBOOK_CLIENT_SECRET: str = os.getenv("FACEBOOK_CLIENT_SECRET", "")
    FACEBOOK_REDIRECT_URI: str = os.getenv("FACEBOOK_REDIRECT_URI", "")
    
    APPLE_CLIENT_ID: str = os.getenv("APPLE_CLIENT_ID", "")
    APPLE_CLIENT_SECRET: str = os.getenv("APPLE_CLIENT_SECRET", "")
    APPLE_REDIRECT_URI: str = os.getenv("APPLE_REDIRECT_URI", "")
    
    APP_NAME: str = os.getenv("APP_NAME", "Phix HRMS")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    
    def get_base_url():
        base_url = os.getenv("BASE_URL")
        if base_url:
            return base_url
        
        if os.getenv("ENVIRONMENT") == "production" or os.getenv("PRODUCTION") == "true":
            return "https://api.migfastkg.ru"
        
        hostname = os.getenv("HOSTNAME", "")
        if "migfastkg.ru" in hostname or "sutwmdarfs" in hostname:
            return "https://api.migfastkg.ru"
        
        return "http://127.0.0.1:8000"
    
    BASE_URL: str = get_base_url()
    
    # Firebase credentials
    FIREBASE_CREDENTIALS: Optional[Dict[str, Any]] = load_firebase_credentials()
    FIREBASE_PROJECT_ID: str = os.getenv("PROJECT_ID", "phix-864d2")

settings = Settings()
