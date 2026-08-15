from datetime import date, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.urls import reverse

from cabanas.models import Reserva, SiteConfig


class Command(BaseCommand):
    help = "Envía email pidiendo reseña a huéspedes cuyo check-out fue ayer."

    def handle(self, *args, **options):
        ayer = date.today() - timedelta(days=1)
        config = SiteConfig.get_solo()

        reservas = Reserva.objects.filter(
            estado="confirmada",
            fecha_salida=ayer,
            resena_solicitada=False,
        )

        for r in reservas:
            if not r.email:
                continue
            link = f"https://{settings.SITE_DOMAIN}{reverse('cabanas:resena_submit', args=[r.token_resena])}"
            mensaje = (
                f"Hola {r.nombre},\n\n"
                f"Esperamos que hayas disfrutado tu estadía en {config.brand_name}.\n\n"
                f"¿Nos ayudas dejando una reseña de tu experiencia?\n{link}\n\n"
                f"Gracias por elegirnos."
            )
            send_mail(
                subject=f"¿Cómo fue tu estadía? — {config.brand_name}",
                message=mensaje,
                from_email=None,
                recipient_list=[r.email],
                fail_silently=True,
            )
            r.resena_solicitada = True
            r.save()
            self.stdout.write(self.style.SUCCESS(f"Solicitud enviada a {r.nombre}"))