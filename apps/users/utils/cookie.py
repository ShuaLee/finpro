from django.conf import settings


def set_auth_cookies(response, access_token, refresh_token):
    access_lifetime = int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())
    refresh_lifetime = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())

    response.set_cookie(
        key="access",
        value=str(access_token),
        httponly=True,
        secure=False,  # OK in dev, use True in prod
        samesite=settings.SIMPLE_JWT.get("AUTH_COOKIE_SAMESITE", "Lax"),
        max_age=access_lifetime,
    )
    response.set_cookie(
        key="refresh",
        value=str(refresh_token),
        httponly=True,
        secure=False,
        samesite=settings.SIMPLE_JWT.get("AUTH_COOKIE_SAMESITE", "Lax"),
        max_age=refresh_lifetime,
    )
    return response