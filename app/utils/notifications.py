import httpx
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

async def send_application_confirmation(
    job_seeker_email: str,
    job_title: str,
    company_name: str,
    job_seeker_name: str
):
    """
    Sends a POST request to n8n webhook to trigger a confirmation email.
    """
    webhook_url = settings.N8N_WEBHOOK_URL.strip().replace("\x00", "")
    webhook_user = settings.N8N_WEBHOOK_USER.strip().replace("\x00", "")
    webhook_pass = settings.N8N_WEBHOOK_PASSWORD.strip().replace("\x00", "")

    if not webhook_url:
        logger.warning("N8N_WEBHOOK_URL not configured. Skipping confirmation email.")
        return

    payload = {
        "email": job_seeker_email,
        "job_title": job_title,
        "company_name": company_name,
        "name": job_seeker_name
    }

    auth = None
    if webhook_user and webhook_pass:
        auth = (webhook_user, webhook_pass)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url, 
                json=payload,
                auth=auth
            )
            response.raise_for_status()
            logger.info(f"Confirmation email triggered for {job_seeker_email}")
    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to trigger confirmation email: {e.response.text}")
    except Exception as e:
        logger.error(f"Error sending confirmation email: {str(e)}")
