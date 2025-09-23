import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# If .env doesn't exist, create it from env.example
if not os.path.exists('.env') and os.path.exists('env.example'):
    import shutil
    shutil.copy('env.example', '.env')
    
    # Reload environment variables
    load_dotenv()

class Settings:
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:0576@localhost:5432/phix_hrms")
    
    # JWT Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 1 kun = 1440 daqiqa
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Email Configuration for OTP
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # Alternative Email Services (for fallback)
    # Outlook/Hotmail
    SMTP_OUTLOOK_SERVER: str = os.getenv("SMTP_OUTLOOK_SERVER", "smtp-mail.outlook.com")
    SMTP_OUTLOOK_PORT: int = int(os.getenv("SMTP_OUTLOOK_PORT", "587"))
    SMTP_OUTLOOK_USERNAME: str = os.getenv("SMTP_OUTLOOK_USERNAME", "")
    SMTP_OUTLOOK_PASSWORD: str = os.getenv("SMTP_OUTLOOK_PASSWORD", "")
    
    # Yahoo
    SMTP_YAHOO_SERVER: str = os.getenv("SMTP_YAHOO_SERVER", "smtp.mail.yahoo.com")
    SMTP_YAHOO_PORT: int = int(os.getenv("SMTP_YAHOO_PORT", "587"))
    SMTP_YAHOO_USERNAME: str = os.getenv("SMTP_YAHOO_USERNAME", "")
    SMTP_YAHOO_PASSWORD: str = os.getenv("SMTP_YAHOO_PASSWORD", "")
    
    # Brevo (Sendinblue) - Free email service - 300 emails/day
    BREVO_API_KEY: str = os.getenv("BREVO_API_KEY", "")
    BREVO_FROM_EMAIL: str = os.getenv("BREVO_FROM_EMAIL", "noreply@yourdomain.com")
    
    # SendGrid (Alternative - 100 emails/day free)
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_FROM_EMAIL: str = os.getenv("SENDGRID_FROM_EMAIL", "noreply@yourdomain.com")
    
    # OTP Configuration
    OTP_EXPIRE_MINUTES: int = int(os.getenv("OTP_EXPIRE_MINUTES", "5"))
    OTP_LENGTH: int = int(os.getenv("OTP_LENGTH", "6"))
    
    # Social Login Configuration
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "")
    
    FACEBOOK_CLIENT_ID: str = os.getenv("FACEBOOK_CLIENT_ID", "")
    FACEBOOK_CLIENT_SECRET: str = os.getenv("FACEBOOK_CLIENT_SECRET", "")
    FACEBOOK_REDIRECT_URI: str = os.getenv("FACEBOOK_REDIRECT_URI", "")
    
    APPLE_CLIENT_ID: str = os.getenv("APPLE_CLIENT_ID", "")
    APPLE_CLIENT_SECRET: str = os.getenv("APPLE_CLIENT_SECRET", "")
    APPLE_REDIRECT_URI: str = os.getenv("APPLE_REDIRECT_URI", "")
    
    # App Configuration
    APP_NAME: str = os.getenv("APP_NAME", "Phix HRMS")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    
    # Auto-detect BASE_URL based on environment
    def get_base_url():
        base_url = os.getenv("BASE_URL")
        if base_url:
            return base_url
        
        # Check if running in production (common indicators)
        if os.getenv("ENVIRONMENT") == "production" or os.getenv("PRODUCTION") == "true":
            return "https://api.migfastkg.ru"
        
        # Check if running on server (not localhost)
        hostname = os.getenv("HOSTNAME", "")
        if "migfastkg.ru" in hostname or "sutwmdarfs" in hostname:
            return "https://api.migfastkg.ru"
        
        # Default to local
        return "http://127.0.0.1:8000"
    
    BASE_URL: str = get_base_url()

settings = Settings()
