from django.http import HttpResponse
from django.urls import reverse

# Rutas públicas que quieres indexar en Google.
# NO incluyas nada de "gestion-huasco-2026" (panel privado) ni "resena_submit" (link único por huésped).
PAGINAS_PUBLICAS = [
    ("cabanas:home", "1.0", "weekly"),
    ("cabanas:galeria", "0.8", "weekly"),
    ("cabanas:guia", "0.7", "monthly"),
    ("cabanas:reservar", "0.9", "weekly"),
    ("cabanas:resenas", "0.6", "monthly"),
]

def sitemap_xml(request):
    urls_xml = []
    for url_name, priority, changefreq in PAGINAS_PUBLICAS:
        loc = request.build_absolute_uri(reverse(url_name))
        urls_xml.append(
            f"<url><loc>{loc}</loc><priority>{priority}</priority>"
            f"<changefreq>{changefreq}</changefreq></url>"
        )

    xml_content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(urls_xml) +
        "</urlset>"
    )
    return HttpResponse(xml_content, content_type="application/xml")