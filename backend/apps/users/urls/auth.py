from django.urls import path

from apps.users.views import (
    CsrfTokenView,
    ChangePasswordView,
    DeleteAccountView,
    EmailChangeConfirmView,
    EmailChangeRequestView,
    LoginView,
    LogoutView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RefreshSessionView,
    RegisterView,
    ResendVerificationView,
    VerifyEmailView,
)


urlpatterns = [
    path("auth/csrf/", CsrfTokenView.as_view(), name="auth-csrf"),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", RefreshSessionView.as_view(), name="auth-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/delete-account/", DeleteAccountView.as_view(), name="auth-delete-account"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("auth/email/verify/", VerifyEmailView.as_view(), name="auth-email-verify"),
    path("auth/email/resend/", ResendVerificationView.as_view(), name="auth-email-resend"),
    path(
        "auth/password/reset/request/",
        PasswordResetRequestView.as_view(),
        name="auth-password-reset-request",
    ),
    path(
        "auth/password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="auth-password-reset-confirm",
    ),
    path(
        "auth/password/change/",
        ChangePasswordView.as_view(),
        name="auth-password-change",
    ),
    path(
        "auth/email/change/request/",
        EmailChangeRequestView.as_view(),
        name="auth-email-change-request",
    ),
    path(
        "auth/email/change/confirm/",
        EmailChangeConfirmView.as_view(),
        name="auth-email-change-confirm",
    ),
]
