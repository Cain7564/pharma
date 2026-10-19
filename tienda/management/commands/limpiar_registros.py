from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from tienda.models import Registro


class Command(BaseCommand):
    help = "Elimina registros de clientes antiguos (cumple lo prometido en el aviso de privacidad)."

    def add_arguments(self, parser):
        parser.add_argument("--dias", type=int, default=365, help="Antigüedad máxima en días (por defecto 365).")
        parser.add_argument("--borrar", action="store_true", help="Sin esta opción solo muestra cuántos se borrarían.")

    def handle(self, *args, **opciones):
        corte = timezone.now() - timedelta(days=opciones["dias"])
        viejos = Registro.objects.filter(creado__lt=corte)
        if opciones["borrar"]:
            self.stdout.write(f"Eliminados: {viejos.delete()[0]} registros.")
        else:
            self.stdout.write(f"Se eliminarían {viejos.count()} registros anteriores a {corte:%Y-%m-%d}. "
                              "Usa --borrar para confirmarlo.")
