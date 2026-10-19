from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("tienda", "0002_registro_departamento_registro_dpi")]
    operations = [
        migrations.CreateModel(
            name="Cadena",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField("nombre", max_length=120, unique=True)),
                ("activa", models.BooleanField("disponible en el registro", default=True)),
            ],
            options={"ordering": ["nombre"], "verbose_name": "cadena de farmacias", "verbose_name_plural": "cadenas de farmacias"},
        ),
        migrations.AddField(model_name="registro", name="cadena", field=models.ForeignKey(
            to="tienda.cadena", verbose_name="cadena de farmacias", null=True, blank=True,
            on_delete=django.db.models.deletion.PROTECT, related_name="registros")),
        migrations.AlterField(model_name="registro", name="correo", field=models.EmailField("correo electrónico", blank=True, default="", max_length=254)),
        migrations.AddField(model_name="producto", name="existencias", field=models.PositiveIntegerField(
            "existencias", null=True, blank=True, help_text="Unidades disponibles. Vacío significa inventario pendiente de registrar.")),
        migrations.AddField(model_name="producto", name="minimo_alerta", field=models.PositiveIntegerField(
            "mínimo de alerta", default=10, help_text="Se genera una alerta cuando las existencias son iguales o inferiores a este valor.")),
    ]
