const defaultApiBaseUrl = `${window.location.protocol}//${window.location.hostname}:8000/api/v1`;

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? defaultApiBaseUrl;

export const API_ENDPOINTS = {
  auth: {
    csrf: `${API_BASE_URL}/auth/csrf/`,
    login: `${API_BASE_URL}/auth/login/`,
    loginVerifyCode: `${API_BASE_URL}/auth/login/verify-code/`,
    logout: `${API_BASE_URL}/auth/logout/`,
    refresh: `${API_BASE_URL}/auth/refresh/`,
    register: `${API_BASE_URL}/auth/register/`,
    status: `${API_BASE_URL}/auth/status/`,
    verifyEmail: `${API_BASE_URL}/auth/verify-email/`,
    resendVerification: `${API_BASE_URL}/auth/resend-verification/`,
  },
};
