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

def send_corporate_verification_email_sync(email: str, otp_code: str) -> bool:
    """Send corporate profile verification OTP code via email (synchronous version)"""
    try:
        print("=== CORPORATE VERIFICATION EMAIL DEBUG ===")
        print(f"Starting corporate verification email send to: {email}")
        print(f"OTP Code: {otp_code}")
        
        # First try Brevo if configured (free service - 300 emails/day)
        if settings.BREVO_API_KEY and settings.BREVO_FROM_EMAIL:
            print("Trying Brevo first...")
            from .brevo_email import send_email_brevo_sync
            if send_email_brevo_sync(email, otp_code, "corporate_verification"):
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
        return send_email_with_retry(email, otp_code, "corporate_verification")
        
    except Exception as e:
        print(f"General Exception during corporate verification email sending: {e}")
        print(f"Exception type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

async def send_corporate_verification_email(email: str, otp_code: str) -> bool:
    """Send corporate profile verification OTP code via email (async version)"""
    try:
        print(f"Starting async corporate verification email send to: {email}")
        # Run email sending in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            email_executor, 
            send_corporate_verification_email_sync, 
            email, 
            otp_code
        )
        print(f"Async corporate verification email send completed with result: {result}")
        return result
    except Exception as e:
        print(f"Exception in async corporate verification email send: {e}")
        print(f"Exception type: {type(e)}")
        import traceback
        print(f"Async traceback: {traceback.format_exc()}")
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
            # Create message - Use MIMEText instead of MIMEMultipart to avoid any header issues
            subject = f"Registration OTP - {settings.APP_NAME}" if email_type != "corporate_verification" else f"Corporate Profile Verification - {settings.APP_NAME}"
            
            if email_type == "corporate_verification":
                body = f"""
                <html>
                <body>
                    <h2>Corporate Profile Verification</h2>
                    <p>Thank you for creating a corporate profile with {settings.APP_NAME}.</p>
                    <p>Your verification code is: <strong>{otp_code}</strong></p>
                    <p>This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.</p>
                    <p>Please use this code to verify your corporate profile.</p>
                    <br>
                    <p>Best regards,<br>{settings.APP_NAME} Team</p>
                </body>
                </html>
                """
            else:
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
            
            # Create simple MIMEText message to avoid any MIME header issues
            msg = MIMEText(body, 'html')
            msg['From'] = settings.SMTP_USERNAME
            msg['To'] = email
            msg['Subject'] = subject
            
            # Create SMTP connection based on config
            if config['use_ssl']:
                server = smtplib.SMTP_SSL(config['server'], config['port'], timeout=10)
            else:
                server = smtplib.SMTP(config['server'], config['port'], timeout=10)
                if config['use_tls']:
                    server.starttls()
            
            # Login and send
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            
            # Debug: Print the actual email content to see what's being sent
            text = msg.as_string()
            print(f"=== EMAIL CONTENT DEBUG ===")
            print(f"Email headers and content:")
            print(text)
            print("=== END EMAIL CONTENT DEBUG ===")
            
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

async def send_team_invitation_email(email: str, company_name: str, inviter_name: str, role: str) -> bool:
    """Send team invitation email to a user"""
    try:
        print(f"=== SENDING TEAM INVITATION EMAIL ===")
        print(f"To: {email}")
        print(f"Company: {company_name}")
        print(f"Inviter: {inviter_name}")
        print(f"Role: {role}")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USERNAME
        msg['To'] = email
        msg['Subject'] = f"Team Invitation - {company_name}"
        
        # Email body
        body = f"""
        <html>
        <body>
            <h2>Team Invitation</h2>
            <p>Hello!</p>
            <p>You have been invited by <strong>{inviter_name}</strong> to join the team at <strong>{company_name}</strong>.</p>
            <p>Your assigned role will be: <strong>{role}</strong></p>
            <p>Please log in to your account to accept or reject this invitation.</p>
            <br>
            <p>Best regards,<br>{company_name} Team</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Try to send using available methods
        return await asyncio.get_event_loop().run_in_executor(
            email_executor, 
            lambda: send_email_with_retry(email, "", "team_invitation")
        )
        
    except Exception as e:
        print(f"Error sending team invitation email: {e}")
        return False


def send_team_invitation_email_sync(email: str, company_name: str, inviter_name: str, role: str):
    """Send team invitation email (sync version)"""
    try:
        subject = f"Team Invitation from {company_name}"
        
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Team Invitation</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Team Invitation</h1>
                </div>
                <div class="content">
                    <h2>Hello!</h2>
                    <p><strong>{inviter_name}</strong> has invited you to join <strong>{company_name}</strong> as a <strong>{role}</strong>.</p>
                    <p>Please log in to your account to accept or decline this invitation.</p>
                    <p>If you have any questions, please contact the person who invited you.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from Phix HRMS.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send email
        send_email_with_retry(
            email=email,
            subject=subject,
            html_content=html_content,
            email_type="team_invitation"
        )
        
        print(f"Team invitation email sent successfully to {email}")
        
    except Exception as e:
        print(f"Error sending team invitation email to {email}: {e}")
        raise e


async def send_team_invitation_email(email: str, company_name: str, inviter_name: str, role: str):
    """Send team invitation email"""
    try:
        # Run the sync function in a thread pool
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            await loop.run_in_executor(
                executor, 
                send_team_invitation_email_sync, 
                email, 
                company_name, 
                inviter_name, 
                role
            )
    except Exception as e:
        print(f"Error sending team invitation email: {e}")
        raise e


def send_team_invitation_email_direct(email: str, company_name: str, inviter_name: str, role: str) -> bool:
    """Send team invitation email directly using SMTP"""
    try:
        subject = f"Job Invitation - {company_name}"
        
        # Create HTML content in English with Accept/Cancel buttons
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Job Invitation</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 24px; color: white; text-decoration: none; border-radius: 5px; margin: 10px; font-weight: bold; }}
                .accept-btn {{ background-color: #4CAF50; }}
                .cancel-btn {{ background-color: #f44336; }}
                .button-container {{ text-align: center; margin: 30px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Job Invitation</h1>
                </div>
                <div class="content">
                    <h2>Hello!</h2>
                    <p><strong>{inviter_name}</strong> has invited you to join <strong>{company_name}</strong> as a <strong>{role}</strong>.</p>
                    <p>Please click one of the buttons below to accept or decline this invitation.</p>
                    <p>If you have any questions, please contact the person who invited you.</p>
                    
                    <div class="button-container">
                        <a href="{{base_url}}/api/v1/team-members/accept-invitation?token={{accept_token}}" class="button accept-btn">Accept</a>
                        <a href="{{base_url}}/api/v1/team-members/reject-invitation?token={{reject_token}}" class="button cancel-btn">Cancel</a>
                    </div>
                </div>
                <div class="footer">
                    <p>This message was sent automatically by Phix HRMS system.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Use existing SMTP configurations
        smtp_configs = [
            {
                "name": "Gmail SSL (465)",
                "server": "smtp.gmail.com",
                "port": 465,
                "use_ssl": True,
                "username": settings.SMTP_USERNAME,
                "password": settings.SMTP_PASSWORD
            },
            {
                "name": "Gmail TLS (587)",
                "server": "smtp.gmail.com",
                "port": 587,
                "use_ssl": False,
                "username": settings.SMTP_USERNAME,
                "password": settings.SMTP_PASSWORD
            },
            {
                "name": "Outlook",
                "server": settings.SMTP_OUTLOOK_SERVER,
                "port": settings.SMTP_OUTLOOK_PORT,
                "use_ssl": False,
                "username": settings.SMTP_OUTLOOK_USERNAME,
                "password": settings.SMTP_OUTLOOK_PASSWORD
            },
            {
                "name": "Yahoo",
                "server": settings.SMTP_YAHOO_SERVER,
                "port": settings.SMTP_YAHOO_PORT,
                "use_ssl": False,
                "username": settings.SMTP_YAHOO_USERNAME,
                "password": settings.SMTP_YAHOO_PASSWORD
            }
        ]
        
        # Try each SMTP configuration
        for config in smtp_configs:
            if not config["username"] or not config["password"]:
                continue
                
            try:
                print(f"Trying {config['name']}...")
                
                # Create message
                msg = MIMEMultipart()
                msg['From'] = config["username"]
                msg['To'] = email
                msg['Subject'] = subject
                
                msg.attach(MIMEText(html_content, 'html'))
                
                # Connect and send
                if config["use_ssl"]:
                    server = smtplib.SMTP_SSL(config["server"], config["port"])
                else:
                    server = smtplib.SMTP(config["server"], config["port"])
                    server.starttls()
                
                server.login(config["username"], config["password"])
                text = msg.as_string()
                server.sendmail(config["username"], email, text)
                server.quit()
                
                print(f"Team invitation email sent successfully to {email} using {config['name']}")
                return True
                
            except Exception as e:
                print(f"Failed with {config['name']}: {e}")
                continue
        
        print(f"All SMTP methods failed for team invitation email to {email}")
        return False
        
    except Exception as e:
        print(f"Error sending team invitation email to {email}: {e}")
        return False


async def send_team_invitation_email_new(email: str, company_name: str, inviter_name: str, role: str, team_member_id: int = None):
    """Send team invitation email (new async version) with Accept/Cancel buttons"""
    try:
        # Run the direct function in a thread pool
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            await loop.run_in_executor(
                executor, 
                send_team_invitation_email_with_buttons, 
                email, 
                company_name, 
                inviter_name, 
                role,
                team_member_id
            )
    except Exception as e:
        print(f"Error sending team invitation email: {e}")
        raise e


def send_team_invitation_email_with_buttons(email: str, company_name: str, inviter_name: str, role: str, team_member_id: int = None) -> bool:
    """Send team invitation email with Accept/Cancel buttons"""
    try:
        subject = f"Job Invitation - {company_name}"
        
        # Create HTML content with Accept/Cancel buttons
        base_url = settings.BASE_URL.rstrip('/')
        accept_url = f"{base_url}/api/v1/team-members/accept-invitation?team_member_id={team_member_id}" if team_member_id else "#"
        reject_url = f"{base_url}/api/v1/team-members/reject-invitation?team_member_id={team_member_id}" if team_member_id else "#"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Team Invitation - {company_name}</title>
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    line-height: 1.6; 
                    color: #333; 
                    margin: 0; 
                    padding: 0; 
                    background-color: #f8f9fa;
                }}
                .email-container {{ 
                    max-width: 600px; 
                    margin: 20px auto; 
                    background: white; 
                    border-radius: 12px; 
                    overflow: hidden; 
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                }}
                .header {{ 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; 
                    padding: 30px 20px; 
                    text-align: center;
                }}
                .header h1 {{ 
                    margin: 0; 
                    font-size: 28px; 
                    font-weight: 300;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
                }}
                .content {{ 
                    padding: 40px 30px; 
                    background: white;
                }}
                .greeting {{ 
                    font-size: 18px; 
                    color: #2c3e50; 
                    margin-bottom: 20px;
                }}
                .invitation-text {{ 
                    font-size: 16px; 
                    color: #34495e; 
                    margin-bottom: 25px;
                    line-height: 1.7;
                }}
                .role-badge {{ 
                    display: inline-block; 
                    background: linear-gradient(45deg, #3498db, #2980b9);
                    color: white; 
                    padding: 8px 16px; 
                    border-radius: 20px; 
                    font-size: 14px; 
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                .button-container {{ 
                    text-align: center; 
                    margin: 40px 0; 
                }}
                .button {{ 
                    display: inline-block; 
                    padding: 16px 32px; 
                    color: white !important; 
                    text-decoration: none; 
                    border-radius: 8px; 
                    margin: 8px 12px; 
                    font-weight: 600; 
                    font-size: 16px;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                .accept-btn {{ 
                    background: linear-gradient(45deg, #27ae60, #2ecc71);
                    color: white !important;
                }}
                .accept-btn:hover {{ 
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(46, 204, 113, 0.4);
                    color: white !important;
                }}
                .cancel-btn {{ 
                    background: linear-gradient(45deg, #e74c3c, #c0392b);
                    color: white !important;
                }}
                .cancel-btn:hover {{ 
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(231, 76, 60, 0.4);
                    color: white !important;
                }}
                .footer {{ 
                    text-align: center; 
                    padding: 25px; 
                    background: #ecf0f1; 
                    color: #7f8c8d; 
                    font-size: 13px;
                }}
                .company-name {{ 
                    color: #2c3e50; 
                    font-weight: 600;
                }}
                .inviter-name {{ 
                    color: #8e44ad; 
                    font-weight: 600;
                }}
                .divider {{ 
                    height: 1px; 
                    background: linear-gradient(to right, transparent, #bdc3c7, transparent); 
                    margin: 30px 0;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>🎉 Team Invitation</h1>
                </div>
                <div class="content">
                    <div class="greeting">Hello there!</div>
                    
                    <div class="invitation-text">
                        <span class="inviter-name">{inviter_name}</span> has invited you to join 
                        <span class="company-name">{company_name}</span> as a 
                        <span class="role-badge">{role}</span>
                    </div>
                    
                    <div class="invitation-text">
                        Please click one of the buttons below to accept or decline this invitation. 
                        This will help us manage our team effectively.
                    </div>
                    
                    <div class="divider"></div>
                    
                    <div class="button-container">
                        <a href="{accept_url}" class="button accept-btn">✅ Accept Invitation</a>
                        <a href="{reject_url}" class="button cancel-btn">❌ Decline</a>
                    </div>
                    
                    <div class="invitation-text" style="font-size: 14px; color: #7f8c8d; margin-top: 30px;">
                        If you have any questions, please contact <span class="inviter-name">{inviter_name}</span> directly.
                    </div>
                </div>
                <div class="footer">
                    <p>This message was sent automatically by <strong>Phix HRMS</strong> system.</p>
                    <p>Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Use existing SMTP configurations
        smtp_configs = [
            {
                "name": "Gmail SSL (465)",
                "server": "smtp.gmail.com",
                "port": 465,
                "use_ssl": True,
                "username": settings.SMTP_USERNAME,
                "password": settings.SMTP_PASSWORD
            },
            {
                "name": "Gmail TLS (587)",
                "server": "smtp.gmail.com",
                "port": 587,
                "use_ssl": False,
                "username": settings.SMTP_USERNAME,
                "password": settings.SMTP_PASSWORD
            }
        ]
        
        # Try each SMTP configuration
        for config in smtp_configs:
            if not config["username"] or not config["password"]:
                continue
                
            try:
                print(f"Trying {config['name']}...")
                
                # Create message
                msg = MIMEMultipart()
                msg['From'] = config["username"]
                msg['To'] = email
                msg['Subject'] = subject
                
                msg.attach(MIMEText(html_content, 'html'))
                
                # Connect and send
                if config["use_ssl"]:
                    server = smtplib.SMTP_SSL(config["server"], config["port"])
                else:
                    server = smtplib.SMTP(config["server"], config["port"])
                    server.starttls()
                
                server.login(config["username"], config["password"])
                text = msg.as_string()
                server.sendmail(config["username"], email, text)
                server.quit()
                
                print(f"Team invitation email sent successfully to {email} using {config['name']}")
                return True
                
            except Exception as e:
                print(f"Failed with {config['name']}: {e}")
                continue
        
        print(f"All SMTP methods failed for team invitation email to {email}")
        return False
        
    except Exception as e:
        print(f"Error sending team invitation email to {email}: {e}")
        return False


def cleanup_email_executor():
    """Cleanup email executor on application shutdown"""
    email_executor.shutdown(wait=True) 