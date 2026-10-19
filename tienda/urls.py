from django.contrib.sitemaps.views import sitemap
from django.urls import path

from . import views
from .sitemaps import PaginasSitemap

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("productos/", views.catalogo, name="catalogo"),
    path("como-funciona/", views.como_funciona, name="como_funciona"),
    path("registro/", views.registro, name="registro"),
    path("gracias/", views.gracias, name="gracias"),
    path("privacidad/", views.privacidad, name="privacidad"),
    path("robots.txt", views.robots, name="robots"),
    path("sitemap.xml", sitemap, {"sitemaps": {"paginas": PaginasSitemap}}, name="sitemap"),
]
