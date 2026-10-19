from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from tienda import views as vistas_tienda

urlpatterns = [
    path(settings.ADMIN_URL + "alertas/chat/", vistas_tienda.alertas_chat, name="alertas_chat"),
    path(settings.ADMIN_URL + "alertas/enviar/", vistas_tienda.alertas_enviar, name="alertas_enviar"),
    # El mapa va antes del panel para que el panel no capture su dirección
    path(settings.ADMIN_URL + "mapa/datos/", vistas_tienda.mapa_datos, name="mapa_datos"),
    path(settings.ADMIN_URL + "mapa/", vistas_tienda.mapa, name="mapa"),
    path(settings.ADMIN_URL, admin.site.urls),  # panel privado (pide usuario y contraseña)
    path("", include("tienda.urls")),           # páginas públicas
]

# Fotos subidas desde el panel. En producción solo se sirven si DJANGO_SERVE_MEDIA=1
# (sirve para poco tráfico con disco persistente; ver README).
if settings.SERVE_MEDIA:
    urlpatterns += [re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT})]

handler404 = "tienda.views.error_404"
