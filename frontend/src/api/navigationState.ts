import { API_ENDPOINTS } from "./config";
import { apiRequest } from "./http";

export type NavigationStateResponse = {
  scope: string;
  section_order: string[];
  asset_item_order: string[];
  account_item_order: string[];
  asset_types_collapsed: boolean;
  accounts_collapsed: boolean;
  active_item_key: string;
  updated_at: string | null;
};

export type UpsertNavigationStatePayload = {
  scope: string;
  section_order: string[];
  asset_item_order: string[];
  account_item_order: string[];
  asset_types_collapsed: boolean;
  accounts_collapsed: boolean;
  active_item_key: string;
};

export async function getNavigationState(scope: string): Promise<NavigationStateResponse> {
  const url = new URL(API_ENDPOINTS.portfolios.navigationState);
  url.searchParams.set("scope", scope);
  return apiRequest<NavigationStateResponse>(url.toString(), "GET");
}

export async function upsertNavigationState(payload: UpsertNavigationStatePayload): Promise<NavigationStateResponse> {
  return apiRequest<NavigationStateResponse>(
    API_ENDPOINTS.portfolios.navigationState,
    "PUT",
    payload as unknown as Record<string, unknown>,
  );
}
