from django.db import models
import re
import uuid
class Casa(models.Model):
    TIPO_CHOICES = [
        ("centenario", "Casa Centenario"),
        ("moderna", "Casa Moderna"),
    ]

    tipo = models.CharField("Tipo", max_length=20, choices=TIPO_CHOICES, unique=True)
    nombre = models.CharField("Nombre a mostrar", max_length=80)
    eyebrow = models.CharField("Texto pequeño superior", max_length=60)
    descripcion = models.TextField("Descripción")
    antiguedad_texto = models.CharField("Antigüedad", max_length=60, blank=True)
    capacidad_huespedes = models.PositiveIntegerField("Capacidad de huéspedes", null=True, blank=True)
    distancia_a_vallenar_km = models.PositiveIntegerField("Distancia a Vallenar (km)", default=10)
    precio_desde = models.PositiveIntegerField("Precio desde (CLP)", null=True, blank=True)
    orden = models.PositiveIntegerField("Orden de aparición", default=0)
    activa = models.BooleanField("Visible en la página", default=True)
    descripcion_en = models.TextField(
        "Descripción (inglés)", blank=True,
        help_text="Opcional.",
    )
    nombre_en = models.CharField("Nombre (inglés)", max_length=80, blank=True)
    eyebrow_en = models.CharField("Texto pequeño superior (inglés)", max_length=60, blank=True)

    checkin_hora = models.CharField("Check-in desde", max_length=20, blank=True, help_text="Ej: 15:00")
    checkout_hora = models.CharField("Check-out hasta", max_length=20, blank=True, help_text="Ej: 11:00")
    acepta_mascotas = models.BooleanField("Acepta mascotas", default=False)
    reglas_texto = models.TextField(
        "Reglas adicionales", blank=True,
        help_text="Una regla por línea. Ej: No fiestas ni eventos.",
    )
    reglas_texto_en = models.TextField("Reglas adicionales (inglés)", blank=True)

    class Meta:
        ordering = ["orden", "id"]

    def get_precio_display(self):
        if self.precio_desde:
            return f"${self.precio_desde:,.0f}".replace(",", ".")
        return "A definir"

    def __str__(self):
        return self.nombre


class FotoCasa(models.Model):
    casa = models.ForeignKey(Casa, related_name="fotos", on_delete=models.CASCADE)
    imagen = models.ImageField("Imagen", upload_to="casas/")
    descripcion = models.CharField("Descripción breve", max_length=80, blank=True)
    orden = models.PositiveIntegerField("Orden", default=0)

    class Meta:
        ordering = ["orden", "id"]

    def __str__(self):
        return f"{self.casa.nombre} — {self.descripcion or self.imagen.name}"


class Reserva(models.Model):
    ESTADO_CHOICES = [
        ("pendiente", "Pendiente de confirmar"),
        ("confirmada", "Confirmada"),
        ("cancelada", "Cancelada"),
    ]

    casa = models.ForeignKey(Casa, related_name="reservas", on_delete=models.SET_NULL, null=True, blank=True)
    servicios = models.ManyToManyField("Servicio", blank=True, verbose_name="Servicios extra")
    nombre = models.CharField("Nombre", max_length=100)
    codigo_pais = models.CharField("Código de país", max_length=5, default="+56")
    contacto = models.CharField("Teléfono", max_length=100)
    fecha_llegada = models.DateField("Llegada", null=True, blank=True)
    fecha_salida = models.DateField("Salida", null=True, blank=True)
    huespedes = models.PositiveIntegerField("Huéspedes", default=2)
    mensaje = models.TextField("Mensaje adicional", blank=True)
    estado = models.CharField("Estado", max_length=15, choices=ESTADO_CHOICES, default="pendiente")
    creado = models.DateTimeField("Creado", auto_now_add=True)
    email = models.EmailField("Email", blank=True, help_text="Para enviar la confirmación por correo.")
    token_resena = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    resena_solicitada = models.BooleanField(default=False)
    
    class Meta:
        ordering = ["-creado"]

    def __str__(self):
        return f"{self.nombre} — {self.casa} ({self.get_estado_display()})"

    def whatsapp_mensaje(self):
        partes = [
            "Hola, me gustaría reservar.",
            f"Casa: {self.casa.nombre if self.casa else 'a definir'}",
        ]
        if self.fecha_llegada:
            partes.append(f"Llegada: {self.fecha_llegada:%d-%m-%Y}")
        if self.fecha_salida:
            partes.append(f"Salida: {self.fecha_salida:%d-%m-%Y}")
        partes.append(f"Huéspedes: {self.huespedes}")
        servicios = list(self.servicios.all())
        if servicios:
            nombres = ", ".join(s.nombre for s in servicios)
            partes.append(f"Servicios extra: {nombres}")
        partes.append(f"Nombre: {self.nombre}")
        partes.append(f"Contacto: {self.codigo_pais} {self.contacto}")
        return "\n".join(partes)

    def mensaje_confirmacion_whatsapp(self):
        return (
            f"Hola {self.nombre}, tu reserva está confirmada ✅\n\n"
            f"Casa: {self.casa.nombre if self.casa else 'a definir'}\n"
            f"Llegada: {self.fecha_llegada.strftime('%d-%m-%Y') if self.fecha_llegada else 'a definir'}\n"
            f"Salida: {self.fecha_salida.strftime('%d-%m-%Y') if self.fecha_salida else 'a definir'}\n\n"
            f"¡Te esperamos!"
        )
    
    def contacto_es_telefono(self):
        return bool(re.search(r'\d{6,}', self.contacto))

    def contacto_whatsapp(self):
        digitos = re.sub(r'\D', '', self.contacto)
        codigo_limpio = re.sub(r'\D', '', self.codigo_pais)
        if digitos.startswith(codigo_limpio):
            return digitos
        return codigo_limpio + digitos


class SiteConfig(models.Model):
    """Config global del sitio. Singleton: solo debe existir un registro (pk=1)."""

    hero_titulo = models.TextField(
        "Título del hero",
        default="Casa Centenario<br><em>cien años de historia</em>",
        help_text="Puedes usar <br> para salto de línea y <em>...</em> para cursiva.",
    )
    hero_subtitulo = models.CharField(
        "Subtítulo del hero",
        max_length=200,
        default="A 10 km de Vallenar, un lugar tranquilo y de fácil acceso en el valle del Huasco.",
    )
    brand_name = models.CharField("Nombre de marca", max_length=60, default="Entresiglos")
    brand_subtitle = models.CharField("Subtítulo", max_length=120, default="Casas de campo en el Huasco")
    whatsapp_number = models.CharField("WhatsApp", max_length=20, help_text="Sin '+' ni espacios. Ej: 56912345678")
    instagram_handle = models.CharField("Instagram", max_length=40, help_text="Con @. Ej: @entresiglos.huasco")
    contact_email = models.EmailField("Email de contacto")
    maps_embed_url = models.URLField("URL de Google Maps (embed)", blank=True)
    guia_pdf = models.FileField(
        "Guía turística (PDF)", upload_to="guias/", blank=True, null=True,
        help_text="Sube un PDF descargable con recomendaciones de la zona.",
    )
    hero_titulo_en = models.TextField("Título del hero (inglés)", blank=True)
    hero_subtitulo_en = models.CharField("Subtítulo del hero (inglés)", max_length=200, blank=True)

    class Meta:
        verbose_name = "Configuración del sitio"
        verbose_name_plural = "Configuración del sitio"

    def __str__(self):
        return self.brand_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                "whatsapp_number": "56989893701",
                "instagram_handle": "@entresiglos.huasco",
                "contact_email": "entresiglos@gmail.com",
            },
        )
        return obj

class Servicio(models.Model):

    nombre = models.CharField("Nombre", max_length=60)
    descripcion = models.TextField("Descripción", blank=True)
    precio = models.PositiveIntegerField("Precio (CLP)", null=True, blank=True)
    icono = models.CharField(
        "Ícono (emoji)", max_length=10, blank=True,
        help_text="Ej: 🛁 para tinaja, ☕ para desayuno. Opcional.",
    )
    imagen = models.ImageField("Imagen de fondo", upload_to="servicios/", blank=True, null=True)
    activo = models.BooleanField("Disponible", default=True)
    orden = models.PositiveIntegerField("Orden", default=0)
    nombre_en = models.CharField("Nombre (inglés)", max_length=60, blank=True)
    descripcion_en = models.TextField("Descripción (inglés)", blank=True)
    

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
        ordering = ["orden", "id"]

    def __str__(self):
        return self.nombre

    def get_precio_display(self):
        if self.precio:
            return f"${self.precio:,.0f}".replace(",", ".")
        return "Incluido"


class FotoZona(models.Model):
    

    imagen = models.ImageField("Imagen", upload_to="zona/")
    descripcion = models.CharField("Descripción breve", max_length=80, blank=True)
    orden = models.PositiveIntegerField("Orden", default=0)

    class Meta:
        verbose_name = "Foto de la zona"
        verbose_name_plural = "Galería de la zona"
        ordering = ["orden", "id"]

    def __str__(self):
        return self.descripcion or self.imagen.name

class Atractivo(models.Model):
    CATEGORIA_CHOICES = [
        ("desierto_florido", "Desierto Florido"),
        ("vinas", "Viñas y bodegas"),
        ("cabalgatas", "Tours y actividades"),
        ("mirador", "Mirador"),
        ("pueblo", "Pueblo / cultura"),
        ("aire_libre", "Aire libre"),
        ("costa", "Caleta / Costa"),
        ("otro", "Otro"),
    ]

    nombre = models.CharField("Nombre", max_length=80)
    categoria = models.CharField("Categoría", max_length=20, choices=CATEGORIA_CHOICES, default="otro")
    descripcion = models.TextField("Descripción")
    distancia_km = models.PositiveIntegerField("Distancia (km)", null=True, blank=True)
    imagen = models.ImageField("Imagen", upload_to="atractivos/", blank=True, null=True)
    destacado = models.BooleanField(
        "Destacado", default=False,
        help_text="Aparece primero y más grande en la página de guía.",
    )
    temporada_inicio = models.DateField(
        "Temporada — inicio", null=True, blank=True,
        help_text="Solo para atractivos estacionales, ej. Desierto Florido. Déjalo vacío si no aplica.",
    )
    temporada_fin = models.DateField("Temporada — fin", null=True, blank=True)
    orden = models.PositiveIntegerField("Orden", default=0)
    nombre_en = models.CharField("Nombre (inglés)", max_length=80, blank=True)
    descripcion_en = models.TextField("Descripción (inglés)", blank=True)
    sitio_web = models.URLField("Sitio web", blank=True, help_text="Opcional. Ej: https://www.pagina.cl")
    mostrar_en_banner = models.BooleanField(
        "Mostrar en banner del inicio", default=False,
        help_text="Actívalo para que la foto de este atractivo aparezca en el carrusel de la página principal.",
    )

    class Meta:
        verbose_name = "Atractivo turístico"
        verbose_name_plural = "Guía — Atractivos turísticos"
        ordering = ["-destacado", "orden", "id"]

    def __str__(self):
        return self.nombre

    def en_temporada(self):
        """True si hoy cae dentro del rango de temporada definido."""
        if not (self.temporada_inicio and self.temporada_fin):
            return False
        from datetime import date
        hoy = date.today()
        return self.temporada_inicio <= hoy <= self.temporada_fin

class AmenidadCasa(models.Model):
    casa = models.ForeignKey(Casa, related_name="amenidades", on_delete=models.CASCADE, verbose_name="Casa")
    icono = models.CharField("Ícono (emoji)", max_length=10, blank=True, help_text="Ej: 🔥 🚿 📺 💧")
    texto = models.CharField("Texto", max_length=60)
    texto_en = models.CharField("Texto (inglés)", max_length=60, blank=True)
    orden = models.PositiveIntegerField("Orden", default=0)

    class Meta:
        verbose_name = "Amenidad"
        verbose_name_plural = "Amenidades"
        ordering = ["orden", "id"]

    def __str__(self):
        return f"{self.casa.nombre} — {self.texto}"

class Resena(models.Model):
    ESTRELLAS_CHOICES = [(i, str(i)) for i in range(1, 6)]

    nombre_huesped = models.CharField("Nombre del huésped", max_length=80)
    casa = models.ForeignKey(Casa, related_name="resenas", on_delete=models.SET_NULL, null=True, blank=True)
    estrellas = models.PositiveSmallIntegerField("Estrellas", choices=ESTRELLAS_CHOICES, default=5)
    texto = models.TextField("Comentario")
    texto_en = models.TextField("Comentario (inglés)", blank=True)
    fecha = models.DateField("Fecha de la estadía", null=True, blank=True)
    publicada = models.BooleanField("Publicada", default=False)
    orden = models.PositiveIntegerField("Orden", default=0)
    reserva = models.OneToOneField(Reserva, related_name="resena", on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        verbose_name = "Reseña"
        verbose_name_plural = "Reseñas"
        ordering = ["orden", "-fecha", "id"]

    def __str__(self):
        return f"{self.nombre_huesped} — {self.estrellas}★"