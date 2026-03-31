from django.conf import settings


def set_auth_cookies(response, access_token, refresh_token):
    secure = getattr(settings, "COOKIE_SECURE", False)
    samesite = settings.SIMPLE_JWT.get("AUTH_COOKIE_SAMESITE", "Lax")
    cookie_path = settings.SIMPLE_JWT.get("AUTH_COOKIE_PATH", "/")

    access_lifetime = settings.SIMPLE_JWT.get("ACCESS_TOKEN_LIFETIME")
    refresh_lifetime = settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME")

    access_max_age = int(access_lifetime.total_seconds()
                         ) if access_lifetime else None
    refresh_max_age = int(refresh_lifetime.total_seconds()
                          ) if refresh_lifetime else None

    response.set_cookie(
        key=settings.SIMPLE_JWT["AUTH_COOKIE"],
        value=str(access_token),
        httponly=True,
        secure=secure,
        samesite=samesite,
        path=cookie_path,
        max_age=access_max_age,
    )
    response.set_cookie(
        key=settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"],
        value=str(refresh_token),
        httponly=True,
        secure=secure,
        samesite=samesite,
        path=cookie_path,
        max_age=refresh_max_age,
    )
    return response


def set_trusted_device_cookie(response, raw_token):
    secure = getattr(settings, "COOKIE_SECURE", False)
    samesite = settings.SIMPLE_JWT.get("AUTH_COOKIE_SAMESITE", "Lax")
    cookie_path = settings.SIMPLE_JWT.get("AUTH_COOKIE_PATH", "/")
    max_age = int(
        getattr(settings, "AUTH_TRUSTED_DEVICE_DAYS", 30) * 24 * 60 * 60)
    cookie_name = getattr(
        settings, "AUTH_TRUSTED_DEVICE_COOKIE", "trusted_device")

    response.set_cookie(
        key=cookie_name,
        value=raw_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path=cookie_path,
        max_age=max_age,
    )
    return response


def clear_auth_cookies(response):
    cookie_path = settings.SIMPLE_JWT.get("AUTH_COOKIE_PATH", "/")
    response.delete_cookie(
        settings.SIMPLE_JWT["AUTH_COOKIE"], path=cookie_path)
    response.delete_cookie(
        settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"], path=cookie_path)
    return response
