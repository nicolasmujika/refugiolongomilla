import resend
from django.conf import settings


def enviar_email(destinatario, asunto, mensaje_texto):
    if not settings.RESEND_API_KEY:
        return False
    try:
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": f"{settings.DEFAULT_FROM_EMAIL}" if getattr(settings, "DEFAULT_FROM_EMAIL", None) else "onboarding@resend.dev",
            "to": [destinatario],
            "subject": asunto,
            "text": mensaje_texto,
        })
        return True
    except Exception:
        return False