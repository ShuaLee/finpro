const defaultApiBaseUrl = `${window.location.protocol}//${window.location.hostname}:8000/api/v1`;

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? defaultApiBaseUrl;

export const API_ENDPOINTS = {
  auth: {
    csrf: `${API_BASE_URL}/auth/csrf/`,
    changePassword: `${API_BASE_URL}/auth/password/change/`,
    login: `${API_BASE_URL}/auth/login/`,
    me: `${API_BASE_URL}/auth/me/`,
    verifyEmailChange: `${API_BASE_URL}/auth/email/change/confirm/`,
    requestEmailChange: `${API_BASE_URL}/auth/email/change/request/`,
    logout: `${API_BASE_URL}/auth/logout/`,
    logoutAll: `${API_BASE_URL}/auth/logout-all/`,
    deleteAccount: `${API_BASE_URL}/auth/delete-account/`,
    refresh: `${API_BASE_URL}/auth/refresh/`,
    register: `${API_BASE_URL}/auth/register/`,
    verifyEmail: `${API_BASE_URL}/auth/email/verify/`,
    resendVerification: `${API_BASE_URL}/auth/email/resend/`,
    forgotPassword: `${API_BASE_URL}/auth/password/reset/request/`,
    resetPassword: `${API_BASE_URL}/auth/password/reset/confirm/`,
  },
  profile: {
    detail: `${API_BASE_URL}/profile/`,
  },
  accounts: {
    create: `${API_BASE_URL}/accounts/`,
    list: `${API_BASE_URL}/accounts/`,
    detail: (accountId: number) => `${API_BASE_URL}/accounts/${accountId}/`,
    createOptions: `${API_BASE_URL}/accounts/create-options/`,
    sidebar: `${API_BASE_URL}/accounts/sidebar/`,
    holdings: (accountId: number) => `${API_BASE_URL}/accounts/${accountId}/holdings/`,
    connections: `${API_BASE_URL}/accounts/connections/`,
    createCustomType: `${API_BASE_URL}/accounts/account-types/custom/`,
  },
  assets: {
    assetTypes: `${API_BASE_URL}/assets/asset-types/`,
    createCustomAssetType: `${API_BASE_URL}/assets/asset-types/custom/`,
    equityLookup: `${API_BASE_URL}/assets/equities/lookup/`,
  },
  ui: {
    dashboardLayouts: `${API_BASE_URL}/ui/dashboard-layouts/`,
    navigationState: `${API_BASE_URL}/ui/navigation-state/`,
  },
};
