"""
Firebase Cloud Messaging (FCM) Push Notification Utility
"""
import firebase_admin
from firebase_admin import credentials, messaging
from typing import List, Optional, Dict, Any
import os
from pathlib import Path


# Global Firebase app instance
_firebase_app = None


def initialize_firebase(service_account_path: Optional[str] = None):
    """
    Initialize Firebase Admin SDK
    
    Args:
        service_account_path: Path to Firebase service account JSON file.
                             If None, will look for it in common locations.
    """
    global _firebase_app
    
    if _firebase_app is not None:
        return _firebase_app
    
    # Try to find service account file
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
                "Firebase service account file not found. "
                "Please provide the path to your Firebase service account JSON file."
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
            initialize_firebase()
        
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
    except messaging.InvalidArgumentError as e:
        print(f"Invalid argument error: {str(e)}")
        return False
    except Exception as e:
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
        initialize_firebase()
    
    if not device_tokens:
        return {
            "success_count": 0,
            "failure_count": 0,
            "results": []
        }
    
    results = {
        "success_count": 0,
        "failure_count": 0,
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
        except messaging.InvalidArgumentError as e:
            results["failure_count"] += 1
            results["results"].append({
                "token": token,
                "success": False,
                "error": f"Invalid argument: {str(e)}"
            })
        except Exception as e:
            results["failure_count"] += 1
            results["results"].append({
                "token": token,
                "success": False,
                "error": str(e)
            })
    
    return results

