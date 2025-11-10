import json
import os
from typing import Dict, Any, Optional

from app.utils.logging_config import setup_logging
from app.utils.retry_handler import retry_with_backoff
from app.utils.circuit_breaker import circuit_breaker

logger = setup_logging("push-sender")

try:
    from firebase_admin import credentials, initialize_app, messaging
    FCM_AVAILABLE = True
except ImportError:
    FCM_AVAILABLE = False
    logger.warning("Firebase Admin SDK not available. Push notifications will be simulated.")

class PushSender:
    """This class handles sending push notifications via Firebase Cloud Messaging."""
    
    def __init__(self, credentials_file: str):
        self.credentials_file = credentials_file
        self.app = None
        self.initialized = False
        
        if FCM_AVAILABLE:
            self._initialize_fcm()
        else:
            logger.warning("FCM not available, running in simulation mode")
    
    def _initialize_fcm(self):
        """Initializes the Firebase Admin SDK."""
        try:
            if not os.path.exists(self.credentials_file):
                logger.warning(f"FCM credentials file not found: {self.credentials_file}")
                return
            
            cred = credentials.Certificate(self.credentials_file)
            self.app = initialize_app(cred)
            self.initialized = True
            logger.info("Firebase Admin SDK initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize FCM: {str(e)}")
    
    @retry_with_backoff(max_retries=3, base_delay=2.0, exceptions=(Exception,))
    @circuit_breaker(failure_threshold=5, recovery_timeout=60, expected_exception=Exception)
    def send_push(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image_url: Optional[str] = None
    ) -> bool:
        """
        Sends a push notification with retry and circuit breaker protection.
        
        Args:
            device_token: The FCM device token.
            title: The notification title.
            body: The notification body.
            data: Additional data payload.
            image_url: Optional image URL for rich notification.
        
        Returns:
            True if the notification was sent successfully.
        
        Raises:
            Exception: If push sending fails.
        """
        if not FCM_AVAILABLE or not self.initialized:
            logger.info(f"[SIMULATED] Push notification to {device_token[:20]}...")
            logger.info(f"  Title: {title}")
            logger.info(f"  Body: {body}")
            logger.info(f"  Data: {data}")
            logger.info(f"  Image: {image_url}")
            return True
        
        try:
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url
            )
            
            message = messaging.Message(
                notification=notification,
                data=data or {},
                token=device_token
            )
            
            response = messaging.send(message)
            logger.info(f"Push notification sent successfully: {response}")
            return True
            
        except messaging.UnregisteredError:
            logger.error(f"Device token is invalid or unregistered: {device_token[:20]}...")
            raise
        except messaging.SenderIdMismatchError:
            logger.error(f"Sender ID mismatch for token: {device_token[:20]}...")
            raise
        except Exception as e:
            logger.error(f"Error sending push notification: {str(e)}")
            raise
    
    def send_multicast(
        self,
        device_tokens: list,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends push notifications to multiple devices.
        
        Args:
            device_tokens: A list of FCM device tokens.
            title: The notification title.
            body: The notification body.
            data: Additional data payload.
            image_url: Optional image URL.
        
        Returns:
            A dictionary with success_count and failure_count.
        """
        if not FCM_AVAILABLE or not self.initialized:
            logger.info(f"[SIMULATED] Multicast push to {len(device_tokens)} devices")
            logger.info(f"  Title: {title}")
            logger.info(f"  Body: {body}")
            return {"success_count": len(device_tokens), "failure_count": 0}
        
        try:
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url
            )
            
            message = messaging.MulticastMessage(
                notification=notification,
                data=data or {},
                tokens=device_tokens
            )
            
            response = messaging.send_multicast(message)
            
            logger.info(
                f"Multicast sent: {response.success_count} successful, "
                f"{response.failure_count} failed"
            )
            
            if response.failure_count > 0:
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        logger.error(
                            f"Failed to send to token {device_tokens[idx][:20]}...: "
                            f"{resp.exception}"
                        )
            
            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count
            }
            
        except Exception as e:
            logger.error(f"Error sending multicast: {str(e)}")
            raise
