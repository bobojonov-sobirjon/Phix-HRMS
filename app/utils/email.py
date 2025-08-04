import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..config import settings
import random
import string
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import socket


# Thread pool executor for async email operations
email_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="email_worker")

def test_smtp_connection(server: str, port: int, timeout: int = 5) -> bool:
    """Test if SMTP connection is possible"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((server, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def send_email_with_retry(email: str, otp_code: str, email_type: str = "registration") -> bool:
    """Send email with multiple fallback methods"""
    
    # Define multiple SMTP configurations to try
    smtp_configs = [
        {
            "name": "Gmail SSL (465)",
            "server": "smtp.gmail.com",
            "port": 465,
            "use_ssl": True,
            "use_tls": False
        },
        {
            "name": "Gmail TLS (587)",
            "server": "smtp.gmail.com", 
            "port": 587,
            "use_ssl": False,
            "use_tls": True
        },
        {
            "name": "Gmail TLS (25)",
            "server": "smtp.gmail.com",
            "port": 25,
            "use_ssl": False,
            "use_tls": True
        }
    ]
    
    for config in smtp_configs:
        print(f"Trying {config['name']}...")
        
        # Test connection first
        if not test_smtp_connection(config['server'], config['port']):
            print(f"Connection test failed for {config['name']}")
            continue
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_USERNAME
            msg['To'] = email
            msg['Subject'] = f"Registration OTP - {settings.APP_NAME}"
            
            # Email body
            body = f"""
            <html>
            <body>
                <h2>Registration Verification</h2>
                <p>Thank you for registering with {settings.APP_NAME}.</p>
                <p>Your verification code is: <strong>{otp_code}</strong></p>
                <p>This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.</p>
                <br>
                <p>Best regards,<br>{settings.APP_NAME} Team</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Create SMTP connection based on config
            if config['use_ssl']:
                server = smtplib.SMTP_SSL(config['server'], config['port'], timeout=10)
            else:
                server = smtplib.SMTP(config['server'], config['port'], timeout=10)
                if config['use_tls']:
                    server.starttls()
            
            # Login and send
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            text = msg.as_string()
            server.sendmail(settings.SMTP_USERNAME, email, text)
            server.quit()
            
            print(f"Email sent successfully using {config['name']}!")
            return True
            
        except Exception as e:
            print(f"Failed with {config['name']}: {e}")
            continue
    
    print("All SMTP configurations failed")
    return False

def generate_otp(length: int = 6) -> str:
    """Generate random OTP code"""
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email_sync(email: str, otp_code: str) -> bool:
    """Send OTP code via email (synchronous version)"""
    try:
        print("=== PASSWORD RESET EMAIL DEBUG ===")
        print(f"Starting password reset email send to: {email}")
        print(f"OTP Code: {otp_code}")
        print(f"SMTP Settings:")
        print(f"  Server: {settings.SMTP_SERVER}")
        print(f"  Port: {settings.SMTP_PORT}")
        print(f"  Username: {settings.SMTP_USERNAME}")
        print(f"  Password: {'*' * len(settings.SMTP_PASSWORD) if settings.SMTP_PASSWORD else 'NOT SET'}")
        
        # Check if email settings are configured
        if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            print("ERROR: SMTP_USERNAME or SMTP_PASSWORD not configured!")
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
        
        print("Attempting to connect to SMTP server...")
        
        # Send email with optimized error handling
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT, timeout=10)
        
        print("SMTP connection established, starting TLS...")
        server.starttls()
        
        print("TLS started, attempting login...")
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        
        print("Login successful, sending email...")
        text = msg.as_string()
        server.sendmail(settings.SMTP_USERNAME, email, text)
        
        print("Password reset email sent successfully!")
        server.quit()
        print("SMTP connection closed")
        print("=== PASSWORD RESET EMAIL COMPLETE ===")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication Error: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP Exception: {e}")
        return False
    except Exception as e:
        print(f"General Exception during password reset email sending: {e}")
        print(f"Exception type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

async def send_otp_email(email: str, otp_code: str) -> bool:
    """Send OTP code via email (async version)"""
    try:
        print(f"Starting async password reset email send to: {email}")
        # Run email sending in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            email_executor, 
            send_otp_email_sync, 
            email, 
            otp_code
        )
        print(f"Async password reset email send completed with result: {result}")
        return result
    except Exception as e:
        print(f"Exception in async password reset email send: {e}")
        print(f"Exception type: {type(e)}")
        import traceback
        print(f"Async traceback: {traceback.format_exc()}")
        return False

def send_registration_otp_email_sync(email: str, otp_code: str) -> bool:
    """Send registration verification OTP code via email (synchronous version)"""
    try:
        print("=== EMAIL SENDING DEBUG ===")
        print(f"Starting email send to: {email}")
        print(f"OTP Code: {otp_code}")
        
        # First try Brevo if configured (free service - 300 emails/day)
        if settings.BREVO_API_KEY and settings.BREVO_FROM_EMAIL:
            print("Trying Brevo first...")
            from .brevo_email import send_email_brevo_sync
            if send_email_brevo_sync(email, otp_code, "registration"):
                return True
            print("Brevo failed, trying SMTP...")
        
        # Fallback to SMTP
        print(f"SMTP Settings:")
        print(f"  Server: {settings.SMTP_SERVER}")
        print(f"  Port: {settings.SMTP_PORT}")
        print(f"  Username: {settings.SMTP_USERNAME}")
        print(f"  Password: {'*' * len(settings.SMTP_PASSWORD) if settings.SMTP_PASSWORD else 'NOT SET'}")
        
        # Check if email settings are configured
        if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            print("ERROR: SMTP_USERNAME or SMTP_PASSWORD not configured!")
            return False
        
        # Use the new retry mechanism with multiple SMTP configurations
        return send_email_with_retry(email, otp_code, "registration")
        
    except Exception as e:
        print(f"General Exception during email sending: {e}")
        print(f"Exception type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

async def send_registration_otp_email(email: str, otp_code: str) -> bool:
    """Send registration verification OTP code via email (async version)"""
    try:
        print(f"Starting async email send to: {email}")
        # Run email sending in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            email_executor, 
            send_registration_otp_email_sync, 
            email, 
            otp_code
        )
        print(f"Async email send completed with result: {result}")
        return result
    except Exception as e:
        print(f"Exception in async email send: {e}")
        print(f"Exception type: {type(e)}")
        import traceback
        print(f"Async traceback: {traceback.format_exc()}")
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

def send_email_with_fallback(email: str, otp_code: str, email_type: str = "registration") -> bool:
    """Send email with fallback to multiple email services"""
    email_services = [
        {
            "name": "Gmail (587)",
            "server": settings.SMTP_SERVER,
            "port": settings.SMTP_PORT,
            "username": settings.SMTP_USERNAME,
            "password": settings.SMTP_PASSWORD
        },
        {
            "name": "Gmail (465)",
            "server": "smtp.gmail.com",
            "port": 465,
            "username": settings.SMTP_USERNAME,
            "password": settings.SMTP_PASSWORD
        },
        {
            "name": "Outlook",
            "server": settings.SMTP_OUTLOOK_SERVER,
            "port": settings.SMTP_OUTLOOK_PORT,
            "username": settings.SMTP_OUTLOOK_USERNAME,
            "password": settings.SMTP_OUTLOOK_PASSWORD
        },
        {
            "name": "Yahoo",
            "server": settings.SMTP_YAHOO_SERVER,
            "port": settings.SMTP_YAHOO_PORT,
            "username": settings.SMTP_YAHOO_USERNAME,
            "password": settings.SMTP_YAHOO_PASSWORD
        }
    ]
    
    for service in email_services:
        if not service["username"] or not service["password"]:
            print(f"Skipping {service['name']} - credentials not configured")
            continue
            
        print(f"Trying {service['name']} email service...")
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = service["username"]
            msg['To'] = email
            
            if email_type == "registration":
                msg['Subject'] = f"Email Verification - {settings.APP_NAME}"
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
            else:
                msg['Subject'] = f"Password Reset OTP - {settings.APP_NAME}"
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
            
            print(f"Connecting to {service['server']}:{service['port']}...")
            
            # Try different connection methods based on port
            if service["port"] == 465:
                # Use SSL for port 465
                import ssl
                server = smtplib.SMTP_SSL(service["server"], service["port"], timeout=10)
                print("Using SSL connection...")
            else:
                # Use STARTTLS for port 587
                server = smtplib.SMTP(service["server"], service["port"], timeout=10)
                print("Starting TLS...")
                server.starttls()
            
            print("Logging in...")
            server.login(service["username"], service["password"])
            
            print("Sending email...")
            text = msg.as_string()
            server.sendmail(service["username"], email, text)
            
            print(f"Email sent successfully via {service['name']}!")
            server.quit()
            return True
            
        except Exception as e:
            print(f"Failed to send via {service['name']}: {e}")
            print(f"Error type: {type(e)}")
            if "Network is unreachable" in str(e):
                print("This appears to be a network connectivity issue")
            continue
    
    print("All email services failed")
    return False

def send_email_simple_smtp(email: str, otp_code: str, email_type: str = "registration") -> bool:
    """Send email with SendGrid first, then fallback to SMTP"""
    try:
        print("=== EMAIL SENDING WITH FALLBACK ===")
        print(f"Attempting to send email to: {email}")
        
        # Try SendGrid first (bypasses SMTP restrictions)
        if settings.SENDGRID_API_KEY:
            print("Trying SendGrid...")
            if send_email_sendgrid(email, otp_code, email_type):
                return True
            else:
                print("SendGrid failed, trying SMTP...")
        
        # Fallback to SMTP if SendGrid fails or not configured
        # Use a simple approach - try different ports and methods
        smtp_servers = [
            {"name": "Gmail SSL (465)", "server": "smtp.gmail.com", "port": 465, "use_ssl": True},
            {"name": "Gmail TLS (587)", "server": "smtp.gmail.com", "port": 587, "use_ssl": False},
            {"name": "Outlook", "server": "smtp-mail.outlook.com", "port": 587, "use_ssl": False},
            {"name": "Yahoo", "server": "smtp.mail.yahoo.com", "port": 587, "use_ssl": False},
        ]
        
        for smtp_config in smtp_servers:
            if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
                print("No SMTP credentials configured")
                continue
                
            print(f"Trying {smtp_config['name']}...")
            
            try:
                # Create message
                msg = MIMEMultipart()
                msg['From'] = settings.SMTP_USERNAME
                msg['To'] = email
                
                if email_type == "registration":
                    msg['Subject'] = f"Email Verification - {settings.APP_NAME}"
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
                else:
                    msg['Subject'] = f"Password Reset OTP - {settings.APP_NAME}"
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
                
                # Connect to SMTP server
                if smtp_config['use_ssl']:
                    server = smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port'], timeout=15)
                    print(f"Connected via SSL to {smtp_config['server']}:{smtp_config['port']}")
                else:
                    server = smtplib.SMTP(smtp_config['server'], smtp_config['port'], timeout=15)
                    print(f"Connected to {smtp_config['server']}:{smtp_config['port']}")
                    server.starttls()
                    print("TLS started")
                
                # Login and send
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                print("Login successful")
                
                text = msg.as_string()
                server.sendmail(settings.SMTP_USERNAME, email, text)
                print(f"Email sent successfully via {smtp_config['name']}!")
                
                server.quit()
                return True
                
            except Exception as e:
                print(f"Failed with {smtp_config['name']}: {e}")
                continue
        
        print("All email methods failed")
        return False
        
    except Exception as e:
        print(f"General error in email sending: {e}")
        return False

def send_email_sendgrid(email: str, otp_code: str, email_type: str = "registration") -> bool:
    """Send email using SendGrid API (bypasses SMTP restrictions)"""
    try:
        print("=== SENDGRID EMAIL SENDING ===")
        print(f"Attempting to send email to: {email}")
        
        if not settings.SENDGRID_API_KEY:
            print("SendGrid API key not configured")
            return False
        
        # Import SendGrid (you'll need to install it: pip install sendgrid)
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
        except ImportError:
            print("SendGrid not installed. Install with: pip install sendgrid")
            return False
        
        # Create email message
        if email_type == "registration":
            subject = f"Email Verification - {settings.APP_NAME}"
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
        else:
            subject = f"Password Reset OTP - {settings.APP_NAME}"
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
        
        # Create SendGrid message
        message = Mail(
            from_email=settings.SENDGRID_FROM_EMAIL,
            to_emails=email,
            subject=subject,
            html_content=body
        )
        
        # Send email
        sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        if response.status_code == 202:
            print("✓ Email sent successfully via SendGrid!")
            return True
        else:
            print(f"✗ SendGrid failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"SendGrid error: {e}")
        return False

def cleanup_email_executor():
    """Cleanup email executor on application shutdown"""
    email_executor.shutdown(wait=True) 