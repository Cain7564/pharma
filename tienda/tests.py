from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Cadena, Producto, Registro
from .validadores import digito_verificador


def dpi_valido(base='23456789', depto='01', muni='01'):
    return f"{base}{digito_verificador(base)}{depto}{muni}"


class PaginasTest(TestCase):
    def setUp(self):
        self.producto = Producto.objects.create(nombre="Vitamina C", descripcion="Frasco")

    def test_paginas_publicas_cargan(self):
        for nombre in ["inicio", "catalogo", "como_funciona", "registro", "gracias", "privacidad"]:
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 200, nombre)

    def test_catalogo_oculta_productos_inactivos(self):
        Producto.objects.create(nombre="Oculto", descripcion="x", activo=False)
        r = self.client.get(reverse("catalogo"))
        self.assertContains(r, "Vitamina C")
        self.assertNotContains(r, "Oculto")


class RegistroTest(TestCase):
    def setUp(self):
        self.producto = Producto.objects.create(nombre="Vitamina C", descripcion="Frasco")
        self.cadena = Cadena.objects.create(nombre="Cadena de prueba")
        self.datos = {"cadena": self.cadena.pk, "nombre": "Ana López", "dpi": dpi_valido(), "telefono": "5555 1234",
                      "correo": "ANA@correo.com", "departamento": "quetzaltenango",
                      "producto": self.producto.id, "acepta_datos": "on"}

    def test_registro_valido_se_guarda_normalizado(self):
        r = self.client.post(reverse("registro"), self.datos)
        self.assertRedirects(r, reverse("gracias"))
        reg = Registro.objects.get()
        self.assertEqual((reg.telefono, reg.correo), ("5555-1234", "ana@correo.com"))
        self.assertEqual((reg.departamento, reg.dpi), ("quetzaltenango", dpi_valido()))
        self.assertTrue(reg.dpi_enmascarado.startswith("*********"))
        self.assertNotIn(reg.dpi[:9], reg.dpi_enmascarado)

    def test_telefono_invalido(self):
        r = self.client.post(reverse("registro"), {**self.datos, "telefono": "123"})
        self.assertEqual(Registro.objects.count(), 0)
        self.assertContains(r, "8 dígitos")

    def test_exige_aceptar_aviso(self):
        datos = {k: v for k, v in self.datos.items() if k != "acepta_datos"}
        self.client.post(reverse("registro"), datos)
        self.assertEqual(Registro.objects.count(), 0)

    def test_evita_duplicados(self):
        self.client.post(reverse("registro"), self.datos)
        self.client.post(reverse("registro"), self.datos)
        self.assertEqual(Registro.objects.count(), 1)


class PanelTest(TestCase):
    def test_panel_pide_login(self):
        r = self.client.get("/panel/tienda/registro/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/panel/login/", r["Location"])

    def test_usuario_sin_permisos_no_entra(self):
        User.objects.create_user("cliente", password="x12345678")
        self.client.login(username="cliente", password="x12345678")
        self.assertEqual(self.client.get("/panel/tienda/registro/").status_code, 302)

    def test_admin_ve_registros(self):
        User.objects.create_superuser("admin", "a@a.com", "x12345678")
        self.client.login(username="admin", password="x12345678")
        self.assertEqual(self.client.get("/panel/tienda/registro/").status_code, 200)


class ProduccionTest(TestCase):
    def test_robots_oculta_el_panel(self):
        r = self.client.get("/robots.txt")
        self.assertContains(r, "Disallow: /panel/")

    def test_sitemap(self):
        r = self.client.get("/sitemap.xml")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "/productos/")

    def test_pagina_404(self):
        with self.settings(DEBUG=False):
            r = self.client.get("/no-existe/")
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, "No encontramos", status_code=404)

    def test_campo_trampa_no_guarda(self):
        p = Producto.objects.create(nombre="X", descripcion="y")
        r = self.client.post(reverse("registro"), {
            "nombre": "Bot Spam", "telefono": "55551234", "correo": "b@b.com",
            "producto": p.id, "acepta_datos": "on", "sitio_web": "http://spam"})
        self.assertRedirects(r, reverse("gracias"))
        self.assertEqual(Registro.objects.count(), 0)


class DpiYDepartamentoTest(TestCase):
    def setUp(self):
        self.producto = Producto.objects.create(nombre="Omega 3", descripcion="x")
        self.cadena = Cadena.objects.create(nombre="Cadena de prueba")
        self.datos = {"cadena": self.cadena.pk, "nombre": "Luis Pérez", "dpi": dpi_valido(), "telefono": "55551234",
                      "correo": "luis@correo.com", "departamento": "peten",
                      "producto": self.producto.id, "acepta_datos": "on"}

    def enviar(self, **cambios):
        return self.client.post(reverse("registro"), {**self.datos, **cambios})

    def test_dpi_con_espacios_se_normaliza(self):
        d = dpi_valido()
        self.enviar(dpi=f"{d[:4]} {d[4:9]} {d[9:]}")
        self.assertEqual(Registro.objects.get().dpi, d)

    def test_dpi_con_digito_verificador_malo(self):
        malo = dpi_valido()[:8] + str((int(dpi_valido()[8]) + 1) % 10) + "0101"
        self.assertContains(self.enviar(dpi=malo), "no es válido")
        self.assertEqual(Registro.objects.count(), 0)

    def test_dpi_con_largo_incorrecto_o_letras(self):
        for valor in ["123", "ABCD123456789", ""]:
            self.enviar(dpi=valor)
        self.assertEqual(Registro.objects.count(), 0)

    def test_departamento_obligatorio_y_valido(self):
        self.enviar(departamento="")
        self.enviar(departamento="atlantis")
        self.assertEqual(Registro.objects.count(), 0)

    def test_mismo_dpi_y_producto_no_se_repite(self):
        self.enviar()
        r = self.enviar(correo="otro@correo.com")
        self.assertContains(r, "ya está registrado")
        self.assertEqual(Registro.objects.count(), 1)


class MapaTest(TestCase):
    def setUp(self):
        self.a = Producto.objects.create(nombre="Vitamina C", descripcion="x")
        self.b = Producto.objects.create(nombre="Omega 3", descripcion="x")
        for i, (depto, prod) in enumerate([("peten", self.a), ("peten", self.a), ("peten", self.b), ("jalapa", self.b)]):
            Registro.objects.create(nombre=f"C{i}", dpi=dpi_valido(f"2345678{i}"), telefono="5555-0000",
                                    correo=f"c{i}@x.com", departamento=depto, producto=prod, acepta_datos=True)

    def test_exige_sesion(self):
        for url in ["/panel/mapa/", "/panel/mapa/datos/"]:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 302)
            self.assertIn("/panel/login/", r["Location"])

    def test_personal_sin_permiso_recibe_403(self):
        User.objects.create_user("empleado", password="x12345678", is_staff=True)
        self.client.login(username="empleado", password="x12345678")
        self.assertEqual(self.client.get("/panel/mapa/datos/").status_code, 403)

    def test_datos_por_departamento(self):
        User.objects.create_superuser("admin", "a@a.com", "x12345678")
        self.client.login(username="admin", password="x12345678")
        self.assertEqual(self.client.get("/panel/mapa/").status_code, 200)
        datos = self.client.get("/panel/mapa/datos/").json()
        self.assertEqual(datos["total"], 4)
        self.assertEqual(len(datos["departamentos"]), 22)
        peten = datos["departamentos"]["peten"]
        self.assertEqual(peten["total"], 3)
        self.assertEqual(peten["productos"][str(self.a.id)], 2)
        self.assertNotIn("dpi", str(datos))  # solo cifras, nunca datos personales

    def test_filtro_por_periodo(self):
        from datetime import timedelta
        from django.utils import timezone
        Registro.objects.filter(departamento="jalapa").update(creado=timezone.now() - timedelta(days=60))
        User.objects.create_superuser("admin", "a@a.com", "x12345678")
        self.client.login(username="admin", password="x12345678")
        self.assertEqual(self.client.get("/panel/mapa/datos/?dias=30").json()["total"], 3)
        self.assertEqual(self.client.get("/panel/mapa/datos/?dias=90").json()["total"], 4)


class NuevosRegistrosTest(RegistroTest):
    def test_correo_opcional(self):
        datos = {k: v for k, v in self.datos.items() if k != "correo"}
        self.assertRedirects(self.client.post(reverse("registro"), datos), reverse("gracias"))
        self.assertEqual(Registro.objects.get().correo, "")
        self.assertEqual(Registro.objects.get().cadena, self.cadena)

    def test_correo_invalido_no_se_guarda(self):
        self.client.post(reverse("registro"), {**self.datos, "correo": "no-es-correo"})
        self.assertFalse(Registro.objects.exists())

    def test_cadena_obligatoria_y_activa(self):
        for cadena in ("", "999999"):
            self.client.post(reverse("registro"), {**self.datos, "cadena": cadena})
        self.cadena.activa = False
        self.cadena.save()
        self.client.post(reverse("registro"), self.datos)
        self.assertFalse(Registro.objects.exists())

    def test_correos_vacios_no_son_duplicados(self):
        self.client.post(reverse("registro"), {**self.datos, "correo": ""})
        self.client.post(reverse("registro"), {**self.datos, "correo": "", "dpi": dpi_valido("23456780")})
        self.assertEqual(Registro.objects.count(), 2)


class AlertasTest(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_superuser("supervisor", "", "clave-prueba")
        self.url = reverse("alertas_chat")
        for nombre, stock in [("Agotado", 0), ("En mínimo", 10), ("Disponible", 11), ("Pendiente", None)]:
            Producto.objects.create(nombre=nombre, descripcion="Prueba", existencias=stock, minimo_alerta=10)

    def test_no_publico(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        empleado = User.objects.create_user("empleado", is_staff=True)
        self.client.force_login(empleado)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_alertas_limite_y_desconocidos(self):
        self.client.force_login(self.usuario)
        data = self.client.get(self.url).json()
        self.assertEqual({p["nombre"] for p in data["productos"]}, {"Agotado", "En mínimo"})
        self.assertEqual(data["pendientes"], 1)
        self.assertEqual(self.client.get(self.url, {"q": "agotados"}).json()["total"], 1)
        self.assertEqual(self.client.get(self.url, {"q": "pendientes"}).json()["total"], 1)
        self.assertEqual(self.client.get(self.url, {"q": "Disponible"}).json()["productos"][0]["estado"], "Disponible")

    def test_actualizacion_stock_se_refleja(self):
        self.client.force_login(self.usuario)
        Producto.objects.filter(nombre="Agotado").update(existencias=40)
        self.assertEqual(self.client.get(self.url).json()["total"], 1)

    def test_panel_y_csv(self):
        from .admin import RegistroAdmin
        from django.contrib import admin
        from django.test import RequestFactory
        self.client.force_login(self.usuario)
        self.assertContains(self.client.get(reverse("admin:index")), "Tu asistente de inventario")
        cadena = Cadena.objects.create(nombre="Cadena ejemplo")
        Registro.objects.create(nombre="Cliente", telefono="5555-1234", cadena=cadena)
        respuesta = RegistroAdmin(Registro, admin.site).exportar_csv(RequestFactory().get("/"), Registro.objects.all())
        self.assertIn("Cadena ejemplo", respuesta.content.decode("utf-8"))

    def test_stock_no_admite_negativos(self):
        from django.core.exceptions import ValidationError
        p = Producto(nombre="Prueba", descripcion="Prueba", existencias=-1)
        with self.assertRaises(ValidationError):
            p.full_clean()


from io import StringIO
from unittest import mock

from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from . import alertas

CONFIG_OK = {"telefonos": ["5555-1234"], "canal": "sms", "twilio_sid": "ACtest", "twilio_token": "secreto",
             "twilio_desde": "+15005550006"}


class EnvioAlertasTest(TestCase):
    def setUp(self):
        cache.clear()
        self.usuario = User.objects.create_superuser("supervisor", "", "clave-prueba")
        self.client.force_login(self.usuario)
        self.url = reverse("alertas_enviar")

    def test_telefonos(self):
        self.assertEqual(alertas.normalizar_telefono("5555-1234"), "+50255551234")
        self.assertEqual(alertas.normalizar_telefono("502 5555 1234"), "+50255551234")
        self.assertEqual(alertas.normalizar_telefono("+15005550006"), "+15005550006")
        with self.assertRaises(alertas.ErrorEnvio):
            alertas.normalizar_telefono("123")

    def test_mensaje_sms_sin_acentos_y_con_agotado(self):
        Producto.objects.create(nombre="Vitamina C", descripcion="x", existencias=0, minimo_alerta=10)
        Producto.objects.create(nombre="Ácido fólico", descripcion="x", existencias=5, minimo_alerta=10)
        Producto.objects.create(nombre="Sobrado", descripcion="x", existencias=50, minimo_alerta=10)
        texto = alertas.construir_mensaje(alertas.productos_en_alerta())
        self.assertIn("Vitamina C: AGOTADO", texto)
        self.assertIn("Acido folico: 5 uds", texto)
        self.assertNotIn("Sobrado", texto)

    def test_solo_post_y_solo_personal(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.client.logout()
        self.assertEqual(self.client.post(self.url).status_code, 302)
        self.client.force_login(User.objects.create_user("empleado", is_staff=True))
        self.assertEqual(self.client.post(self.url).status_code, 403)

    @override_settings(ALERTAS={**CONFIG_OK, "twilio_token": ""})
    def test_sin_configuracion_no_envia(self):
        with mock.patch("tienda.alertas.enviar_mensaje") as envio:
            data = self.client.post(self.url).json()
        envio.assert_not_called()
        self.assertFalse(data["ok"])
        self.assertIn("TWILIO_AUTH_TOKEN", data["mensaje"])

    @override_settings(ALERTAS=CONFIG_OK)
    def test_envia_al_numero_registrado(self):
        Producto.objects.create(nombre="Paracetamol", descripcion="30 pastillas", existencias=30, minimo_alerta=30)
        with mock.patch("tienda.alertas.enviar_mensaje", return_value="SM1") as envio:
            data = self.client.post(self.url).json()
        self.assertTrue(data["ok"])
        self.assertIn("1234", data["mensaje"])
        self.assertNotIn("5555", data["mensaje"])  # el número sale enmascarado
        destino, texto = envio.call_args.args
        self.assertEqual(destino, "5555-1234")
        self.assertIn("Paracetamol: 30 uds (minimo 30)", texto)

    @override_settings(ALERTAS=CONFIG_OK)
    def test_sin_productos_en_alerta_no_envia(self):
        Producto.objects.create(nombre="Sobrado", descripcion="x", existencias=99, minimo_alerta=10)
        with mock.patch("tienda.alertas.enviar_mensaje") as envio:
            data = self.client.post(self.url).json()
        envio.assert_not_called()
        self.assertIn("no se envió", data["mensaje"])

    @override_settings(ALERTAS=CONFIG_OK)
    def test_segundo_clic_inmediato_se_bloquea(self):
        Producto.objects.create(nombre="Paracetamol", descripcion="x", existencias=1, minimo_alerta=10)
        with mock.patch("tienda.alertas.enviar_mensaje", return_value="SM1") as envio:
            self.client.post(self.url)
            data = self.client.post(self.url).json()
        self.assertEqual(envio.call_count, 1)
        self.assertFalse(data["ok"])

    @override_settings(ALERTAS=CONFIG_OK)
    def test_error_del_proveedor_se_informa(self):
        Producto.objects.create(nombre="Paracetamol", descripcion="x", existencias=1, minimo_alerta=10)
        with mock.patch("tienda.alertas.enviar_mensaje", side_effect=alertas.ErrorEnvio("Twilio rechazó el envío (400).")):
            data = self.client.post(self.url).json()
        self.assertFalse(data["ok"])
        self.assertIn("Twilio rechazó", data["mensaje"])

    @override_settings(ALERTAS=CONFIG_OK)
    def test_comando_probar_y_simular(self):
        with mock.patch("tienda.alertas.enviar_mensaje", return_value="SM1") as envio:
            call_command("enviar_alertas", "--probar", stdout=StringIO())
        self.assertIn("prueba", envio.call_args.args[1])
        salida = StringIO()
        with mock.patch("tienda.alertas.enviar_mensaje") as envio:
            call_command("enviar_alertas", "--simular", stdout=salida)
        envio.assert_not_called()
        self.assertIn("5555-1234", salida.getvalue())

    @override_settings(ALERTAS={**CONFIG_OK, "telefonos": []})
    def test_comando_sin_configurar_falla_con_mensaje(self):
        with self.assertRaisesMessage(CommandError, "ALERTAS_TELEFONOS"):
            call_command("enviar_alertas", stdout=StringIO())

    def test_producto_de_prueba_aparece_como_alerta(self):
        call_command("cargar_producto_prueba", stdout=StringIO())
        call_command("cargar_producto_prueba", stdout=StringIO())  # repetirlo no duplica
        p = Producto.objects.get()
        self.assertEqual((p.existencias, p.minimo_alerta), (30, 30))
        self.assertIn("30 pastillas", p.descripcion)
        self.assertEqual(self.client.get(reverse("alertas_chat")).json()["productos"][0]["nombre"], p.nombre)

    def test_panel_muestra_boton_y_estilos(self):
        r = self.client.get(reverse("admin:index"))
        self.assertContains(r, 'id="chat-send"')
        self.assertContains(r, "Bricolage+Grotesque")


from datetime import date, timedelta

from . import recordatorios
from .models import Registro, Tratamiento


class RecordatorioClienteTest(TestCase):
    def setUp(self):
        self.prod = Producto.objects.create(nombre="Paracetamol 500 mg", descripcion="30 pastillas")
        self.cli = Registro.objects.create(nombre="Roberto Pérez", telefono="5555-1234", producto=self.prod)
        self.inicio = date(2026, 10, 1)
        self.t = Tratamiento.objects.create(registro=self.cli, producto=self.prod, tabletas=30, por_dia=1,
                                            avisar_con=5, autorizado=True, fecha_inicio=self.inicio)

    def dia(self, n):
        return self.inicio + timedelta(days=n)

    def test_30_tabletas_una_por_dia_avisa_al_quedar_5(self):
        self.assertEqual(self.t.restantes(self.dia(24)), 6)
        self.assertEqual(self.t.restantes(self.dia(25)), 5)
        self.assertEqual(self.t.fecha_aviso, self.dia(25))
        self.assertFalse(self.t.toca_avisar(self.dia(24)))
        self.assertTrue(self.t.toca_avisar(self.dia(25)))

    def test_dos_por_dia(self):
        self.t.por_dia = 2
        self.assertEqual(self.t.fecha_aviso, self.dia(13))  # 30-26=4 <= 5 tras 13 días
        self.assertEqual(self.t.restantes(self.dia(13)), 4)

    def test_sin_autorizacion_no_envia(self):
        self.t.autorizado = False
        self.t.save()
        self.assertEqual(recordatorios.pendientes(self.dia(26)), [])

    def test_si_ya_termino_hace_mucho_no_envia(self):
        self.assertEqual(len(recordatorios.pendientes(self.dia(33))), 1)
        self.assertEqual(recordatorios.pendientes(self.dia(40)), [])

    @override_settings(ALERTAS=CONFIG_OK)
    def test_envia_una_sola_vez_al_cliente(self):
        with mock.patch("tienda.alertas.enviar_mensaje", return_value="SM1") as envio:
            self.assertEqual(recordatorios.procesar(self.dia(24)), ([], []))
            enviados, errores = recordatorios.procesar(self.dia(25))
            recordatorios.procesar(self.dia(26))  # no repite
        self.assertEqual(envio.call_count, 1)
        destino, texto = envio.call_args.args
        self.assertEqual(destino, "5555-1234")
        self.assertIn("Hola Roberto", texto)
        self.assertIn("te quedan 5 tabletas de Paracetamol 500 mg", texto)
        self.assertTrue(len(enviados) == 1 and not errores)
        self.t.refresh_from_db()
        self.assertIsNotNone(self.t.aviso_enviado_en)

    @override_settings(ALERTAS=CONFIG_OK)
    def test_si_falla_se_reintenta(self):
        with mock.patch("tienda.alertas.enviar_mensaje", side_effect=alertas.ErrorEnvio("sin red")):
            enviados, errores = recordatorios.procesar(self.dia(25))
        self.assertTrue(errores and not enviados)
        self.t.refresh_from_db()
        self.assertIsNone(self.t.aviso_enviado_en)
        with mock.patch("tienda.alertas.enviar_mensaje", return_value="SM2") as envio:
            recordatorios.procesar(self.dia(25))
        self.assertEqual(envio.call_count, 1)

    @override_settings(ALERTAS={**CONFIG_OK, "telefonos": []})
    def test_clientes_no_necesitan_telefonos_del_personal(self):
        self.assertEqual(alertas.credenciales_faltantes(), [])

    @override_settings(ALERTAS=CONFIG_OK)
    def test_comando_y_cliente_de_prueba(self):
        Tratamiento.objects.all().delete()
        call_command("cargar_producto_prueba", "--telefono", "5555-9999", stdout=StringIO())
        t = Tratamiento.objects.get()
        self.assertEqual(t.restantes(), 5)
        salida = StringIO()
        with mock.patch("tienda.alertas.enviar_mensaje", return_value="SM1") as envio:
            call_command("enviar_recordatorios", "--simular", stdout=salida)
            envio.assert_not_called()
            self.assertIn("1 aviso(s) pendiente(s)", salida.getvalue())
            call_command("enviar_recordatorios", stdout=StringIO())
        self.assertEqual(envio.call_args.args[0], "5555-9999")

    def test_admin_carga_y_valida(self):
        admin_user = User.objects.create_superuser("jefe", "", "clave-prueba")
        self.client.force_login(admin_user)
        for nombre in ("admin:tienda_tratamiento_changelist", "admin:tienda_tratamiento_add"):
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 200)
        self.assertContains(self.client.get(reverse("admin:tienda_tratamiento_changelist")), "Tabletas restantes hoy")
        self.assertContains(self.client.get(reverse("admin:tienda_registro_change", args=[self.cli.pk])), "Tratamiento")
        r = self.client.post(reverse("admin:tienda_tratamiento_add"), {
            "registro": self.cli.pk, "producto": self.prod.pk, "tabletas": 30, "por_dia": 1,
            "fecha_inicio": "2026-10-01", "avisar_con": 30})
        self.assertContains(r, "Debe ser menor")
