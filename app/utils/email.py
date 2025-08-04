import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..config import settings
import random
import string
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional


# Thread pool executor for async email operations
email_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="email_worker")

def generate_otp(length: int = 6) -> str:
    """Generate random OTP code"""
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email_sync(email: str, otp_code: str) -> bool:
    """Send OTP code via email (synchronous version)"""
    try:
        # Check if email settings are configured
        if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            return False
        
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
        
        # Send email with optimized error handling
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT, timeout=10)
        
        server.starttls()
        
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        
        text = msg.as_string()
        server.sendmail(settings.SMTP_USERNAME, email, text)
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        return False
    except smtplib.SMTPException as e:
        return False
    except Exception as e:
        return False

async def send_otp_email(email: str, otp_code: str) -> bool:
    """Send OTP code via email (async version)"""
    try:
        # Run email sending in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            email_executor, 
            send_otp_email_sync, 
            email, 
            otp_code
        )
        return result
    except Exception as e:
        return False

def send_registration_otp_email_sync(email: str, otp_code: str) -> bool:
    """Send registration verification OTP code via email (synchronous version)"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USERNAME
        msg['To'] = email
        msg['Subject'] = f"Email Verification - {settings.APP_NAME}"
        
        # Email body
        body = f"""
        <html>
        <body>
            <h2>Email Verification</h2>
            <p>Thank you for registering with {settings.APP_NAME}!</p>
            <p>Please verify your email address by entering the following verification code:</p>
            <p><strong>{otp_code}</strong></p>
            <p>This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.</p>
            <p>If you didn't create an account, please ignore this email.</p>
            <br>
            <p>Best regards,<br>{settings.APP_NAME} Team</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email with optimized error handling
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT, timeout=10)
        
        server.starttls()
        
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        
        text = msg.as_string()
        server.sendmail(settings.SMTP_USERNAME, email, text)
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        return False
    except smtplib.SMTPException as e:
        return False
    except Exception as e:
        return False

async def send_registration_otp_email(email: str, otp_code: str) -> bool:
    """Send registration verification OTP code via email (async version)"""
    try:
        # Run email sending in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            email_executor, 
            send_registration_otp_email_sync, 
            email, 
            otp_code
        )
        return result
    except Exception as e:
        return False

async def send_otp_email_batch(emails_and_otps: list) -> dict:
    """Send OTP emails to multiple recipients concurrently"""
    results = {}
    
    # Create tasks for all emails
    tasks = []
    for email, otp_code in emails_and_otps:
        task = asyncio.create_task(send_otp_email(email, otp_code))
        tasks.append((email, task))
    
    # Wait for all emails to complete
    for email, task in tasks:
        try:
            success = await task
            results[email] = success
        except Exception as e:
            results[email] = False
    
    return results

def cleanup_email_executor():
    """Cleanup email executor on application shutdown"""
    email_executor.shutdown(wait=True) 