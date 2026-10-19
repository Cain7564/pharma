import random
from datetime import timedelta

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from tienda.departamentos import DEPARTAMENTOS
from tienda.models import Producto, Registro
from tienda.validadores import digito_verificador


def dpi_de_prueba(rng):
    base = "".join(str(rng.randint(0, 9)) for _ in range(8))
    return f"{base}{digito_verificador(base)}{rng.randint(1, 22):02d}{rng.randint(1, 5):02d}"


class Command(BaseCommand):
    help = "Crea registros FICTICIOS para ver el mapa funcionando (solo en tu computadora). Bórralos con borrar_demo."

    def add_arguments(self, parser):
        parser.add_argument("--cantidad", type=int, default=150)

    def handle(self, *args, **opciones):
        if not settings.DEBUG:
            raise CommandError("Este comando es solo para pruebas locales (DEBUG=1).")
        if not Producto.objects.exists():
            call_command("cargar_ejemplos", verbosity=0)
        rng = random.Random(7)
        productos = list(Producto.objects.filter(activo=True))
        # Cada departamento "prefiere" más a unos productos que a otros
        pesos = {d: [rng.random() ** 2 + 0.05 for _ in productos] for d, _ in DEPARTAMENTOS}
        creados = 0
        for n in range(opciones["cantidad"]):
            depto = rng.choice([d for d, _ in DEPARTAMENTOS])
            producto = rng.choices(productos, weights=pesos[depto])[0]
            r = Registro.objects.create(
                nombre=f"Cliente demo {n + 1}", dpi=dpi_de_prueba(rng), telefono=f"5555-{n:04d}",
                correo=f"demo{n + 1}@demo.invalid", departamento=depto, producto=producto, acepta_datos=True,
            )
            Registro.objects.filter(pk=r.pk).update(creado=timezone.now() - timedelta(days=rng.randint(0, 120)))
            creados += 1
        self.stdout.write(f"Creados {creados} registros de demostración. Para borrarlos: python manage.py borrar_demo")
