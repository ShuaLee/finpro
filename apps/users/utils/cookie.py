from django.conf import settings


def set_auth_cookies(response, access_token, refresh_token):
    response.set_cookie(
        key="access",
        value=str(access_token),
        httponly=True,
        secure=False,  # OK in dev
        samesite="Lax",  # ✅ Use Lax for localhost
        max_age=60 * 5,
    )
    response.set_cookie(
        key="refresh",
        value=str(refresh_token),
        httponly=True,
        secure=False,  # OK in dev
        samesite="Lax",  # ✅ Use Lax for localhost
        max_age=60 * 10,  # ✅ 10 minutes
    )
    return response
