from django.core.management.base import BaseCommand

from cabanas.ical_sync import sincronizar_casa
from cabanas.models import Casa


class Command(BaseCommand):
    help = "Lee el calendario iCal de Airbnb de cada casa y actualiza los días ocupados."

    def handle(self, *args, **options):
        casas = Casa.objects.exclude(ical_url="")
        if not casas:
            self.stdout.write("Ninguna casa tiene enlace iCal configurado.")
        for casa in casas:
            try:
                n = sincronizar_casa(casa)
                self.stdout.write(self.style.SUCCESS(f"{casa.nombre}: {n} bloqueos importados"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"{casa.nombre}: error — {e}"))