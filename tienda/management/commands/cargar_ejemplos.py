from django.core.management.base import BaseCommand

from tienda.models import Producto

EJEMPLOS = [
    ("Vitamina C 500 mg", "Frasco de 60 tabletas."),
    ("Multivitamínico diario", "Frasco de 90 tabletas."),
    ("Omega 3", "Frasco de 60 cápsulas."),
    ("Protector solar FPS 50", "Tubo de 120 ml."),
    ("Crema hidratante", "Pote de 250 g."),
    ("Sales de rehidratación", "Caja de 6 sobres."),
]


class Command(BaseCommand):
    help = "Crea productos de ejemplo (puedes editarlos o borrarlos desde el panel)."

    def handle(self, *args, **opciones):
        for nombre, descripcion in EJEMPLOS:
            _, creado = Producto.objects.get_or_create(nombre=nombre, defaults={"descripcion": descripcion})
            self.stdout.write(("Creado: " if creado else "Ya existía: ") + nombre)
