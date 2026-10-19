import re

from django.core.exceptions import ValidationError


def digito_verificador(primeros_8):
    """Dígito verificador del DPI (CUI): suma ponderada de los 8 primeros dígitos, módulo 11."""
    return sum(int(d) * (i + 2) for i, d in enumerate(primeros_8)) % 11


def normalizar_dpi(valor):
    """Quita espacios y guiones, valida el DPI de 13 dígitos y lo devuelve sin separadores."""
    dpi = re.sub(r"[\s-]", "", valor or "")
    if not re.fullmatch(r"\d{13}", dpi):
        raise ValidationError("El DPI debe tener 13 dígitos, por ejemplo 2345 67890 0101.")
    if digito_verificador(dpi[:8]) != int(dpi[8]):
        raise ValidationError("El número de DPI no es válido. Revísalo e inténtalo de nuevo.")
    if not 1 <= int(dpi[9:11]) <= 22 or int(dpi[11:]) < 1:
        raise ValidationError("El número de DPI no es válido. Revísalo e inténtalo de nuevo.")
    return dpi
