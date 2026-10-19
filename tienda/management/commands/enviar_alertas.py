from django.core.management.base import BaseCommand, CommandError

from tienda import alertas


class Command(BaseCommand):
    help = ("Envía por SMS/WhatsApp la alerta de medicamentos por agotarse a los teléfonos de ALERTAS_TELEFONOS. "
            "Úsalo a mano o prográmalo (Programador de tareas en Windows, cron en Linux).")

    def add_arguments(self, parser):
        parser.add_argument("--probar", action="store_true",
                            help="Envía un mensaje de prueba aunque no haya productos en alerta.")
        parser.add_argument("--simular", action="store_true",
                            help="Muestra el mensaje y los números, pero no envía nada.")

    def handle(self, *args, **opciones):
        config, faltan = alertas.configuracion()
        texto = "Pharma Del: mensaje de prueba del asistente de alertas." if opciones["probar"] else None
        if opciones["simular"]:
            texto = texto or alertas.construir_mensaje(alertas.productos_en_alerta(), config["canal"])
            self.stdout.write(f"Canal: {config['canal']} · Destinos: {', '.join(config['telefonos']) or '(ninguno)'}")
            self.stdout.write(texto or "No hay medicamentos por agotarse.")
            if faltan:
                self.stdout.write(self.style.WARNING("No se enviaría: falta " + ", ".join(faltan)))
            return
        if faltan:
            raise CommandError("Falta configurar: " + ", ".join(faltan) + ". Revisa .env.example.")
        enviados, errores, texto = alertas.enviar_alertas(texto)
        if not texto:
            self.stdout.write("No hay medicamentos por agotarse; no se envió nada.")
            return
        for n in enviados:
            self.stdout.write(self.style.SUCCESS(f"Enviado a {alertas.enmascarar(n)}"))
        if errores:
            raise CommandError("No se pudo enviar a: " + "; ".join(errores))
