import csv

from django.contrib import admin, messages
from django.utils import timezone
from django.http import HttpResponse

from . import alertas, recordatorios
from .models import Cadena, Producto, Registro, Tratamiento

admin.site.site_header = "Pharma Del · Panel privado"
admin.site.site_title = "Panel Pharma Del"
admin.site.index_title = "Administración"
admin.site.index_template = "admin/index_pharma.html"  # agrega el acceso al mapa


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "existencias", "minimo_alerta", "activo", "creado")
    list_editable = ("existencias", "minimo_alerta", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "descripcion")


def _seguro(valor):
    """Evita que Excel interprete un texto como fórmula (=, +, -, @)."""
    valor = str(valor)
    return "'" + valor if valor[:1] in "=+-@" else valor


class TratamientoInline(admin.TabularInline):
    model = Tratamiento
    extra = 0
    autocomplete_fields = ("producto",)
    fields = ("producto", "tabletas", "por_dia", "fecha_inicio", "avisar_con", "autorizado", "aviso_enviado_en")
    readonly_fields = ("aviso_enviado_en",)


@admin.register(Registro)
class RegistroAdmin(admin.ModelAdmin):
    list_display = ("nombre", "dpi_enmascarado", "telefono", "correo", "departamento", "cadena", "producto", "creado")
    list_filter = ("producto", "departamento", "cadena", "creado")
    search_fields = ("nombre", "correo", "telefono", "dpi", "cadena__nombre")
    list_select_related = ("producto", "cadena")
    date_hierarchy = "creado"
    readonly_fields = ("creado", "acepta_datos")
    inlines = [TratamientoInline]
    actions = ["exportar_csv"]

    @admin.display(description="DPI")
    def dpi_enmascarado(self, obj):
        return obj.dpi_enmascarado

    def has_add_permission(self, request):
        return False  # los registros solo llegan desde el formulario público

    @admin.action(description="Exportar registros seleccionados a CSV")
    def exportar_csv(self, request, queryset):
        respuesta = HttpResponse(content_type="text/csv; charset=utf-8")
        respuesta["Content-Disposition"] = 'attachment; filename="registros.csv"'
        respuesta.write("\ufeff")  # para que Excel muestre bien los acentos
        w = csv.writer(respuesta)
        w.writerow(["Nombre", "DPI (enmascarado)", "Teléfono", "Correo", "Departamento", "Cadena", "Producto", "Fecha"])
        for r in queryset.select_related("producto", "cadena"):
            w.writerow([_seguro(r.nombre), r.dpi_enmascarado, _seguro(r.telefono), _seguro(r.correo),
                        r.get_departamento_display(), _seguro(r.cadena or "Sin cadena (registro anterior)"), _seguro(r.producto or ""),
                        r.creado.strftime("%Y-%m-%d %H:%M")])
        return respuesta


@admin.register(Cadena)
class CadenaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activa")
    list_editable = ("activa",)
    search_fields = ("nombre",)
    list_filter = ("activa",)


@admin.register(Tratamiento)
class TratamientoAdmin(admin.ModelAdmin):
    list_display = ("registro", "producto", "tabletas", "por_dia", "restantes_hoy", "fecha_aviso", "estado_aviso")
    list_filter = ("autorizado", "producto")
    search_fields = ("registro__nombre", "registro__telefono", "producto__nombre")
    autocomplete_fields = ("registro", "producto")
    list_select_related = ("registro", "producto")
    actions = ["enviar_avisos_ahora"]

    @admin.display(description="Tabletas restantes hoy")
    def restantes_hoy(self, obj):
        return obj.restantes()

    @admin.display(description="Aviso desde")
    def fecha_aviso(self, obj):
        return obj.fecha_aviso

    @admin.display(description="Estado")
    def estado_aviso(self, obj):
        return obj.estado()

    @admin.action(description="Enviar ahora los avisos que ya correspondan", permissions=["change"])
    def enviar_avisos_ahora(self, request, queryset):
        faltan = alertas.credenciales_faltantes()
        if faltan:
            self.message_user(request, "No se envió nada. Falta configurar: " + ", ".join(faltan) + ".", messages.ERROR)
            return
        enviados, errores = recordatorios.procesar(queryset=queryset)
        if enviados:
            self.message_user(request, "Avisos enviados: " + "; ".join(enviados), messages.SUCCESS)
        for e in errores:
            self.message_user(request, "No se pudo enviar: " + e, messages.ERROR)
        if not enviados and not errores:
            self.message_user(request, "Ninguno de los seleccionados está listo para aviso (revisa autorización, fecha y si ya se envió).", messages.WARNING)
