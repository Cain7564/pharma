from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class PaginasSitemap(Sitemap):
    """Lista de páginas públicas para buscadores (/sitemap.xml)."""
    changefreq = "weekly"

    def items(self):
        return ["inicio", "catalogo", "como_funciona", "registro", "privacidad"]

    def location(self, nombre):
        return reverse(nombre)
