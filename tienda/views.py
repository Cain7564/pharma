from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from django.utils import timezone

from .departamentos import DEPARTAMENTOS

from . import alertas
from .forms import RegistroForm
from .models import Producto, Registro


def inicio(request):
    destacados = Producto.objects.filter(activo=True)[:3]
    return render(request, "tienda/inicio.html", {"destacados": destacados})


def catalogo(request):
    productos = Producto.objects.filter(activo=True)
    return render(request, "tienda/catalogo.html", {"productos": productos})


def registro(request):
    if request.method == "POST":
        # Campo trampa para bots: las personas no lo ven ni lo llenan
        if request.POST.get("sitio_web"):
            return redirect("gracias")
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("gracias")
    else:
        # /registro/?producto=3 deja el producto ya elegido
        form = RegistroForm(initial={"producto": request.GET.get("producto")})
    return render(request, "tienda/registro.html", {"form": form})


def gracias(request):
    return render(request, "tienda/gracias.html")


def como_funciona(request):
    return render(request, "tienda/como_funciona.html")


def privacidad(request):
    return render(request, "tienda/privacidad.html")


def robots(request):
    texto = (
        "User-agent: *\n"
        f"Disallow: /{settings.ADMIN_URL}\n"
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml\n"
    )
    return HttpResponse(texto, content_type="text/plain")


def error_404(request, exception):
    return render(request, "404.html", status=404)


# ----------------------------------------------------------------------
# Mapa de productos por departamento (solo personal con permiso)
# ----------------------------------------------------------------------
def solo_personal(vista):
    """Exige iniciar sesión en el panel y tener permiso para ver los registros."""
    @staff_member_required
    @wraps(vista)
    def protegida(request, *args, **kwargs):
        if not request.user.has_perm("tienda.view_registro"):
            raise PermissionDenied
        return vista(request, *args, **kwargs)
    return protegida


@solo_personal
def mapa(request):
    contexto = {**admin.site.each_context(request), "title": "Mapa de productos por departamento"}
    return render(request, "tienda/mapa.html", contexto)


@solo_personal
def mapa_datos(request):
    """Cantidad de registros por departamento y producto (solo cifras, sin datos personales)."""
    registros = Registro.objects.exclude(departamento="").exclude(producto=None)
    dias = request.GET.get("dias", "")
    if dias in ("30", "90"):
        registros = registros.filter(creado__gte=timezone.now() - timedelta(days=int(dias)))

    departamentos = {slug: {"nombre": n, "total": 0, "productos": {}} for slug, n in DEPARTAMENTOS}
    for fila in registros.values("departamento", "producto_id").annotate(n=Count("id")):
        d = departamentos.get(fila["departamento"])
        if d:
            d["productos"][str(fila["producto_id"])] = fila["n"]
            d["total"] += fila["n"]

    return JsonResponse({
        "productos": [{"id": p.id, "nombre": p.nombre} for p in Producto.objects.all()],
        "departamentos": departamentos,
        "total": sum(d["total"] for d in departamentos.values()),
    })


@staff_member_required
def alertas_chat(request):
    """Asistente informativo de inventario; no cambia existencias ni da consejo médico."""
    if not request.user.has_perm("tienda.view_producto"):
        raise PermissionDenied
    from django.db.models import F
    consulta = request.GET.get("q", "alertas").strip()[:120]
    productos = Producto.objects.all()
    comando = consulta.casefold()
    if comando in ("alertas", "", "bajo stock"):
        productos = productos.filter(existencias__lte=F("minimo_alerta"))
        mensaje = "Medicamentos que necesitan reposición."
    elif comando in ("agotados", "sin existencias"):
        productos = productos.filter(existencias=0)
        mensaje = "Medicamentos agotados."
    elif comando in ("pendientes", "sin inventario"):
        productos = productos.filter(existencias__isnull=True)
        mensaje = "Registra las existencias de estos medicamentos para activar sus alertas."
    else:
        productos = productos.filter(nombre__icontains=consulta)
        mensaje = "Resultado de la búsqueda por nombre."
    total = productos.count()
    filas = [{"nombre": p.nombre, "existencias": p.existencias, "minimo": p.minimo_alerta,
              "estado": "Sin inventario" if p.existencias is None else
              "Agotado" if p.existencias == 0 else
              "Por agotarse" if p.existencias <= p.minimo_alerta else "Disponible"}
             for p in productos[:50]]
    respuesta = JsonResponse({"mensaje": mensaje if total else "No hay resultados para esta consulta.",
        "productos": filas, "total": total,
        "pendientes": Producto.objects.filter(existencias__isnull=True).count()})
    respuesta["Cache-Control"] = "no-store"
    return respuesta


@staff_member_required
@require_POST
def alertas_enviar(request):
    """Envía por SMS/WhatsApp la alerta de inventario actual a los teléfonos configurados."""
    from django.core.cache import cache
    if not request.user.has_perm("tienda.view_producto"):
        raise PermissionDenied
    config, faltan = alertas.configuracion()
    if faltan:
        return JsonResponse({"ok": False, "mensaje": "Aún no está configurado el envío. Falta: " + ", ".join(faltan) + "."})
    if not cache.add("alertas_envio_reciente", 1, timeout=30):  # evita envíos repetidos por clics seguidos
        return JsonResponse({"ok": False, "mensaje": "Ya se envió una alerta hace unos segundos. Espera 30 s."})
    enviados, errores, texto = alertas.enviar_alertas()
    if not texto:
        cache.delete("alertas_envio_reciente")
        return JsonResponse({"ok": True, "mensaje": "No hay medicamentos por agotarse; no se envió ningún mensaje."})
    partes = []
    if enviados:
        partes.append("Alerta enviada a " + ", ".join(alertas.enmascarar(n) for n in enviados) + ".")
    partes += errores
    respuesta = JsonResponse({"ok": bool(enviados) and not errores, "mensaje": " ".join(partes)})
    respuesta["Cache-Control"] = "no-store"
    return respuesta
