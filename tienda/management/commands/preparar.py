from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key

from config.settings import BASE_DIR
from tienda.models import Producto


class Command(BaseCommand):
    help = "Prepara el proyecto en tu computadora: .env, base de datos, usuario del panel y productos de ejemplo."

    def handle(self, *args, **opciones):
        env = BASE_DIR / ".env"
        if not env.exists():
            env.write_text(
                "# Configuración local (no la compartas ni la subas a internet)\n"
                f"DJANGO_SECRET_KEY={get_random_secret_key()}\n"
                "DJANGO_DEBUG=1\n",
                encoding="utf-8",
            )
            self.stdout.write("Creado el archivo .env")

        call_command("migrate", verbosity=0)

        if not get_user_model().objects.filter(is_superuser=True).exists():
            self.stdout.write("\nCrea tu usuario para el panel privado (la contraseña no se ve al escribirla):")
            call_command("createsuperuser")

        if not Producto.objects.exists():
            call_command("cargar_ejemplos", verbosity=0)
            self.stdout.write("Cargados productos de ejemplo (puedes editarlos o borrarlos en el panel).")
