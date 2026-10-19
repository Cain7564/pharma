import re

from django import forms
from django.core.validators import MaxLengthValidator

from .departamentos import DEPARTAMENTOS
from .models import Cadena, Producto, Registro
from .validadores import normalizar_dpi


class RegistroForm(forms.ModelForm):
    # Campo trampa anti-spam (se oculta con CSS; ver registro.html)
    sitio_web = forms.CharField(required=False, widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))

    class Meta:
        model = Registro
        fields = ["nombre", "dpi", "telefono", "correo", "departamento", "cadena", "producto", "acepta_datos"]
        labels = {
            "nombre": "Nombre completo",
            "dpi": "DPI",
            "telefono": "Teléfono",
            "correo": "Correo electrónico",
            "departamento": "Departamento desde donde te registras",
            "producto": "Producto de interés",
            "acepta_datos": "He leído y acepto el aviso de privacidad",
        }
        help_texts = {
            "dpi": "13 dígitos. Lo usamos para confirmar tu identidad y evitar registros duplicados.",
            "departamento": "Nos ayuda a saber en qué zonas hay más interés.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        f = self.fields
        f["cadena"].queryset = Cadena.objects.filter(activa=True)
        f["cadena"].required = True
        f["cadena"].empty_label = "Elige una cadena de farmacias"
        if not f["cadena"].queryset.exists():
            f["cadena"].help_text = "Aún no hay cadenas disponibles. Comunícate con Pharma Del para completar tu registro."
        f["correo"].required = False
        f["correo"].label = "Correo electrónico (opcional)"
        f["correo"].help_text = "Puedes usar Gmail u otro proveedor, o dejarlo vacío."
        f["producto"].queryset = Producto.objects.filter(activo=True)
        f["producto"].required = True
        f["producto"].empty_label = "Elige un producto"
        f["departamento"].required = True
        f["departamento"].choices = [("", "Elige tu departamento")] + list(DEPARTAMENTOS)
        f["dpi"].required = True
        # El DPI puede escribirse con espacios (15 caracteres); el largo real se valida en clean_dpi
        f["dpi"].validators = [v for v in f["dpi"].validators if not isinstance(v, MaxLengthValidator)]
        f["acepta_datos"].required = True
        f["acepta_datos"].error_messages["required"] = (
            "Debes aceptar el aviso de privacidad para poder registrarte."
        )
        f["nombre"].widget.attrs.update({"autocomplete": "name"})
        f["dpi"].widget.attrs.update({"inputmode": "numeric", "placeholder": "0000 00000 0000",
                                      "autocomplete": "off", "maxlength": "16"})
        f["telefono"].widget.attrs.update({"inputmode": "tel", "placeholder": "5555-5555", "autocomplete": "tel"})
        f["correo"].widget.attrs.update({"autocomplete": "email", "placeholder": "nombre@correo.com"})

    def clean_nombre(self):
        nombre = " ".join(self.cleaned_data["nombre"].split())
        if len(nombre) < 3:
            raise forms.ValidationError("Escribe tu nombre completo.")
        return nombre

    def clean_dpi(self):
        return normalizar_dpi(self.cleaned_data["dpi"])

    def clean_telefono(self):
        t = re.sub(r"[\s-]", "", self.cleaned_data["telefono"])
        if t.startswith("+502"):
            t = t[4:]
        elif t.startswith("502") and len(t) == 11:
            t = t[3:]
        if not re.fullmatch(r"\d{8}", t):
            raise forms.ValidationError("Escribe un teléfono de 8 dígitos, por ejemplo 5555-5555.")
        return f"{t[:4]}-{t[4:]}"

    def clean_correo(self):
        return self.cleaned_data["correo"].strip().lower()

    def clean(self):
        datos = super().clean()
        producto = datos.get("producto")
        if producto:
            if datos.get("dpi") and Registro.objects.filter(dpi=datos["dpi"], producto=producto).exists():
                raise forms.ValidationError("Este DPI ya está registrado para ese producto.")
            if datos.get("correo") and Registro.objects.filter(correo=datos["correo"], producto=producto).exists():
                raise forms.ValidationError("Ya tenemos un registro con este correo para ese producto.")
        return datos
