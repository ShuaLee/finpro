import { API_ENDPOINTS } from "./config";
import { apiRequest } from "./http";

export type DashboardLayoutStateResponse = {
  scope: string;
  active_layout_id: string;
  layouts: Array<Record<string, unknown>>;
  updated_at: string | null;
};

export type UpsertDashboardLayoutStatePayload = {
  scope: string;
  active_layout_id: string;
  layouts: Array<Record<string, unknown>>;
};

export async function getDashboardLayoutState(scope: string): Promise<DashboardLayoutStateResponse> {
  const url = new URL(API_ENDPOINTS.ui.dashboardLayouts);
  url.searchParams.set("scope", scope);
  return apiRequest<DashboardLayoutStateResponse>(url.toString(), "GET");
}

export async function upsertDashboardLayoutState(payload: UpsertDashboardLayoutStatePayload): Promise<DashboardLayoutStateResponse> {
  return apiRequest<DashboardLayoutStateResponse>(
    API_ENDPOINTS.ui.dashboardLayouts,
    "PUT",
    payload as unknown as Record<string, unknown>,
  );
}
