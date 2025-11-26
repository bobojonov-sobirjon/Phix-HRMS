"""
Firebase Cloud Messaging (FCM) Push Notification Utility
"""
import firebase_admin
from firebase_admin import credentials, messaging
from typing import List, Optional, Dict, Any
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# Global Firebase app instance
_firebase_app = None


def initialize_firebase(service_account_path: Optional[str] = None):
    """
    Initialize Firebase Admin SDK
    
    Args:
        service_account_path: Path to Firebase service account JSON file.
                             If None, will try to use environment variables or look for it in common locations.
    """
    global _firebase_app
    
    if _firebase_app is not None:
        return _firebase_app
    
    # First, try to use environment variables (without FIREBASE_ prefix, as in main.py)
    firebase_type = os.getenv("TYPE")
    firebase_project_id = os.getenv("PROJECT_ID")
    firebase_private_key_id = os.getenv("PRIVATE_KEY_ID")
    firebase_private_key = os.getenv("PRIVATE_KEY")
    firebase_client_email = os.getenv("CLIENT_EMAIL")
    firebase_client_id = os.getenv("CLIENT_ID")
    firebase_auth_uri = os.getenv("AUTH_URI")
    firebase_token_uri = os.getenv("TOKEN_URI")
    firebase_auth_provider_cert_url = os.getenv("AUTH_PROVIDER_CERT_URL")
    firebase_client_cert_url = os.getenv("CLIENT_CERT_URL")
    firebase_universe_domain = os.getenv("UNIVERSE_DOMAIN")
    
    # Debug log removed for production; uncomment if low-level Firebase env debugging is needed
    # print(f"DEBUG: Firebase env vars - Private Key: {'Found' if firebase_private_key else 'Not found'}, Client Email: {'Found' if firebase_client_email else 'Not found'}")
    
    if firebase_private_key and firebase_client_email:
        # Use environment variables to create credentials
        try:
            # Extract project_id from client_email if not provided
            # Format: service-account@project-id.iam.gserviceaccount.com
            project_id = firebase_project_id
            if not project_id and firebase_client_email and "@" in firebase_client_email:
                try:
                    # Extract project_id from email: service-account@project-id.iam.gserviceaccount.com
                    email_parts = firebase_client_email.split("@")
                    if len(email_parts) > 1:
                        domain_parts = email_parts[1].split(".")
                        if len(domain_parts) > 0:
                            project_id = domain_parts[0]
                except Exception:
                    project_id = None
            
            # Build service account info dictionary
            service_account_info = {
                "type": firebase_type or "service_account",
                "project_id": project_id or "",
                "private_key_id": firebase_private_key_id or "",
                "private_key": firebase_private_key.replace("\\n", "\n"),  # Handle escaped newlines
                "client_email": firebase_client_email,
                "client_id": firebase_client_id or "",
                "auth_uri": firebase_auth_uri or "https://accounts.google.com/o/oauth2/auth",
                "token_uri": firebase_token_uri or "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": firebase_auth_provider_cert_url or "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": firebase_client_cert_url or "",
                "universe_domain": firebase_universe_domain or "googleapis.com"
            }
            
            cred = credentials.Certificate(service_account_info)
            _firebase_app = firebase_admin.initialize_app(cred)
            return _firebase_app
        except Exception as e:
            print(f"WARNING: Failed to initialize Firebase using environment variables: {str(e)}")
            # Fall through to try file-based initialization
    
    # If environment variables not available, try to find service account file
    if service_account_path is None:
        # Check common locations
        possible_paths = [
            "phix-864d2-firebase-adminsdk-fbsvc-1f428184f0.json",
            "firebase-service-account.json",
            os.path.join(os.path.dirname(__file__), "..", "..", "phix-864d2-firebase-adminsdk-fbsvc-1f428184f0.json"),
            os.path.join(os.path.dirname(__file__), "..", "..", "firebase-service-account.json"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                service_account_path = path
                break
        
        if service_account_path is None:
            raise FileNotFoundError(
                "Firebase service account file not found and environment variables not set. "
                "Please provide either Firebase environment variables or the path to your Firebase service account JSON file."
            )
    
    if not os.path.exists(service_account_path):
        raise FileNotFoundError(f"Firebase service account file not found at: {service_account_path}")
    
    try:
        cred = credentials.Certificate(service_account_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        return _firebase_app
    except Exception as e:
        raise Exception(f"Failed to initialize Firebase: {str(e)}")


def send_push_notification(
    device_token: str,
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None,
    image_url: Optional[str] = None,
    sound: str = "default"
) -> bool:
    """
    Send a push notification to a single device
    
    Args:
        device_token: FCM device token
        title: Notification title
        body: Notification body text
        data: Optional dictionary of key-value pairs for notification data
        image_url: Optional URL for notification image
        sound: Notification sound (default: "default")
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        # Ensure Firebase is initialized
        if _firebase_app is None:
            try:
                initialize_firebase()
            except FileNotFoundError as e:
                print(f"WARNING: Cannot send push notification - Firebase not initialized: {str(e)}")
                return False
            except Exception as e:
                print(f"WARNING: Cannot send push notification - Firebase initialization failed: {str(e)}")
                return False
        
        # Build notification
        notification = messaging.Notification(
            title=title,
            body=body,
            image=image_url
        )
        
        # Build Android config
        android_config = messaging.AndroidConfig(
            priority="high",
            notification=messaging.AndroidNotification(
                sound=sound,
                priority="high"
            )
        )
        
        # Build APNS (iOS) config
        apns_config = messaging.APNSConfig(
            headers={"apns-priority": "10"},
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    sound=sound,
                    badge=1
                )
            )
        )
        
        # Create message
        message = messaging.Message(
            notification=notification,
            data=data or {},
            token=device_token,
            android=android_config,
            apns=apns_config
        )
        
        # Send message
        response = messaging.send(message)
        print(f"Successfully sent message: {response}")
        return True
        
    except messaging.UnregisteredError:
        print(f"Device token is unregistered: {device_token}")
        return False
    except Exception as e:
        # Covers invalid arguments and other Firebase errors for SDK versions
        # where messaging.InvalidArgumentError is not available
        print(f"Error sending push notification: {str(e)}")
        return False


def send_push_notification_multiple(
    device_tokens: List[str],
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None,
    image_url: Optional[str] = None,
    sound: str = "default"
) -> Dict[str, Any]:
    """
    Send push notifications to multiple devices
    Uses individual sends (fallback from batch/multicast due to API issues)
    
    Args:
        device_tokens: List of FCM device tokens
        title: Notification title
        body: Notification body text
        data: Optional dictionary of key-value pairs for notification data
        image_url: Optional URL for notification image
        sound: Notification sound (default: "default")
    
    Returns:
        Dict with success_count, failure_count, and results
    """
    # Ensure Firebase is initialized
    if _firebase_app is None:
        try:
            initialize_firebase()
        except FileNotFoundError as e:
            # If Firebase file not found, return skipped results instead of failure
            print(f"WARNING: Cannot send push notifications - Firebase not initialized: {str(e)}")
            return {
                "success_count": 0,
                "failure_count": 0,
                "skipped_count": len(device_tokens),
                "results": [{"token": token, "success": False, "skipped": True, "error": "Firebase not initialized"} for token in device_tokens]
            }
        except Exception as e:
            # Other initialization errors
            print(f"WARNING: Cannot send push notifications - Firebase initialization failed: {str(e)}")
            return {
                "success_count": 0,
                "failure_count": 0,
                "skipped_count": len(device_tokens),
                "results": [{"token": token, "success": False, "skipped": True, "error": f"Firebase init error: {str(e)}"} for token in device_tokens]
            }
    
    if not device_tokens:
        return {
            "success_count": 0,
            "failure_count": 0,
            "results": []
        }
    
    results = {
        "success_count": 0,
        "failure_count": 0,
        "skipped_count": 0,
        "results": []
    }
    
    # Build notification
    notification = messaging.Notification(
        title=title,
        body=body,
        image=image_url
    )
    
    # Build Android config
    android_config = messaging.AndroidConfig(
        priority="high",
        notification=messaging.AndroidNotification(
            sound=sound,
            priority="high"
        )
    )
    
    # Build APNS (iOS) config
    apns_config = messaging.APNSConfig(
        headers={"apns-priority": "10"},
        payload=messaging.APNSPayload(
            aps=messaging.Aps(
                sound=sound,
                badge=1
            )
        )
    )
    
    # Send to each device individually (more reliable than batch)
    for token in device_tokens:
        try:
            # Create message for this device
            message = messaging.Message(
                notification=notification,
                data=data or {},
                token=token,
                android=android_config,
                apns=apns_config
            )
            
            # Send message
            response = messaging.send(message)
            results["success_count"] += 1
            results["results"].append({
                "token": token,
                "success": True,
                "message_id": response
            })
            
        except messaging.UnregisteredError:
            results["failure_count"] += 1
            results["results"].append({
                "token": token,
                "success": False,
                "error": "Device token is unregistered"
            })
        except Exception as e:
            # Covers invalid arguments and other Firebase errors for SDK versions
            # where messaging.InvalidArgumentError is not available
            results["failure_count"] += 1
            results["results"].append({
                "token": token,
                "success": False,
                "error": str(e)
            })
    
    return results

