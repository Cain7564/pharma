"""Envío de alertas de inventario por SMS o WhatsApp (Twilio).

No usa librerías externas. Si faltan las credenciales no se envía nada y se
explica qué falta; nunca se escriben las claves en pantalla ni en los logs.
"""
import base64
import json
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.db.models import F

from .models import Producto

MAX_PRODUCTOS_EN_MENSAJE = 8


class ErrorEnvio(Exception):
    """Algo impidió enviar el mensaje; el texto es seguro para mostrar al personal."""


def productos_en_alerta():
    return Producto.objects.filter(existencias__lte=F("minimo_alerta")).order_by("existencias", "nombre")


def normalizar_telefono(valor):
    """'5555-1234' -> '+50255551234'. Acepta también números ya internacionales (+1...)."""
    limpio = re.sub(r"[\s\-().]", "", str(valor or ""))
    if re.fullmatch(r"\d{8}", limpio):
        limpio = "+502" + limpio
    elif re.fullmatch(r"502\d{8}", limpio):
        limpio = "+" + limpio
    if not re.fullmatch(r"\+\d{8,15}", limpio):
        raise ErrorEnvio(f"El número «{valor}» no es válido. Usa 8 dígitos de Guatemala o formato +código país.")
    return limpio


def configuracion():
    c = settings.ALERTAS
    faltan = []
    if not c["telefonos"]:
        faltan.append("ALERTAS_TELEFONOS")
    for clave, env in (("twilio_sid", "TWILIO_ACCOUNT_SID"), ("twilio_token", "TWILIO_AUTH_TOKEN"),
                       ("twilio_desde", "TWILIO_DESDE")):
        if not c[clave]:
            faltan.append(env)
    return c, faltan


def credenciales_faltantes():
    """Lo que falta para enviar a cualquier número (no exige ALERTAS_TELEFONOS, que es solo para el personal)."""
    return [f for f in configuracion()[1] if f != "ALERTAS_TELEFONOS"]


def sin_acentos(texto):
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()


def construir_mensaje(productos, canal="sms"):
    filas = list(productos)
    if not filas:
        return ""
    lineas = [f"Pharma Del: {len(filas)} medicamento(s) por reponer."]
    for p in filas[:MAX_PRODUCTOS_EN_MENSAJE]:
        estado = "AGOTADO" if p.existencias == 0 else f"{p.existencias} uds (minimo {p.minimo_alerta})"
        lineas.append(f"- {p.nombre}: {estado}")
    if len(filas) > MAX_PRODUCTOS_EN_MENSAJE:
        lineas.append(f"...y {len(filas) - MAX_PRODUCTOS_EN_MENSAJE} mas.")
    texto = "\n".join(lineas)
    if canal == "sms":  # sin acentos para no multiplicar los segmentos del SMS
        texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return texto


def enviar_mensaje(destino, texto):
    """Envía un mensaje con la API de Twilio. Devuelve el SID del mensaje."""
    c, _ = configuracion()
    faltan = credenciales_faltantes()
    if faltan:
        raise ErrorEnvio("Falta configurar: " + ", ".join(faltan) + ".")
    destino = normalizar_telefono(destino)
    desde = c["twilio_desde"]
    if c["canal"] == "whatsapp":
        destino, desde = "whatsapp:" + destino, "whatsapp:" + desde.removeprefix("whatsapp:")
    url = f"https://api.twilio.com/2010-04-01/Accounts/{c['twilio_sid']}/Messages.json"
    datos = urllib.parse.urlencode({"To": destino, "From": desde, "Body": texto}).encode()
    credenciales = base64.b64encode(f"{c['twilio_sid']}:{c['twilio_token']}".encode()).decode()
    peticion = urllib.request.Request(url, data=datos, method="POST",
                                      headers={"Authorization": "Basic " + credenciales})
    try:
        with urllib.request.urlopen(peticion, timeout=15) as r:
            return json.loads(r.read().decode()).get("sid", "")
    except urllib.error.HTTPError as e:
        try:
            detalle = json.loads(e.read().decode()).get("message", "")
        except Exception:
            detalle = ""
        raise ErrorEnvio(f"Twilio rechazó el envío ({e.code}). {detalle}".strip()) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ErrorEnvio("No se pudo conectar con Twilio. Revisa la conexión a internet.") from None


def enviar_alertas(texto=None):
    """Envía el texto (o la alerta de inventario actual) a todos los teléfonos configurados.

    Devuelve (enviados, errores, texto). Si no hay productos en alerta y no se pasa texto, no envía nada.
    """
    c, _ = configuracion()
    if texto is None:
        texto = construir_mensaje(productos_en_alerta(), c["canal"])
    if not texto:
        return [], [], ""
    enviados, errores = [], []
    for numero in c["telefonos"]:
        try:
            enviar_mensaje(numero, texto)
            enviados.append(normalizar_telefono(numero))
        except ErrorEnvio as e:
            errores.append(f"{numero}: {e}")
    return enviados, errores, texto


def enmascarar(numero):
    return "*" * max(len(numero) - 4, 0) + numero[-4:]
