import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Crea el usuario del panel con DJANGO_SUPERUSER_USERNAME / _PASSWORD / _EMAIL "
        "si no existe (no cambia la contraseña de un usuario existente). Pensado para el hosting."
    )

    def handle(self, *args, **opciones):
        usuario = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
        clave = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        correo = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
        if not clave:
            self.stdout.write("Sin DJANGO_SUPERUSER_PASSWORD: no se crea usuario del panel.")
            return
        User = get_user_model()
        if User.objects.filter(**{User.USERNAME_FIELD: usuario}).exists():
            self.stdout.write(f"El usuario «{usuario}» ya existe; no se modifica.")
            return
        User.objects.create_superuser(usuario, correo, clave)
        self.stdout.write(f"Usuario del panel «{usuario}» creado.")
