import httpx
import logging
from core.config import settings

logger = logging.getLogger(__name__)


def send_otp_sms(phone: str, otp: str) -> bool:
    if not settings.SPARROW_SMS_TOKEN:
        logger.warning(f"SMS token not configured. OTP for {phone}: {otp}")
        return False

    message = f"Your Uthau Nepal verification code is: {otp}. Valid for {settings.OTP_EXPIRE_MINUTES} minutes."

    try:
        with httpx.Client(timeout=10) as client:
            response = client.post(
                "https://api.sparrowsms.com/v2/sms/send",
                json={
                    "token": settings.SPARROW_SMS_TOKEN,
                    "from": settings.SPARROW_SMS_FROM,
                    "to": phone,
                    "message": message,
                },
            )
            if response.status_code == 200:
                logger.info(f"OTP SMS sent to {phone}")
                return True
            else:
                logger.error(f"SMS failed for {phone}: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"SMS error for {phone}: {e}")
        return False


def send_push(user_id: int, title: str, body: str) -> None:
    pass
