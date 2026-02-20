import { API_ENDPOINTS } from "./config";
import { apiRequest, clearCachedCsrfToken } from "./http";

export type AuthStatusResponse = {
  authenticated: boolean;
  email?: string;
  is_email_verified?: boolean;
  is_locked?: boolean;
};

export type LoginResponse = {
  detail: string;
  email?: string;
  requires_login_code?: boolean;
};

export type RegisterResponse = {
  detail: string;
  email: string;
};

export type VerifyEmailResponse = {
  detail: string;
  email: string;
};

export async function getAuthStatus(): Promise<AuthStatusResponse> {
  return apiRequest<AuthStatusResponse>(API_ENDPOINTS.auth.status, "GET");
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  return apiRequest<LoginResponse>(API_ENDPOINTS.auth.login, "POST", {
    email,
    password,
  });
}

export async function verifyLoginCode(email: string, code: string, rememberDevice: boolean): Promise<LoginResponse> {
  return apiRequest<LoginResponse>(API_ENDPOINTS.auth.loginVerifyCode, "POST", {
    email,
    code,
    remember_device: rememberDevice,
  });
}

export async function logout(): Promise<void> {
  await apiRequest<{ detail: string }>(API_ENDPOINTS.auth.logout, "POST");
  clearCachedCsrfToken();
}

export async function refreshSession(): Promise<void> {
  await apiRequest<{ detail: string }>(API_ENDPOINTS.auth.refresh, "POST");
}

export async function register(fullName: string, email: string, password: string, acceptTerms: boolean): Promise<RegisterResponse> {
  return apiRequest<RegisterResponse>(API_ENDPOINTS.auth.register, "POST", {
    full_name: fullName,
    email,
    password,
    accept_terms: acceptTerms,
  });
}

export async function verifyEmail(email: string, code: string): Promise<VerifyEmailResponse> {
  return apiRequest<VerifyEmailResponse>(API_ENDPOINTS.auth.verifyEmail, "POST", {
    email,
    code,
  });
}

export async function resendVerification(email: string): Promise<{ detail: string }> {
  return apiRequest<{ detail: string }>(API_ENDPOINTS.auth.resendVerification, "POST", {
    email,
  });
}

export async function forgotPassword(email: string): Promise<{ detail: string }> {
  return apiRequest<{ detail: string }>(API_ENDPOINTS.auth.forgotPassword, "POST", {
    email,
  });
}

export async function resetPassword(token: string, newPassword: string): Promise<{ detail: string }> {
  return apiRequest<{ detail: string }>(API_ENDPOINTS.auth.resetPassword, "POST", {
    token,
    new_password: newPassword,
  });
}
