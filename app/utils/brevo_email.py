"""
Brevo (Sendinblue) Email Utility
Free email service - 300 emails/day
"""
import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from ..config import settings
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

# Thread pool executor for async email operations
brevo_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="brevo_worker")

def send_email_brevo_sync(email: str, otp_code: str, email_type: str = "registration") -> bool:
    """Send email using Brevo API (synchronous version)"""
    try:
        print("=== BREVO EMAIL DEBUG ===")
        print(f"Brevo API Key: {'*' * 20 if settings.BREVO_API_KEY else 'NOT SET'}")
        print(f"From Email: {settings.BREVO_FROM_EMAIL}")
        print(f"To Email: {email}")
        print(f"OTP Code: {otp_code}")
        print(f"Email Type: {email_type}")
        print("========================")
        
        # Check if Brevo is configured
        if not settings.BREVO_API_KEY:
            print("ERROR: BREVO_API_KEY not configured!")
            return False
        
        if not settings.BREVO_FROM_EMAIL:
            print("ERROR: BREVO_FROM_EMAIL not configured!")
            return False
        
        # Configure API key
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = settings.BREVO_API_KEY
        
        # Create API instance
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
        
        # Create email content based on type
        if email_type == "registration":
            subject = f"Registration Verification - {settings.APP_NAME}"
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                    <h2 style="color: #333; text-align: center;">Registration Verification</h2>
                    <p>Thank you for registering with <strong>{settings.APP_NAME}</strong>!</p>
                    <p>Please verify your email address by entering the following verification code:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <div style="background-color: #007bff; color: white; padding: 15px; border-radius: 8px; display: inline-block; font-size: 24px; font-weight: bold;">
                            {otp_code}
                        </div>
                    </div>
                    <p><strong>This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.</strong></p>
                    <p style="color: #666; font-size: 14px;">If you didn't create an account, please ignore this email.</p>
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                    <p style="text-align: center; color: #666;">Best regards,<br><strong>{settings.APP_NAME} Team</strong></p>
                </div>
            </body>
            </html>
            """
        elif email_type == "password_reset":
            subject = f"Password Reset - {settings.APP_NAME}"
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                    <h2 style="color: #333; text-align: center;">Password Reset Request</h2>
                    <p>You have requested to reset your password for <strong>{settings.APP_NAME}</strong>.</p>
                    <p>Your verification code is:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <div style="background-color: #dc3545; color: white; padding: 15px; border-radius: 8px; display: inline-block; font-size: 24px; font-weight: bold;">
                            {otp_code}
                        </div>
                    </div>
                    <p><strong>This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.</strong></p>
                    <p style="color: #666; font-size: 14px;">If you didn't request this, please ignore this email.</p>
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                    <p style="text-align: center; color: #666;">Best regards,<br><strong>{settings.APP_NAME} Team</strong></p>
                </div>
            </body>
            </html>
            """
        elif email_type == "corporate_verification":
            subject = f"Corporate Profile Verification - {settings.APP_NAME}"
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                    <h2 style="color: #333; text-align: center;">Corporate Profile Verification</h2>
                    <p>Thank you for creating a corporate profile with <strong>{settings.APP_NAME}</strong>!</p>
                    <p>Please verify your corporate profile by entering the following verification code:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <div style="background-color: #6f42c1; color: white; padding: 15px; border-radius: 8px; display: inline-block; font-size: 24px; font-weight: bold;">
                            {otp_code}
                        </div>
                    </div>
                    <p><strong>This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.</strong></p>
                    <p style="color: #666; font-size: 14px;">Please use this code to verify your corporate profile and activate it.</p>
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                    <p style="text-align: center; color: #666;">Best regards,<br><strong>{settings.APP_NAME} Team</strong></p>
                </div>
            </body>
            </html>
            """
        elif email_type == "team_invitation":
            # Extract data from html_content for team invitation
            import re
            company_match = re.search(r'<strong>([^<]+)</strong> has invited you to join <strong>([^<]+)</strong> as a <strong>([^<]+)</strong>', html_content)
            if company_match:
                inviter_name = company_match.group(1)
                company_name = company_match.group(2)
                role = company_match.group(3)
            else:
                inviter_name = "Team Member"
                company_name = "Company"
                role = "Member"
            
            subject = f"Team Invitation from {company_name}"
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                    <h2 style="color: #333; text-align: center;">Team Invitation</h2>
                    <p>Hello!</p>
                    <p><strong>{inviter_name}</strong> has invited you to join <strong>{company_name}</strong> as a <strong>{role}</strong>.</p>
                    <p>Please log in to your account to accept or decline this invitation.</p>
                    <p>If you have any questions, please contact the person who invited you.</p>
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                    <p style="text-align: center; color: #666;">Best regards,<br><strong>{settings.APP_NAME} Team</strong></p>
                </div>
            </body>
            </html>
            """
        else:
            subject = f"Verification Code - {settings.APP_NAME}"
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                    <h2 style="color: #333; text-align: center;">Verification Code</h2>
                    <p>Your verification code is:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <div style="background-color: #28a745; color: white; padding: 15px; border-radius: 8px; display: inline-block; font-size: 24px; font-weight: bold;">
                            {otp_code}
                        </div>
                    </div>
                    <p><strong>This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.</strong></p>
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                    <p style="text-align: center; color: #666;">Best regards,<br><strong>{settings.APP_NAME} Team</strong></p>
                </div>
            </body>
            </html>
            """
        
        # Create send email object
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": email}],
            sender={"email": settings.BREVO_FROM_EMAIL},
            subject=subject,
            html_content=html_content
        )
        
        print("Sending email via Brevo API...")
        
        # Send email
        response = api_instance.send_transac_email(send_smtp_email)
        
        print(f"Brevo Response: {response}")
        
        if response and hasattr(response, 'message_id'):
            print("✅ Email sent successfully via Brevo!")
            return True
        else:
            print(f"❌ Brevo API error: {response}")
            return False
            
    except ApiException as e:
        print(f"❌ Brevo API Exception: {e}")
        return False
    except Exception as e:
        print(f"❌ Brevo email sending failed: {e}")
        print(f"Exception type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

async def send_email_brevo_async(email: str, otp_code: str, email_type: str = "registration") -> bool:
    """Send email using Brevo API (async version)"""
    try:
        print(f"Starting async Brevo email send to: {email}")
        # Run email sending in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            brevo_executor, 
            send_email_brevo_sync, 
            email, 
            otp_code,
            email_type
        )
        print(f"Async Brevo email send completed with result: {result}")
        return result
    except Exception as e:
        print(f"Exception in async Brevo email send: {e}")
        print(f"Exception type: {type(e)}")
        import traceback
        print(f"Async traceback: {traceback.format_exc()}")
        return False

def test_brevo_connection() -> bool:
    """Test Brevo API connection"""
    try:
        if not settings.BREVO_API_KEY:
            print("❌ BREVO_API_KEY not configured")
            return False
        
        # Configure API key
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = settings.BREVO_API_KEY
        
        # Create API instance
        api_instance = sib_api_v3_sdk.AccountApi(sib_api_v3_sdk.ApiClient(configuration))
        
        # Test API key by getting account info
        response = api_instance.get_account()
        print(f"✅ Brevo API connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Brevo API connection failed: {e}")
        return False

def cleanup_brevo_executor():
    """Clean up Brevo thread pool executor"""
    brevo_executor.shutdown(wait=True) 