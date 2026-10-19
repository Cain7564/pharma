from django.http import HttpResponse


class HealthCheckMiddleware:
    """Responde 200 en /healthz antes que cualquier otra capa (redirección HTTPS, hosts permitidos).
    Lo usa Render para saber que el sitio está vivo."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/healthz":
            return HttpResponse("ok", content_type="text/plain")
        return self.get_response(request)
