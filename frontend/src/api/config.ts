const defaultApiBaseUrl = `${window.location.protocol}//${window.location.hostname}:8000/api/v1`;

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? defaultApiBaseUrl;

export const API_ENDPOINTS = {
  auth: {
    csrf: `${API_BASE_URL}/auth/csrf/`,
    changePassword: `${API_BASE_URL}/auth/change-password/`,
    login: `${API_BASE_URL}/auth/login/`,
    loginVerifyCode: `${API_BASE_URL}/auth/login/verify-code/`,
    me: `${API_BASE_URL}/auth/me/`,
    verifyEmailChange: `${API_BASE_URL}/auth/me/verify-email-change/`,
    resendEmailChange: `${API_BASE_URL}/auth/me/email-change/resend/`,
    cancelEmailChange: `${API_BASE_URL}/auth/me/email-change/cancel/`,
    logout: `${API_BASE_URL}/auth/logout/`,
    refresh: `${API_BASE_URL}/auth/refresh/`,
    register: `${API_BASE_URL}/auth/register/`,
    status: `${API_BASE_URL}/auth/status/`,
    verifyEmail: `${API_BASE_URL}/auth/verify-email/`,
    resendVerification: `${API_BASE_URL}/auth/resend-verification/`,
    forgotPassword: `${API_BASE_URL}/auth/forgot-password/`,
    resetPassword: `${API_BASE_URL}/auth/reset-password/`,
  },
  profile: {
    detail: `${API_BASE_URL}/user/profile/`,
  },
};
