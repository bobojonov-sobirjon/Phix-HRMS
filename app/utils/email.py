import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..config import settings
import random
import string

def generate_otp(length: int = 6) -> str:
    """Generate random OTP code"""
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(email: str, otp_code: str) -> bool:
    """Send OTP code via email"""
    try:
        print(f"📧 Attempting to send OTP email to: {email}")
        print(f"📧 SMTP Settings: {settings.SMTP_SERVER}:{settings.SMTP_PORT}")
        print(f"📧 Username: {settings.SMTP_USERNAME}")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USERNAME
        msg['To'] = email
        msg['Subject'] = f"Password Reset OTP - {settings.APP_NAME}"
        
        # Email body
        body = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You have requested to reset your password for {settings.APP_NAME}.</p>
            <p>Your OTP code is: <strong>{otp_code}</strong></p>
            <p>This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.</p>
            <p>If you didn't request this, please ignore this email.</p>
            <br>
            <p>Best regards,<br>{settings.APP_NAME} Team</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email with detailed error handling
        print("📧 Connecting to SMTP server...")
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        
        print("📧 Starting TLS...")
        server.starttls()
        
        print("📧 Attempting login...")
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        print("📧 Login successful!")
        
        print("📧 Sending email...")
        text = msg.as_string()
        server.sendmail(settings.SMTP_USERNAME, email, text)
        print("📧 Email sent successfully!")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication failed: {e}")
        print("💡 Solution: Check your Gmail password or use App Password")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False 