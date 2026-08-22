from datetime import date, timedelta
from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.core.mail import send_mail
from .forms import ReservaForm
from .models import AmenidadCasa, Atractivo, Casa, FotoZona, PuntoMapa, Reserva, Resena, Servicio, SiteConfig
import json

class HomeView(TemplateView):
    template_name = "cabanas/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = SiteConfig.get_solo()
        context["config"] = config
        context["casas"] = Casa.objects.filter(activa=True).prefetch_related("fotos")
        context["servicios"] = Servicio.objects.filter(activo=True)
        context["desierto_florido"] = Atractivo.objects.filter(
            categoria="desierto_florido", temporada_inicio__isnull=False
        ).first()
        context["resenas"] = Resena.objects.filter(publicada=True).select_related("casa")[:3]
        banner_atractivos = Atractivo.objects.filter(mostrar_en_banner=True).exclude(imagen='').order_by('orden')

        context["banner_imagenes"] = [a.imagen.url for a in banner_atractivos]

        idioma_actual = self.request.session.get("idioma", "es")

        puntos_interes = PuntoMapa.objects.all()
        context["puntos_interes"] = puntos_interes

        puntos_mapa = []
        for p in puntos_interes:
            nombre = p.nombre_en if (idioma_actual == "en" and p.nombre_en) else p.nombre
            puntos_mapa.append({
                "id": p.id,
                "nombre": nombre,
                "lat": float(p.latitud),
                "lng": float(p.longitud),
            })
        context["puntos_mapa_json"] = puntos_mapa

        if config.latitud and config.longitud:
            context["casa_mapa_json"] = {
                "nombre": config.brand_name,
                "lat": float(config.latitud),
                "lng": float(config.longitud),
            }
            context["mostrar_mapa_interactivo"] = True
        else:
            context["casa_mapa_json"] = None
            context["mostrar_mapa_interactivo"] = False

        context.setdefault("reserva_form", ReservaForm(idioma=idioma_actual))
        return context


class GaleriaView(TemplateView):
    template_name = "cabanas/galeria.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["config"] = SiteConfig.get_solo()
        context["casas"] = Casa.objects.filter(activa=True)
        context["fotos_zona"] = FotoZona.objects.all()
        return context


class GuiaZonaView(TemplateView):
    template_name = "cabanas/guia.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["config"] = SiteConfig.get_solo()
        context["casas"] = Casa.objects.filter(activa=True)
        
        atractivos = Atractivo.objects.all()
        destacados = [a for a in atractivos if a.destacado]

        grupos = []
        for valor, etiqueta in Atractivo.CATEGORIA_CHOICES:
            items = [a for a in atractivos if a.categoria == valor and not a.destacado]
            if items:
                grupos.append({"valor": valor, "etiqueta": etiqueta, "items": items})
                

        puntos_mapa = []
        for a in atractivos:
            if a.latitud and a.longitud:
                puntos_mapa.append({
                    "id": a.id,
                    "nombre": a.nombre_en if (a.nombre_en) else a.nombre,
                    "lat": float(a.latitud),
                    "lng": float(a.longitud),
                })
        context["puntos_mapa_json"] = json.dumps(puntos_mapa)

        context["destacados"] = destacados
        context["grupos_atractivos"] = grupos
        context["hay_desierto_florido"] = any(a.categoria == "desierto_florido" for a in atractivos)
        return context


from .emails import enviar_email  # agrega este import arriba del archivo, junto a los demás


class ReservaCreateView(FormView):
    form_class = ReservaForm
    template_name = "cabanas/home.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["idioma"] = self.request.session.get("idioma", "es")
        return kwargs

    def form_valid(self, form):
        reserva = form.save()
        config = SiteConfig.get_solo()
        texto = quote(reserva.whatsapp_mensaje())

        enviar_email(
            destinatario=config.contact_email,
            asunto=f"Nueva solicitud de reserva — {reserva.nombre}",
            mensaje_texto=reserva.whatsapp_mensaje(),
        )

        if reserva.email:
            mensaje_huesped = (
                f"Hola {reserva.nombre},\n\n"
                f"Recibimos tu solicitud de reserva en {config.brand_name}.\n\n"
                f"Casa: {reserva.casa.nombre if reserva.casa else 'a definir'}\n"
                f"Llegada: {reserva.fecha_llegada.strftime('%d-%m-%Y') if reserva.fecha_llegada else 'a definir'}\n"
                f"Salida: {reserva.fecha_salida.strftime('%d-%m-%Y') if reserva.fecha_salida else 'a definir'}\n"
                f"Huéspedes: {reserva.huespedes}\n\n"
                f"Te vamos a escribir pronto por WhatsApp para confirmar disponibilidad.\n\n"
                f"Gracias por elegirnos.\n{config.brand_name}"
            )
            enviar_email(
                destinatario=reserva.email,
                asunto=f"Recibimos tu solicitud — {config.brand_name}",
                mensaje_texto=mensaje_huesped,
            )

        messages.success(self.request, "¡Solicitud recibida! Te enviamos un correo y te redirigimos a WhatsApp para confirmar.")
        return redirect(f"https://wa.me/{config.whatsapp_number}?text={texto}")

    def form_invalid(self, form):
        home = HomeView()
        home.request = self.request
        context = home.get_context_data(reserva_form=form)
        return render(self.request, "cabanas/home.html", context)


def fechas_ocupadas(request):
    reservas = Reserva.objects.exclude(estado="cancelada").exclude(fecha_llegada__isnull=True).exclude(fecha_salida__isnull=True)
    rangos = [
        {"inicio": r.fecha_llegada.isoformat(), "fin": r.fecha_salida.isoformat()}
        for r in reservas
    ]
    return JsonResponse({"ocupado": rangos})


def cambiar_idioma(request, lang):
    if lang in ("es", "en"):
        request.session["idioma"] = lang
    siguiente = request.META.get("HTTP_REFERER", "/")
    return redirect(siguiente)

def calcular_ingreso_reserva(reserva):
    """Devuelve (ingreso_arriendo, ingreso_servicios) para una reserva."""
    ingreso_arriendo = 0
    if reserva.fecha_llegada and reserva.fecha_salida and reserva.casa and reserva.casa.precio_desde:
        noches = (reserva.fecha_salida - reserva.fecha_llegada).days
        ingreso_arriendo = noches * reserva.casa.precio_desde

    ingreso_servicios = sum(s.precio for s in reserva.servicios.all() if s.precio)
    return ingreso_arriendo, ingreso_servicios

def calcular_ingreso_en_rango(reserva, desde, hasta):
    """Ingreso de arriendo prorrateado por las noches que caen dentro de [desde, hasta] (ambos inclusive)."""
    if not (reserva.fecha_llegada and reserva.fecha_salida and reserva.casa and reserva.casa.precio_desde):
        return 0, 0
    inicio_solapado = max(reserva.fecha_llegada, desde)
    fin_solapado = min(reserva.fecha_salida, hasta + timedelta(days=1))
    noches = (fin_solapado - inicio_solapado).days
    if noches <= 0:
        return 0, 0
    ingreso_arriendo = noches * reserva.casa.precio_desde
    # Los servicios se atribuyen completos si la estadía se solapa con el rango
    ingreso_servicios = sum(s.precio for s in reserva.servicios.all() if s.precio)
    return ingreso_arriendo, ingreso_servicios

class PanelLoginView(View):
    template_name = "cabanas/panel_login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("cabanas:panel_home")
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("cabanas:panel_home")
        return render(request, self.template_name, {"error": True})


def panel_logout(request):
    logout(request)
    return redirect("cabanas:panel_login")


@method_decorator(login_required(login_url="cabanas:panel_login"), name="dispatch")
class PanelHomeView(View):
    template_name = "cabanas/panel_home.html"

    def get(self, request):
        hoy = date.today()
        contexto = {
            "active": "home",
            "pendientes": Reserva.objects.filter(estado="pendiente").count(),
            "confirmadas": Reserva.objects.filter(estado="confirmada").count(),
            "proximas_count": Reserva.objects.filter(estado="confirmada", fecha_llegada__gte=hoy).count(),
        }
        return render(request, self.template_name, contexto)


@method_decorator(login_required(login_url="cabanas:panel_login"), name="dispatch")
class PanelReservasView(View):
    template_name = "cabanas/panel_reservas.html"

    def get(self, request):
        reservas_qs = Reserva.objects.all().select_related("casa").prefetch_related("servicios")

        estado_filtro = request.GET.get("estado", "")
        busqueda = request.GET.get("q", "")
        fecha_desde = request.GET.get("fecha_desde", "")
        fecha_hasta = request.GET.get("fecha_hasta", "")

        reservas = reservas_qs
        if estado_filtro:
            reservas = reservas.filter(estado=estado_filtro)
        if busqueda:
            reservas = reservas.filter(nombre__icontains=busqueda)
        if fecha_desde:
            reservas = reservas.filter(fecha_llegada__gte=fecha_desde)
        if fecha_hasta:
            reservas = reservas.filter(fecha_llegada__lte=fecha_hasta)

        hoy = date.today()
        confirmadas_qs = Reserva.objects.filter(estado="confirmada")

        ingresos_estimados = 0
        noches_reservadas_mes = 0
        primer_dia_mes = hoy.replace(day=1)
        if hoy.month == 12:
            ultimo_dia_mes = hoy.replace(day=31)
        else:
            ultimo_dia_mes = hoy.replace(month=hoy.month + 1, day=1) - timedelta(days=1)
        dias_en_mes = ultimo_dia_mes.day

        for r in confirmadas_qs:
            if r.fecha_llegada and r.fecha_salida and r.casa and r.casa.precio_desde:
                noches = (r.fecha_salida - r.fecha_llegada).days
                ingresos_estimados += noches * r.casa.precio_desde
                inicio_solapado = max(r.fecha_llegada, primer_dia_mes)
                fin_solapado = min(r.fecha_salida, ultimo_dia_mes + timedelta(days=1))
                if fin_solapado > inicio_solapado:
                    noches_reservadas_mes += (fin_solapado - inicio_solapado).days

        ocupacion_pct = round((noches_reservadas_mes / dias_en_mes) * 100) if dias_en_mes else 0

        seis_meses_atras = hoy.replace(day=1) - timedelta(days=180)
        por_mes = {}
        for r in Reserva.objects.filter(creado__date__gte=seis_meses_atras):
            clave = r.creado.strftime("%Y-%m")
            por_mes[clave] = por_mes.get(clave, 0) + 1
        meses_ordenados = sorted(por_mes.items())[-6:]
        max_valor = max([v for _, v in meses_ordenados], default=1)
        NOMBRES_MES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        grafico_mensual = [
            {
                "mes": NOMBRES_MES[int(clave.split("-")[1]) - 1],
                "cantidad": cantidad,
                "pct": round((cantidad / max_valor) * 100) if max_valor else 0,
            }
            for clave, cantidad in meses_ordenados
        ]

        resumen = {
            "total": reservas_qs.count(),
            "pendientes": reservas_qs.filter(estado="pendiente").count(),
            "confirmadas": reservas_qs.filter(estado="confirmada").count(),
            "canceladas": reservas_qs.filter(estado="cancelada").count(),
            "ingresos_estimados": ingresos_estimados,
            "ocupacion_pct": ocupacion_pct,
            "proximas": confirmadas_qs.filter(fecha_llegada__gte=hoy).order_by("fecha_llegada")[:3],
            "grafico_mensual": grafico_mensual,
        }

        return render(request, self.template_name, {
            "active": "reservas",
            "reservas": reservas,
            "resumen": resumen,
            "estado_filtro": estado_filtro,
            "busqueda": busqueda,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
        })

    def post(self, request):
        reserva_id = request.POST.get("reserva_id")
        nuevo_estado = request.POST.get("estado")
        if reserva_id and nuevo_estado in dict(Reserva.ESTADO_CHOICES):
            Reserva.objects.filter(id=reserva_id).update(estado=nuevo_estado)
        return redirect("cabanas:panel_reservas")


@method_decorator(login_required(login_url="cabanas:panel_login"), name="dispatch")
class PanelCasasView(View):
    template_name = "cabanas/panel_casas.html"

    def get(self, request):
        casas = Casa.objects.prefetch_related("amenidades")
        return render(request, self.template_name, {"active": "casas", "casas": casas})

    def post(self, request):
        casa_id = request.POST.get("casa_id")
        casa = Casa.objects.filter(id=casa_id).first()
        if not casa:
            return redirect("cabanas:panel_casas")

        casa.nombre = request.POST.get("nombre", casa.nombre)
        casa.nombre_en = request.POST.get("nombre_en", "")
        casa.eyebrow = request.POST.get("eyebrow", casa.eyebrow)
        casa.eyebrow_en = request.POST.get("eyebrow_en", "")
        casa.descripcion = request.POST.get("descripcion", casa.descripcion)
        casa.descripcion_en = request.POST.get("descripcion_en", "")
        casa.antiguedad_texto = request.POST.get("antiguedad_texto", "")
        casa.distancia_a_vallenar_km = request.POST.get("distancia_a_vallenar_km") or casa.distancia_a_vallenar_km

        capacidad = request.POST.get("capacidad_huespedes", "").strip()
        casa.capacidad_huespedes = int(capacidad) if capacidad.isdigit() else None

        precio = request.POST.get("precio_desde", "").strip()
        casa.precio_desde = int(precio) if precio.isdigit() else None

        casa.checkin_hora = request.POST.get("checkin_hora", "")
        casa.checkout_hora = request.POST.get("checkout_hora", "")
        casa.acepta_mascotas = request.POST.get("acepta_mascotas") == "on"
        casa.reglas_texto = request.POST.get("reglas_texto", "")
        casa.reglas_texto_en = request.POST.get("reglas_texto_en", "")
        casa.activa = request.POST.get("activa") == "on"
        casa.save()

        casa.amenidades.all().delete()
        lineas = request.POST.get("amenidades_texto", "").splitlines()
        for i, linea in enumerate(lineas):
            partes = [p.strip() for p in linea.split("|")]
            if not partes or not partes[0]:
                continue
            icono = partes[0] if len(partes) > 0 else ""
            texto = partes[1] if len(partes) > 1 else ""
            texto_en = partes[2] if len(partes) > 2 else ""
            if texto:
                AmenidadCasa.objects.create(casa=casa, icono=icono, texto=texto, texto_en=texto_en, orden=i)

        return redirect("cabanas:panel_casas")


@method_decorator(login_required(login_url="cabanas:panel_login"), name="dispatch")
class PanelConfigView(View):
    template_name = "cabanas/panel_config.html"

    def get(self, request):
        config = SiteConfig.get_solo()
        return render(request, self.template_name, {"active": "config", "config": config})

    def post(self, request):
        config = SiteConfig.get_solo()
        config.brand_name = request.POST.get("brand_name", config.brand_name)
        config.brand_subtitle = request.POST.get("brand_subtitle", config.brand_subtitle)
        config.hero_titulo = request.POST.get("hero_titulo", config.hero_titulo)
        config.hero_titulo_en = request.POST.get("hero_titulo_en", "")
        config.hero_subtitulo = request.POST.get("hero_subtitulo", config.hero_subtitulo)
        config.hero_subtitulo_en = request.POST.get("hero_subtitulo_en", "")
        config.whatsapp_number = request.POST.get("whatsapp_number", config.whatsapp_number)
        config.instagram_handle = request.POST.get("instagram_handle", config.instagram_handle)
        config.contact_email = request.POST.get("contact_email", config.contact_email)
        config.save()
        return redirect("cabanas:panel_config")

@method_decorator(login_required(login_url="cabanas:panel_login"), name="dispatch")
class PanelFinanzasView(View):
    template_name = "cabanas/panel_finanzas.html"

    def get(self, request):
        confirmadas = Reserva.objects.filter(estado="confirmada").select_related("casa").prefetch_related("servicios")
        pendientes = Reserva.objects.filter(estado="pendiente").select_related("casa").prefetch_related("servicios")

        total_arriendo = 0
        total_servicios = 0
        por_casa = {}
        por_servicio = {}
        por_mes = {}

        for r in confirmadas:
            ing_arriendo, ing_servicios = calcular_ingreso_reserva(r)
            total_arriendo += ing_arriendo
            total_servicios += ing_servicios

            if r.casa:
                casa_data = por_casa.setdefault(r.casa.nombre, {"ingreso": 0, "reservas": 0})
                casa_data["ingreso"] += ing_arriendo
                casa_data["reservas"] += 1

            for s in r.servicios.all():
                if s.precio:
                    serv_data = por_servicio.setdefault(s.nombre, {"ingreso": 0, "usos": 0})
                    serv_data["ingreso"] += s.precio
                    serv_data["usos"] += 1

            if r.fecha_llegada:
                clave = r.fecha_llegada.strftime("%Y-%m")
                por_mes[clave] = por_mes.get(clave, 0) + ing_arriendo + ing_servicios

        potencial_pendientes = 0
        for r in pendientes:
            ing_arriendo, ing_servicios = calcular_ingreso_reserva(r)
            potencial_pendientes += ing_arriendo + ing_servicios

        meses_ordenados = sorted(por_mes.items())[-6:]
        max_valor = max([v for _, v in meses_ordenados], default=1)
        NOMBRES_MES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        grafico_ingresos = [
            {
                "mes": NOMBRES_MES[int(clave.split("-")[1]) - 1],
                "monto": monto,
                "pct": round((monto / max_valor) * 100) if max_valor else 0,
            }
            for clave, monto in meses_ordenados
        ]

        # --- Rango de fechas seleccionado ---
        fecha_desde_str = request.GET.get("fecha_desde", "")
        fecha_hasta_str = request.GET.get("fecha_hasta", "")
        rango_resultado = None

        if fecha_desde_str:
            desde = date.fromisoformat(fecha_desde_str)
            hasta = date.fromisoformat(fecha_hasta_str) if fecha_hasta_str else desde

            rango_arriendo = 0
            rango_servicios = 0
            rango_reservas = 0
            for r in confirmadas:
                ing_a, ing_s = calcular_ingreso_en_rango(r, desde, hasta)
                if ing_a or ing_s:
                    rango_arriendo += ing_a
                    rango_servicios += ing_s
                    rango_reservas += 1

            rango_resultado = {
                "desde": desde,
                "hasta": hasta,
                "arriendo": rango_arriendo,
                "servicios": rango_servicios,
                "total": rango_arriendo + rango_servicios,
                "reservas": rango_reservas,
            }

        contexto = {
            "active": "finanzas",
            "total_arriendo": total_arriendo,
            "total_servicios": total_servicios,
            "total_general": total_arriendo + total_servicios,
            "potencial_pendientes": potencial_pendientes,
            "por_casa": sorted(por_casa.items(), key=lambda x: -x[1]["ingreso"]),
            "por_servicio": sorted(por_servicio.items(), key=lambda x: -x[1]["ingreso"]),
            "grafico_ingresos": grafico_ingresos,
            "cantidad_confirmadas": confirmadas.count(),
            "fecha_desde": fecha_desde_str,
            "fecha_hasta": fecha_hasta_str,
            "rango_resultado": rango_resultado,
        }
        return render(request, self.template_name, contexto)
@method_decorator(login_required(login_url="cabanas:panel_login"), name="dispatch")
class PanelReservaDeleteView(View):
    def post(self, request, reserva_id):
        if request.POST.get("confirmar") == "si":
            reserva = Reserva.objects.filter(id=reserva_id).first()
            if reserva:
                reserva.delete()
                messages.success(request, "Reserva eliminada correctamente.")
        return redirect("cabanas:panel_reservas")

class ResenasView(TemplateView):
    template_name = "cabanas/resenas.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["config"] = SiteConfig.get_solo()
        context["casas"] = Casa.objects.filter(activa=True)
        context["resenas"] = Resena.objects.filter(publicada=True).select_related("casa")
        return context

class ResenaSubmitView(View):
    template_name = "cabanas/resena_submit.html"

    def get(self, request, token):
        reserva = Reserva.objects.filter(token_resena=token).first()
        if not reserva or hasattr(reserva, "resena"):
            return render(request, self.template_name, {"invalido": True, "config": SiteConfig.get_solo()})
        return render(request, self.template_name, {"reserva": reserva, "config": SiteConfig.get_solo()})

    def post(self, request, token):
        reserva = Reserva.objects.filter(token_resena=token).first()
        if not reserva or hasattr(reserva, "resena"):
            return render(request, self.template_name, {"invalido": True, "config": SiteConfig.get_solo()})

        estrellas = request.POST.get("estrellas", "5")
        texto = request.POST.get("texto", "").strip()
        if not texto:
            return render(request, self.template_name, {
                "reserva": reserva, "config": SiteConfig.get_solo(), "error": True,
            })

        Resena.objects.create(
            reserva=reserva,
            nombre_huesped=reserva.nombre,
            casa=reserva.casa,
            estrellas=int(estrellas),
            texto=texto,
            fecha=reserva.fecha_salida,
            publicada=False,
        )
        return render(request, self.template_name, {"enviado": True, "config": SiteConfig.get_solo()})

@method_decorator(login_required(login_url="cabanas:panel_login"), name="dispatch")
class PanelResenasView(View):
    template_name = "cabanas/panel_resenas.html"

    def get(self, request):
        resenas = Resena.objects.all().select_related("casa")
        return render(request, self.template_name, {"active": "resenas", "resenas": resenas})

    def post(self, request):
        resena_id = request.POST.get("resena_id")
        accion = request.POST.get("accion")
        resena = Resena.objects.filter(id=resena_id).first()
        if resena:
            if accion == "publicar":
                resena.publicada = True
                resena.save()
            elif accion == "ocultar":
                resena.publicada = False
                resena.save()
            elif accion == "eliminar":
                resena.delete()
        return redirect("cabanas:panel_resenas")