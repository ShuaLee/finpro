import { API_ENDPOINTS } from "./config";
import { apiRequest } from "./http";

export type MeResponse = {
  user: {
    id: number;
    email: string;
    is_active: boolean;
    is_email_verified: boolean;
    is_locked: boolean;
    date_joined: string;
  };
  profile: {
    full_name: string;
    language: string;
    timezone: string;
    country: string;
    currency: string;
    created_at: string;
    updated_at: string;
  };
};

export type ProfileResponse = {
  user: {
    id: number;
    email: string;
    is_active: boolean;
    is_staff: boolean;
    email_verified_at: string | null;
    is_email_verified: boolean;
    is_locked: boolean;
    date_joined: string;
  };
  full_name: string;
  language: string;
  timezone: string;
  country: string;
  currency: string;
  created_at: string;
  updated_at: string;
};

export async function getMe(): Promise<MeResponse> {
  return apiRequest<MeResponse>(API_ENDPOINTS.auth.me, "GET");
}

export async function updateEmail(newEmail: string, currentPassword: string): Promise<{ detail: string; target_email: string }> {
  return apiRequest<{ detail: string; target_email: string }>(API_ENDPOINTS.auth.requestEmailChange, "POST", {
    new_email: newEmail,
    current_password: currentPassword,
  });
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<{ detail: string }> {
  return apiRequest<{ detail: string }>(API_ENDPOINTS.auth.changePassword, "POST", {
    current_password: currentPassword,
    new_password: newPassword,
  });
}

export async function deleteAccount(currentPassword: string, confirmation: string): Promise<{ detail: string; email: string }> {
  return apiRequest<{ detail: string; email: string }>(API_ENDPOINTS.auth.deleteAccount, "POST", {
    current_password: currentPassword,
    confirmation,
  });
}

export async function verifyPendingEmailChange(newEmail: string, code: string): Promise<{ detail: string; email: string }> {
  return apiRequest<{ detail: string; email: string }>(API_ENDPOINTS.auth.verifyEmailChange, "POST", {
    new_email: newEmail,
    code,
  });
}

export async function getProfile(): Promise<ProfileResponse> {
  return apiRequest<ProfileResponse>(API_ENDPOINTS.profile.detail, "GET");
}

export async function updateProfile(payload: Partial<ProfileResponse>): Promise<ProfileResponse> {
  return apiRequest<ProfileResponse>(API_ENDPOINTS.profile.detail, "PATCH", payload as Record<string, unknown>);
}
