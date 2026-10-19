from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from .departamentos import DEPARTAMENTOS


class Cadena(models.Model):
    nombre = models.CharField("nombre", max_length=120, unique=True)
    activa = models.BooleanField("disponible en el registro", default=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "cadena de farmacias"
        verbose_name_plural = "cadenas de farmacias"

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField("nombre", max_length=120)
    descripcion = models.TextField("descripción")
    foto = models.ImageField("foto", upload_to="productos/", blank=True)
    condiciones = models.TextField(
        "condiciones de la promoción",
        default="Compra 1 y recibe otro igual gratis. Válido hasta agotar existencias.",
    )
    activo = models.BooleanField("visible en el catálogo", default=True)
    existencias = models.PositiveIntegerField("existencias", null=True, blank=True,
        help_text="Unidades disponibles. Vacío significa inventario pendiente de registrar.")
    minimo_alerta = models.PositiveIntegerField("mínimo de alerta", default=10,
        help_text="Se genera una alerta cuando las existencias son iguales o inferiores a este valor.")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "producto"
        verbose_name_plural = "productos"

    def __str__(self):
        return self.nombre


class Registro(models.Model):
    nombre = models.CharField("nombre", max_length=120)
    dpi = models.CharField("DPI", max_length=13, blank=True, default="")
    telefono = models.CharField("teléfono", max_length=20)
    correo = models.EmailField("correo electrónico", blank=True, default="")
    cadena = models.ForeignKey(Cadena, verbose_name="cadena de farmacias", null=True,
        blank=True, on_delete=models.PROTECT, related_name="registros")
    departamento = models.CharField(
        "departamento del registro", max_length=20, choices=DEPARTAMENTOS, blank=True, default="",
    )
    producto = models.ForeignKey(
        Producto, verbose_name="producto de interés", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="registros",
    )
    acepta_datos = models.BooleanField("aceptó el aviso de datos personales", default=False)
    creado = models.DateTimeField("fecha de registro", auto_now_add=True)

    class Meta:
        ordering = ["-creado"]
        verbose_name = "registro de cliente"
        verbose_name_plural = "registros de clientes"

    def __str__(self):
        return f"{self.nombre} ({self.correo or self.telefono})"

    @property
    def dpi_enmascarado(self):
        """DPI con solo los últimos 4 dígitos visibles (para listados y exportaciones)."""
        return "*" * 9 + self.dpi[-4:] if self.dpi else ""


class Tratamiento(models.Model):
    """Medicamento que lleva un cliente: sirve para avisarle cuando le queden pocas tabletas."""

    registro = models.ForeignKey(Registro, verbose_name="cliente", on_delete=models.CASCADE, related_name="tratamientos")
    producto = models.ForeignKey(Producto, verbose_name="medicamento", on_delete=models.CASCADE, related_name="tratamientos")
    tabletas = models.PositiveIntegerField("tabletas en el empaque", validators=[MinValueValidator(1)], default=30)
    por_dia = models.PositiveIntegerField("tabletas por día", validators=[MinValueValidator(1)], default=1)
    fecha_inicio = models.DateField("fecha en que empieza a tomarlas", default=timezone.localdate,
        help_text="Se cuenta una dosis por cada día transcurrido desde esta fecha.")
    avisar_con = models.PositiveIntegerField("avisar cuando queden", default=5, help_text="Número de tabletas restantes.")
    autorizado = models.BooleanField("el cliente aceptó recibir este aviso por mensaje", default=False,
        help_text="Sin esta marca no se envía nada.")
    aviso_enviado_en = models.DateTimeField("aviso enviado", null=True, blank=True, editable=False)
    creado = models.DateTimeField(auto_now_add=True)

    # Si el sistema estuvo apagado y el medicamento terminó hace más de estos días, el aviso ya no sirve.
    MAX_DIAS_TARDE = 3

    class Meta:
        ordering = ["-creado"]
        verbose_name = "tratamiento de cliente"
        verbose_name_plural = "tratamientos de clientes"

    def __str__(self):
        return f"{self.producto} · {self.registro.nombre}"

    def clean(self):
        if self.tabletas and self.avisar_con is not None and self.avisar_con >= self.tabletas:
            raise ValidationError({"avisar_con": "Debe ser menor que el total de tabletas."})

    def _dias(self, hoy=None):
        return max(((hoy or timezone.localdate()) - self.fecha_inicio).days, 0)

    def restantes(self, hoy=None):
        return max(self.tabletas - self._dias(hoy) * self.por_dia, 0)

    @property
    def fecha_aviso(self):
        dias = -(-(self.tabletas - self.avisar_con) // self.por_dia)  # división hacia arriba
        return self.fecha_inicio + timedelta(days=dias)

    @property
    def fecha_fin(self):
        return self.fecha_inicio + timedelta(days=-(-self.tabletas // self.por_dia))

    def toca_avisar(self, hoy=None):
        hoy = hoy or timezone.localdate()
        return (self.autorizado and self.aviso_enviado_en is None and hoy >= self.fecha_aviso
                and hoy <= self.fecha_fin + timedelta(days=self.MAX_DIAS_TARDE))

    def estado(self, hoy=None):
        hoy = hoy or timezone.localdate()
        if self.aviso_enviado_en:
            return "Aviso enviado"
        if not self.autorizado:
            return "Sin autorización del cliente"
        if hoy > self.fecha_fin + timedelta(days=self.MAX_DIAS_TARDE):
            return "Vencido sin aviso"
        return "Aviso pendiente de enviar" if hoy >= self.fecha_aviso else f"En curso (aviso el {self.fecha_aviso:%d/%m/%Y})"
