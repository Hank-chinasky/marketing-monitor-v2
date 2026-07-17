from django.core.exceptions import PermissionDenied
from django.urls import Resolver404, resolve

from core.services.demo_access import (
    ALLOWED_DEMO_SAFE_URL_NAMES,
    ALLOWED_DEMO_UNSAFE_URL_NAMES,
    SAFE_DEMO_HTTP_METHODS,
    is_demo_viewer,
)


class DemoReadOnlyMiddleware:
    """
    Confine demo viewers to an explicit read-only demo surface.

    The UI hiding is presentational. This middleware is the server-side
    boundary that blocks both mutations and operational GET routes.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.is_demo_viewer = is_demo_viewer(request.user)

        if not request.is_demo_viewer:
            return self.get_response(request)

        try:
            url_name = resolve(request.path_info).url_name
        except Resolver404:
            url_name = None

        method = request.method.upper()

        if method in SAFE_DEMO_HTTP_METHODS:
            if url_name not in ALLOWED_DEMO_SAFE_URL_NAMES:
                raise PermissionDenied(
                    "This route is outside the read-only demo surface."
                )
        elif url_name not in ALLOWED_DEMO_UNSAFE_URL_NAMES:
            raise PermissionDenied(
                "Demo viewer access is read-only."
            )

        return self.get_response(request)
