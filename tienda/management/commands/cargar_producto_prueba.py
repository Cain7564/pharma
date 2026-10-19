from django.core.management.base import BaseCommand

from tienda.models import Producto


class Command(BaseCommand):
    help = ("Crea (o restablece) un producto de prueba de 30 pastillas para comprobar las alertas. "
            "Por defecto queda en el mínimo de alerta, así aparece de inmediato como «Por agotarse».")

    def add_arguments(self, parser):
        parser.add_argument("--existencias", type=int, default=30)
        parser.add_argument("--minimo", type=int, default=30)
        parser.add_argument("--telefono", help="Crea un cliente de prueba con este número y un tratamiento de 30 tabletas "
                                               "(1 al día) que empezó hace 25 días: ya le quedan 5 y toca avisarle.")
        parser.add_argument("--nombre", default="Prueba recordatorio")

    def handle(self, *args, **o):
        p, creado = Producto.objects.get_or_create(
            nombre="Paracetamol 500 mg (prueba)",
            defaults={"descripcion": "Caja con 30 pastillas."},
        )
        p.existencias, p.minimo_alerta = o["existencias"], o["minimo"]
        p.save()
        self.stdout.write(("Creado" if creado else "Restablecido") +
                          f": {p.nombre} · {p.existencias} unidades · mínimo de alerta {p.minimo_alerta}")
        if o["telefono"]:
            from datetime import timedelta

            from django.utils import timezone

            from tienda.models import Registro, Tratamiento
            tel = o["telefono"]
            r, _ = Registro.objects.get_or_create(nombre=o["nombre"], telefono=tel, defaults={"producto": p})
            Tratamiento.objects.filter(registro=r, producto=p).delete()
            Tratamiento.objects.create(registro=r, producto=p, tabletas=30, por_dia=1, avisar_con=5, autorizado=True,
                                       fecha_inicio=timezone.localdate() - timedelta(days=25))
            self.stdout.write(f"Cliente de prueba «{r.nombre}» ({r.telefono}) con 5 tabletas restantes. "
                              "Ahora corre: python manage.py enviar_recordatorios")
