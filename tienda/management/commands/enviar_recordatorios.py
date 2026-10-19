import time

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from tienda import alertas, recordatorios


class Command(BaseCommand):
    help = ("Envía por SMS/WhatsApp el aviso a los clientes a quienes ya les quedan pocas tabletas. "
            "Con --cada SEGUNDOS se queda corriendo y revisa de forma periódica.")

    def add_arguments(self, parser):
        parser.add_argument("--simular", action="store_true", help="Muestra qué se enviaría, sin enviar.")
        parser.add_argument("--cada", type=int, default=0, metavar="SEGUNDOS",
                            help="Repite la revisión continuamente (ej: 3600 = cada hora). Ctrl+C para detener.")

    def handle(self, *args, **o):
        if o["simular"]:
            lista = recordatorios.pendientes()
            for t in lista:
                self.stdout.write(f"A {t.registro.nombre} ({t.registro.telefono}): {recordatorios.construir_mensaje(t)}")
            self.stdout.write(f"{len(lista)} aviso(s) pendiente(s). No se envió nada.")
            return
        faltan = alertas.credenciales_faltantes()
        if faltan and not o["cada"]:
            raise CommandError("Falta configurar: " + ", ".join(faltan) + ". Revisa .env.example.")
        while True:
            hora = timezone.localtime().strftime("%d/%m %H:%M")
            if faltan:
                self.stdout.write(self.style.WARNING(f"[{hora}] Sin configurar Twilio, no se envía nada. Falta: {', '.join(faltan)}"))
            else:
                enviados, errores = recordatorios.procesar()
                for e in enviados:
                    self.stdout.write(self.style.SUCCESS(f"[{hora}] Aviso enviado a {e}"))
                for e in errores:
                    self.stderr.write(f"[{hora}] No se pudo enviar: {e}")
                if not enviados and not errores:
                    self.stdout.write(f"[{hora}] Sin avisos pendientes.")
            if not o["cada"]:
                break
            try:
                time.sleep(o["cada"])
            except KeyboardInterrupt:
                self.stdout.write("Detenido.")
                break
