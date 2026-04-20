import { API_ENDPOINTS } from "./config";
import { apiRequest, clearCachedCsrfToken } from "./http";

export type AuthStatusResponse = {
  authenticated: boolean;
  email?: string;
  full_name?: string;
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

export type RegisterPayload = {
  fullName: string;
  email: string;
  password: string;
  acceptTerms: boolean;
  language?: string;
  timezone?: string;
  country?: string | null;
  currency?: string;
};

export type VerifyEmailResponse = {
  detail: string;
  email: string;
};

export async function getAuthStatus(): Promise<AuthStatusResponse> {
  const response = await apiRequest<{
    user: {
      email: string;
      is_email_verified: boolean;
      is_locked: boolean;
    };
    profile?: {
      full_name?: string;
    };
  }>(API_ENDPOINTS.auth.me, "GET");

  return {
    authenticated: true,
    email: response.user.email,
    full_name: response.profile?.full_name,
    is_email_verified: response.user.is_email_verified,
    is_locked: response.user.is_locked,
  };
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  return apiRequest<LoginResponse>(API_ENDPOINTS.auth.login, "POST", {
    email,
    password,
  });
}

export async function logout(): Promise<void> {
  await apiRequest<{ detail: string }>(API_ENDPOINTS.auth.logout, "POST");
  clearCachedCsrfToken();
}

export async function logoutAllSessions(): Promise<{ detail: string; revoked_refresh_tokens: number }> {
  const response = await apiRequest<{ detail: string; revoked_refresh_tokens: number }>(API_ENDPOINTS.auth.logoutAll, "POST");
  clearCachedCsrfToken();
  return response;
}

export async function refreshSession(): Promise<void> {
  await apiRequest<{ detail: string }>(API_ENDPOINTS.auth.refresh, "POST");
}

export async function register(payload: RegisterPayload): Promise<RegisterResponse> {
  return apiRequest<RegisterResponse>(API_ENDPOINTS.auth.register, "POST", {
    full_name: payload.fullName,
    email: payload.email,
    password: payload.password,
    accept_terms: payload.acceptTerms,
    language: payload.language ?? "en",
    timezone: payload.timezone ?? "UTC",
    country: payload.country ?? "",
    currency: payload.currency ?? "USD",
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
