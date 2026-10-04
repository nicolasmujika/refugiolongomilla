import logging
import urllib.request
from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import BloqueoFechas, Casa

logger = logging.getLogger(__name__)

INTERVALO_MIN = 30  # cada cuántos minutos se vuelve a leer Airbnb


def _parse_ical(texto):
    """Devuelve una lista de dicts (uno por VEVENT) con DTSTART, DTEND, SUMMARY..."""
    lineas = []
    for l in texto.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if l[:1] in (" ", "\t") and lineas:  # línea continuada
            lineas[-1] += l[1:]
        else:
            lineas.append(l)

    eventos, ev = [], None
    for l in lineas:
        if l == "BEGIN:VEVENT":
            ev = {}
        elif l == "END:VEVENT":
            if ev is not None:
                eventos.append(ev)
            ev = None
        elif ev is not None and ":" in l:
            clave, valor = l.split(":", 1)
            ev[clave.split(";")[0].upper()] = valor.strip()
    return eventos


def _a_fecha(valor):
    return datetime.strptime(valor[:8], "%Y%m%d").date()


def sincronizar_casa(casa):
    """Lee el iCal de la casa y reemplaza sus bloqueos de origen 'airbnb'. Devuelve cuántos quedaron."""
    if not casa.ical_url:
        return 0

    req = urllib.request.Request(casa.ical_url, headers={"User-Agent": "Mozilla/5.0 (sync calendario)"})
    with urllib.request.urlopen(req, timeout=10) as r:
        texto = r.read().decode("utf-8", errors="replace")

    if "BEGIN:VCALENDAR" not in texto:
        raise ValueError("El enlace no devolvió un calendario iCal válido")

    hoy = timezone.localdate()
    nuevos = []
    for ev in _parse_ical(texto):
        try:
            inicio = _a_fecha(ev["DTSTART"])
        except (KeyError, ValueError):
            continue
        try:
            fin = _a_fecha(ev["DTEND"])
        except (KeyError, ValueError):
            fin = inicio + timedelta(days=1)
        if fin <= inicio:
            fin = inicio + timedelta(days=1)
        if fin < hoy:
            continue  # ya pasó
        nuevos.append(BloqueoFechas(
            casa=casa, fecha_desde=inicio, fecha_hasta=fin,
            motivo=(ev.get("SUMMARY") or "Airbnb")[:100], origen="airbnb",
        ))

    # Solo si la lectura funcionó: reemplazamos todo (así se limpian las cancelaciones)
    with transaction.atomic():
        BloqueoFechas.objects.filter(casa=casa, origen="airbnb").delete()
        BloqueoFechas.objects.bulk_create(nuevos)
    return len(nuevos)


def sincronizar_si_corresponde():
    """Sincroniza las casas cuya última lectura fue hace más de INTERVALO_MIN minutos. Nunca lanza error."""
    ahora = timezone.now()
    limite = ahora - timedelta(minutes=INTERVALO_MIN)
    casas = Casa.objects.exclude(ical_url="").filter(
        Q(ical_ultima_sync__isnull=True) | Q(ical_ultima_sync__lt=limite)
    )
    for casa in casas:
        # marcamos el intento primero, así si Airbnb falla no se reintenta en cada visita
        Casa.objects.filter(pk=casa.pk).update(ical_ultima_sync=ahora)
        try:
            sincronizar_casa(casa)
        except Exception:
            logger.exception("No se pudo sincronizar el calendario de %s", casa)