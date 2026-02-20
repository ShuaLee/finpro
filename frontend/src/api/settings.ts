import { API_ENDPOINTS } from "./config";
import { apiRequest } from "./http";

export type MeResponse = {
  id: number;
  email: string;
  pending_email_change?: string | null;
  is_email_verified: boolean;
  is_active: boolean;
  is_locked: boolean;
  date_joined: string;
};

export type ProfileResponse = {
  id: number;
  email: string;
  full_name: string | null;
  birth_date: string | null;
  language: string;
  timezone: string;
  country: string | null;
  currency: string;
  plan: string | null;
  receive_email_updates: boolean;
  receive_marketing_emails: boolean;
  onboarding_status: string;
  onboarding_step: number;
  created_at: string;
  updated_at: string;
};

export async function getMe(): Promise<MeResponse> {
  return apiRequest<MeResponse>(API_ENDPOINTS.auth.me, "GET");
}

export async function updateEmail(email: string, currentPassword: string): Promise<MeResponse & { detail: string }> {
  return apiRequest<MeResponse & { detail: string }>(API_ENDPOINTS.auth.me, "PATCH", {
    email,
    current_password: currentPassword,
  });
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<{ detail: string }> {
  return apiRequest<{ detail: string }>(API_ENDPOINTS.auth.changePassword, "POST", {
    current_password: currentPassword,
    new_password: newPassword,
  });
}

export async function verifyPendingEmailChange(email: string, code: string): Promise<MeResponse & { detail: string }> {
  return apiRequest<MeResponse & { detail: string }>(API_ENDPOINTS.auth.verifyEmailChange, "POST", {
    email,
    code,
  });
}

export async function resendPendingEmailChangeCode(): Promise<MeResponse & { detail: string }> {
  return apiRequest<MeResponse & { detail: string }>(API_ENDPOINTS.auth.resendEmailChange, "POST");
}

export async function cancelPendingEmailChange(): Promise<MeResponse & { detail: string }> {
  return apiRequest<MeResponse & { detail: string }>(API_ENDPOINTS.auth.cancelEmailChange, "POST");
}

export async function getProfile(): Promise<ProfileResponse> {
  return apiRequest<ProfileResponse>(API_ENDPOINTS.profile.detail, "GET");
}

export async function updateProfile(payload: Partial<ProfileResponse>): Promise<ProfileResponse> {
  return apiRequest<ProfileResponse>(API_ENDPOINTS.profile.detail, "PATCH", payload as Record<string, unknown>);
}
