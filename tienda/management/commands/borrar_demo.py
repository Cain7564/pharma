from django.core.management.base import BaseCommand

from tienda.models import Registro


class Command(BaseCommand):
    help = "Borra los registros ficticios creados con cargar_demo."

    def handle(self, *args, **opciones):
        n = Registro.objects.filter(correo__endswith="@demo.invalid").delete()[0]
        self.stdout.write(f"Eliminados {n} registros de demostración.")
