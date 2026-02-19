from django.urls import path
from users.views.auth import (
    AuthStatusView,
    CSRFTokenView,
    ChangePasswordView,
    ForgotPasswordView,
    RegisterView,
    RefreshSessionView,
    VerifyEmailView,
    VerifyLoginCodeView,
    ResendVerificationView,
    ResetPasswordView,
    LoginView,
    LogoutView,
    MeView,
)

urlpatterns = [
    path("csrf/", CSRFTokenView.as_view(), name="auth-csrf"),
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("verify-email/", VerifyEmailView.as_view(), name="auth-verify-email"),
    path("resend-verification/", ResendVerificationView.as_view(), name="auth-resend-verification"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="auth-forgot-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="auth-reset-password"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("login/verify-code/", VerifyLoginCodeView.as_view(), name="auth-login-verify-code"),
    path("refresh/", RefreshSessionView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("status/", AuthStatusView.as_view(), name="auth-status"),
]
