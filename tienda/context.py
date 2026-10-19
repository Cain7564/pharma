from django.conf import settings


def empresa(request):
    """Pone los datos de la empresa (settings.EMPRESA) en todas las plantillas."""
    return {"empresa": settings.EMPRESA}


def panel_resumen(request):
    if not request.user.is_active or not request.user.is_staff:
        return {}
    from django.db.models import F
    from .models import Producto, Registro, Cadena
    datos = {}
    if request.user.has_perm("tienda.view_producto"):
        datos.update(panel_productos=Producto.objects.count(),
            panel_alertas=Producto.objects.filter(existencias__lte=F("minimo_alerta")).count(),
            panel_pendientes=Producto.objects.filter(existencias__isnull=True).count())
    if request.user.has_perm("tienda.view_registro"):
        datos["panel_registros"] = Registro.objects.count()
    if request.user.has_perm("tienda.view_cadena"):
        datos["panel_cadenas"] = Cadena.objects.filter(activa=True).count()
    return datos
