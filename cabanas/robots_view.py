from django.http import HttpResponse

def robots_txt(request):
    content = (
        "User-agent: *\n"
        "Disallow: /gestion-huasco-2026/\n"
        "Disallow: /resena/\n"
        "Disallow: /admin/\n"
        "\n"
        "Sitemap: https://refugiosdelongomilla.cl/sitemap.xml\n"
    )
    return HttpResponse(content, content_type="text/plain")