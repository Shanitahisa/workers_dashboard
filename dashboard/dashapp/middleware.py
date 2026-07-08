from django.conf import settings
from django.utils.cache import patch_cache_control


class NoCacheAuthenticatedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        is_authenticated = getattr(request, 'user', None) and request.user.is_authenticated
        is_login_page = request.path == settings.LOGIN_URL

        if is_authenticated or is_login_page:
            patch_cache_control(response, no_cache=True, no_store=True, must_revalidate=True, private=True, max_age=0)
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response
