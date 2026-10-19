"""Avisos a clientes cuando a su medicamento le quedan pocas tabletas."""
from django.utils import timezone

from . import alertas
from .models import Tratamiento


def construir_mensaje(t, hoy=None):
    n = t.restantes(hoy)
    nombre = t.registro.nombre.split()[0]
    if n == 0:
        cuerpo = f"ya terminaste las tabletas de {t.producto.nombre}"
    elif n == 1:
        cuerpo = f"te queda 1 tableta de {t.producto.nombre}"
    else:
        cuerpo = f"te quedan {n} tabletas de {t.producto.nombre}"
    texto = (f"Hola {nombre}, te escribe Pharma Del: {cuerpo}. Es buen momento para reponerlo. "
             "Si no deseas recibir estos avisos, comunicate con Pharma Del.")
    return alertas.sin_acentos(texto) if alertas.configuracion()[0]["canal"] == "sms" else texto


def pendientes(hoy=None, queryset=None):
    hoy = hoy or timezone.localdate()
    base = queryset if queryset is not None else Tratamiento.objects.all()
    base = base.filter(autorizado=True, aviso_enviado_en__isnull=True).select_related("registro", "producto")
    return [t for t in base if t.toca_avisar(hoy)]


def procesar(hoy=None, queryset=None):
    """Envía los avisos que toquen. Devuelve (enviados, errores) como listas de texto."""
    hoy = hoy or timezone.localdate()
    enviados, errores = [], []
    for t in pendientes(hoy, queryset):
        # Se "reserva" el aviso antes de enviar para que dos procesos a la vez no manden el mismo mensaje dos veces.
        if not Tratamiento.objects.filter(pk=t.pk, aviso_enviado_en__isnull=True).update(aviso_enviado_en=timezone.now()):
            continue
        try:
            alertas.enviar_mensaje(t.registro.telefono, construir_mensaje(t, hoy))
            enviados.append(f"{t.registro.nombre} ({alertas.enmascarar(alertas.normalizar_telefono(t.registro.telefono))}) · {t.producto}")
        except alertas.ErrorEnvio as e:
            Tratamiento.objects.filter(pk=t.pk).update(aviso_enviado_en=None)  # se reintentará en la próxima revisión
            errores.append(f"{t.registro.nombre}: {e}")
    return enviados, errores
