from django.conf import settings


def set_auth_cookies(response, access_token, refresh_token):
    secure = getattr(settings, "COOKIE_SECURE", False)
    samesite = settings.SIMPLE_JWT.get("AUTH_COOKIE_SAMESITE", "Lax")

    response.set_cookie(
        key=settings.SIMPLE_JWT["AUTH_COOKIE"],
        value=str(access_token),
        httponly=True,
        secure=secure,
        samesite=samesite,
        path=settings.SIMPLE_JWT.get("AUTH_COOKIE_PATH", "/"),
    )
    response.set_cookie(
        key=settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"],
        value=str(refresh_token),
        httponly=True,
        secure=secure,
        samesite=samesite,
        path=settings.SIMPLE_JWT.get("AUTH_COOKIE_PATH", "/"),
    )
    return response


def clear_auth_cookies(response):
    response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE"], path="/")
    response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"], path="/")
    return response
