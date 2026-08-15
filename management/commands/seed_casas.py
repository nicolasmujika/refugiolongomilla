from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand

from cabanas.models import Casa, FotoCasa, SiteConfig

SEED_IMAGES_DIR = Path(__file__).resolve().parents[3] / "seed_data" / "images"


class Command(BaseCommand):
    help = "Carga datos de ejemplo: Casa Centenario, configuración del sitio y fotos iniciales."

    def handle(self, *args, **options):
        SiteConfig.get_solo()
        self.stdout.write(self.style.SUCCESS("Configuración del sitio lista (edítala en /admin/)."))

        centenario, created = Casa.objects.get_or_create(
            tipo="centenario",
            defaults=dict(
                nombre="Casa Centenario",
                eyebrow="Casa antigua",
                descripcion="Una casa antigua de alrededor de cien años.",
                antiguedad_texto="~100 años",
                distancia_a_vallenar_km=10,
                orden=1,
            ),
        )
        self.stdout.write(self.style.SUCCESS(f"Casa Centenario {'creada' if created else 'ya existía'}."))