from django.contrib import admin
from django.utils.html import format_html

from .models import AmenidadCasa, Atractivo, Casa, FotoCasa, FotoZona, Reserva, Resena, Servicio, SiteConfig

class FotoCasaInline(admin.TabularInline):
    model = FotoCasa
    extra = 1
    fields = ("imagen", "preview", "descripcion", "orden")
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="height:60px; border-radius:2px;">', obj.imagen.url)
        return "—"

    preview.short_description = "Vista previa"
    
class AmenidadCasaInline(admin.TabularInline):
    model = AmenidadCasa
    extra = 1
    fields = ("icono", "texto", "texto_en", "orden")


@admin.register(Casa)
class CasaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "capacidad_huespedes", "precio_desde", "activa", "orden")
    list_editable = ("activa", "orden")
    inlines = [FotoCasaInline, AmenidadCasaInline]

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "casa", "fecha_llegada", "fecha_salida", "estado", "creado")
    list_editable = ("estado",)
    list_filter = ("estado",)
    filter_horizontal = ("servicios",)


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Portada (hero)", {"fields": ("hero_titulo", "hero_titulo_en", "hero_subtitulo", "hero_subtitulo_en")}),
        ("Marca", {"fields": ("brand_name", "brand_subtitle")}),
        ("Contacto", {"fields": ("whatsapp_number", "instagram_handle", "contact_email")}),
        ("Ubicación", {"fields": ("maps_embed_url",)}),
        ("Guía descargable", {"fields": ("guia_pdf",)}),
    )

    def has_add_permission(self, request):
        return not SiteConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "precio", "activo", "orden", "preview")
    list_editable = ("precio", "activo", "orden")
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="height:50px; border-radius:2px;">', obj.imagen.url)
        return "—"

    preview.short_description = "Vista previa"

@admin.register(FotoZona)
class FotoZonaAdmin(admin.ModelAdmin):
    list_display = ("descripcion", "orden", "preview")
    list_editable = ("orden",)
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="height:50px; border-radius:2px;">', obj.imagen.url)
        return "—"

    preview.short_description = "Vista previa"

@admin.register(Atractivo)
class AtractivoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "destacado", "mostrar_en_banner", "temporada_inicio", "temporada_fin", "orden", "preview")
    list_editable = ("destacado", "mostrar_en_banner", "orden")
    list_filter = ("categoria",)
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="height:50px; border-radius:2px;">', obj.imagen.url)
        return "—"

    preview.short_description = "Vista previa"


@admin.register(Resena)
class ResenaAdmin(admin.ModelAdmin):
    list_display = ("nombre_huesped", "casa", "estrellas", "fecha", "publicada", "orden")
    list_editable = ("publicada", "orden")
    list_filter = ("estrellas", "publicada", "casa")
