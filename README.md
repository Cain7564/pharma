# Avisos a clientes cuando les quedan pocas tabletas

Ejemplo: empaque de 30 tabletas, 1 por día → el cliente recibe un SMS/WhatsApp cuando le quedan 5.

1. En el panel: **Registros de clientes → (cliente) → Tratamiento**, o **Tratamientos de clientes → Añadir**. Indica medicamento, tabletas del empaque (30), tabletas por día (1), fecha de inicio y «avisar cuando queden» (5).
2. Marca **«el cliente aceptó recibir este aviso por mensaje»**. Sin esa marca no se envía nada. Conviene mencionar estos avisos en el aviso de privacidad.
3. Se cuenta una dosis por cada día transcurrido desde la fecha de inicio; el aviso se envía una sola vez.
4. El envío necesita Twilio configurado (ver sección anterior; aquí `ALERTAS_TELEFONOS` no hace falta, ese es solo para el personal).
5. **Revisión automática:** deja corriendo `recordatorios.bat` (revisa cada hora) en una segunda ventana junto al servidor, o programa `python manage.py enviar_recordatorios` una vez al día. También puedes usar la acción «Enviar ahora los avisos que ya correspondan» en la lista de Tratamientos.
6. Probar: `python manage.py cargar_producto_prueba --telefono 5555-1234` crea un cliente de prueba al que ya le quedan 5 tabletas; luego `python manage.py enviar_recordatorios --simular` (solo muestra) o sin `--simular` (envía).

---

# Novedades: panel con los colores del sitio y alertas por mensaje

- El panel usa la paleta del sitio público (azul marino, azul, lima y verde, franjas en el encabezado, botones redondeados, mismas fuentes). Está en `tienda/static/tienda/admin.css`.
- **Producto de prueba de 30 pastillas:** `python manage.py cargar_producto_prueba` crea «Paracetamol 500 mg (prueba)» con 30 unidades y mínimo de alerta 30, así aparece de inmediato como «Por agotarse». Repetir el comando lo restablece. Opciones: `--existencias N --minimo N`. Bórralo o desmarca «visible en el catálogo» al terminar.
- **Enviar la alerta a tu teléfono (SMS o WhatsApp con Twilio):** añade a `.env` (ver `.env.example`):
  `ALERTAS_TELEFONOS`, `ALERTAS_CANAL` (`sms` o `whatsapp`), `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_DESDE`.
  Con una cuenta de prueba de Twilio solo se puede enviar a números verificados en Twilio.
  1. Comprobar el número: `python manage.py enviar_alertas --probar`
  2. Ver qué se enviaría sin enviar: `python manage.py enviar_alertas --simular`
  3. Enviar la alerta real: botón verde del asistente en el panel, o `python manage.py enviar_alertas`.
  Para envíos automáticos, programa ese comando (Programador de tareas de Windows o cron).

---

# Actualización: administrador, cadenas y alertas

## Aplicar esta versión

1. Instala dependencias: `python -m pip install -r requirements.txt`.
2. Si ya tienes datos, respalda tu base de datos antes de actualizar.
3. Ejecuta `python manage.py migrate` para aplicar la migración 0003.
4. Ejecuta `python manage.py test` y `python manage.py check`.
5. En producción ejecuta `python manage.py collectstatic --noinput`.
6. Inicia con `python manage.py runserver` (desarrollo) y entra a `/panel/`.

## Configuración necesaria

- En **Cadenas de farmacias**, crea las cadenas reales y déjalas activas. El formulario público exige seleccionar una. No se inventaron cadenas ni se asignaron a registros históricos.
- En **Productos**, registra las existencias y el mínimo de alerta. Puedes editarlos directamente en la lista y pulsar Guardar.
- El inventario es global por producto, no por cadena. El mínimo inicial es 10; ajústalo según cada medicamento.
- Los productos anteriores quedan con inventario desconocido, no con cero unidades. Aparecen en “Sin inventario”.
- Los registros anteriores conservan sus datos y quedan sin cadena hasta que un administrador la asigne. Desactiva una cadena para retirarla del formulario; las cadenas usadas están protegidas contra eliminación.
- El correo es opcional, tanto Gmail como cualquier otro proveedor. Si se proporciona, se valida y se mantiene la comprobación de duplicados.

## Chatbot de alertas

Está disponible dentro del panel para personal con permiso de ver productos. Al abrirlo consulta el inventario actual. Incluye botones **Por agotarse**, **Agotados** y **Sin inventario**, y búsqueda por nombre de medicamento.

Genera una alerta cuando las existencias son menores o iguales al mínimo. Cero se muestra como agotado. También contempla productos no visibles en el catálogo. Las consultas posteriores vuelven a leer la base de datos.

Es un asistente basado en reglas y datos reales registrados, sin servicio de IA externo ni claves API. No interpreta conversaciones generales. Por sí solo no envía mensajes: solo lo hace al pulsar **Enviar alerta al teléfono** (o con `python manage.py enviar_alertas`) y únicamente si configuraste Twilio (ver abajo). No hay notificaciones en segundo plano. No estima fechas de agotamiento ni modifica inventario automáticamente: el personal debe actualizar las existencias. Registrarse en una promoción no descuenta unidades.

## Validación de esta entrega

Se agregaron pruebas de correo opcional, cadenas, permisos, umbral de alertas, inventario desconocido, actualización de stock y exportación CSV. Se comprobó la sintaxis Python y JavaScript. No fue posible ejecutar Django en el entorno de edición porque no estaba instalado y la instalación de dependencias no estuvo disponible; ejecutar los comandos de prueba indicados arriba antes de publicar.

---

# Pharma Del · Promoción 1x1 (Django)

Sitio con catálogo, formulario de registro de clientes y panel privado.
No tiene carrito ni pagos en línea.

## Iniciar el proyecto (lo más fácil)

Necesitas Python 3.12 o más reciente (python.org; en Windows marca **"Add Python to PATH"**).

- **Windows:** haz doble clic en `iniciar.bat`.
- **Mac / Linux:** abre una terminal en esta carpeta y ejecuta `bash iniciar.sh`.

La primera vez, el script crea el entorno, instala lo necesario, prepara la base de datos,
te pide crear tu usuario del panel (la contraseña no se ve al escribirla) y carga productos
de ejemplo. Las siguientes veces solo enciende el sitio.

- Sitio: http://127.0.0.1:8000
- Panel privado: http://127.0.0.1:8000/panel/
- Para apagarlo: `Ctrl + C` en la ventana negra.

## Cómo comprobar que funciona
1. Entra al panel, agrega un producto con foto y mira que aparezca en `/productos/`.
2. Llena el formulario de `/registro/` y comprueba que el registro aparece en el panel
   ("Registros de clientes"), donde también puedes exportarlo a CSV.
3. Pruebas automáticas (con el entorno activado): `python manage.py test`.

## Registro con DPI y departamento
El formulario pide **DPI** (13 dígitos, con validación del dígito verificador; se puede escribir
con espacios) y el **departamento** desde donde se hace el registro. El DPI sirve para evitar
registros duplicados del mismo producto.
- En los listados del panel y en la exportación a CSV el DPI aparece oculto (`*********1234`);
  solo se ve completo al abrir un registro.
- El DPI es un dato muy sensible: pide solo lo necesario, limita quién tiene acceso al panel,
  usa HTTPS y contraseñas fuertes, y protege las copias de seguridad.

## Mapa de productos por departamento
Es una página privada dentro del panel: entra a http://127.0.0.1:8000/panel/ y usa el enlace
"Abrir el mapa" (o ve directo a `/panel/mapa/`). Solo la ven usuarios del panel con permiso para
ver registros.
- Muestra el **producto líder** de cada departamento (color) y cuántos registros hay (intensidad).
- Elige un producto en el filtro para ver **en qué departamentos se mueve más**.
- Filtra por periodo (todo, 90 o 30 días). Abajo hay una tabla con el resumen por departamento.
- Se basa en **registros de interés**, no en ventas.
- Para verlo funcionando sin datos reales: `python manage.py cargar_demo` crea registros
  ficticios (solo en tu computadora) y `python manage.py borrar_demo` los elimina.

## Dónde cambiar cada cosa
| Qué | Dónde |
|---|---|
| Teléfono, correo, horario, responsable de datos | `config/settings.py`, bloque `EMPRESA` (al final) |
| Textos de las páginas | `tienda/templates/tienda/*.html` |
| Colores y diseño | `tienda/static/tienda/css/styles.css` (variables al inicio) |
| Productos y fotos | Panel privado → Productos |
| Validación del formulario y del DPI | `tienda/forms.py`, `tienda/validadores.py` |
| Mapa (diseño y lógica) | `tienda/static/tienda/js/mapa.js`, `tienda/static/tienda/css/mapa.css`, `tienda/views.py` |
| Tablas de la base de datos | `tienda/models.py` (si las cambias: `makemigrations` y `migrate`) |

## Aviso de privacidad
`privacidad.html` es una base general. Antes de publicar, revísalo con la empresa y con un
abogado, y cumple lo que prometa. Para borrar registros viejos (por ejemplo a los 12 meses):
`python manage.py limpiar_registros --dias 365` (solo muestra cuántos borraría) y
`python manage.py limpiar_registros --dias 365 --borrar` (los elimina).

## Publicar en Render (paso a paso)
El proyecto ya incluye `render.yaml`, `build.sh` y `.python-version`.

1. Sube **el contenido de esta carpeta** (donde está `manage.py`) a un repositorio de GitHub.
2. En Render: **New + → Blueprint**, elige el repositorio y pulsa **Apply**. Crea el sitio web
   y la base de datos PostgreSQL con todas las variables necesarias.
3. Espera a que termine el despliegue (la primera vez tarda unos minutos). Tu sitio queda en
   `https://pharma-del.onrender.com` (o el nombre que Render asigne).
4. **Panel privado:** `https://TU-SITIO.onrender.com/panel/`. Usuario `admin`; la contraseña
   está en Render → tu servicio → **Environment** → `DJANGO_SUPERUSER_PASSWORD`.
5. Cuando tengas tus productos reales, cambia `CARGAR_EJEMPLOS` a `0`.

Notas del plan gratuito: el sitio se «duerme» tras 15 minutos sin visitas (la primera carga
tarda ~1 minuto), la base de datos gratuita de Render caduca a los 30 días (pasa a un plan de
pago para conservar los datos) y **las fotos subidas se borran al reiniciar** porque no hay
disco persistente: usa un plan de pago con disco (`DJANGO_MEDIA_ROOT=/data/media`) o
almacenamiento externo.

## Publicar en internet
El proyecto ya trae la configuración de producción lista; solo hay que darle los valores.

1. **Hosting con Python** (PythonAnywhere, Render, Railway o un servidor propio) y un
   **dominio con HTTPS**.
2. **Variables de entorno** en el hosting (el modelo está en `.env.example`):
   - `DJANGO_SECRET_KEY`: clave larga y secreta. Al definirla, el sitio arranca en modo producción.
   - `DJANGO_ALLOWED_HOSTS=pharmadel.com,www.pharmadel.com`
   - `DJANGO_CSRF_TRUSTED_ORIGINS=https://pharmadel.com,https://www.pharmadel.com`
3. **Instalar:** `pip install -r requirements-prod.txt`
4. **Preparar:** `python manage.py collectstatic --noinput` y `python manage.py migrate`
5. **Arrancar:** `gunicorn config.wsgi` (el `Procfile` ya lo indica).
6. **Crear el usuario del panel** en el servidor: `python manage.py createsuperuser`.
7. **Base de datos:** SQLite sirve al inicio (usa `DJANGO_DB_PATH` apuntando a un disco
   persistente). Con más uso, PostgreSQL con `DATABASE_URL`.
8. **Fotos de productos:** necesitan un disco persistente (`DJANGO_MEDIA_ROOT` y
   `DJANGO_SERVE_MEDIA=1`, válido para poco tráfico) o almacenamiento externo.
9. **Verificar:** `python manage.py check --deploy`.
10. **Después de publicar:** sube `DJANGO_HSTS_SECONDS` a `31536000`, cambia la dirección del
    panel con `DJANGO_ADMIN_URL`, haz copias de seguridad periódicas de la base de datos y
    de las fotos, y valora un CAPTCHA y bloqueo de intentos de acceso al panel
    (por ejemplo django-axes). El formulario ya tiene un campo trampa contra bots básicos.
