import resend
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def enviar_email(destinatario, asunto, mensaje_texto):
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY no configurada, no se envía email")
        return False
    try:
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": [destinatario],
            "subject": asunto,
            "text": mensaje_texto,
        })
        return True
    except Exception as e:
        logger.error(f"Error enviando email a {destinatario}: {e}")
        return False