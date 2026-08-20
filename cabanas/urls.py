from django.urls import path
from .views import (
    HomeView, ReservaCreateView, GaleriaView, GuiaZonaView,
    fechas_ocupadas, cambiar_idioma,
    PanelLoginView, PanelReservasView, PanelCasasView, PanelConfigView, panel_logout,
    PanelHomeView,PanelFinanzasView,PanelReservaDeleteView,ResenasView,ResenaSubmitView, PanelResenasView
)
from .sitemap_view import sitemap_xml
from .robots_view import robots_txt
app_name = "cabanas"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("galeria/", GaleriaView.as_view(), name="galeria"),
    path("guia/", GuiaZonaView.as_view(), name="guia"),
    path("reservar/", ReservaCreateView.as_view(), name="reservar"),
    path("fechas-ocupadas/", fechas_ocupadas, name="fechas_ocupadas"),
    path("idioma/<str:lang>/", cambiar_idioma, name="cambiar_idioma"),
    path("gestion-huasco-2026/", PanelLoginView.as_view(), name="panel_login"),
    path("gestion-huasco-2026/reservas/", PanelReservasView.as_view(), name="panel_reservas"),
    path("gestion-huasco-2026/casas/", PanelCasasView.as_view(), name="panel_casas"),
    path("gestion-huasco-2026/config/", PanelConfigView.as_view(), name="panel_config"),
    path("gestion-huasco-2026/salir/", panel_logout, name="panel_logout"),
    path("gestion-huasco-2026/inicio/", PanelHomeView.as_view(), name="panel_home"),
    path("gestion-huasco-2026/finanzas/", PanelFinanzasView.as_view(), name="panel_finanzas"),
    path("gestion-huasco-2026/reservas/<int:reserva_id>/eliminar/", PanelReservaDeleteView.as_view(), name="panel_reserva_delete"),
    path("resenas/", ResenasView.as_view(), name="resenas"),
    path("resena/<uuid:token>/", ResenaSubmitView.as_view(), name="resena_submit"),
    path("gestion-huasco-2026/resenas/", PanelResenasView.as_view(), name="panel_resenas"),
    path("sitemap.xml", sitemap_xml, name="sitemap_xml"),
    path("robots.txt", robots_txt, name="robots_txt"),
]