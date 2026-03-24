import { API_ENDPOINTS } from "./config";
import { apiRequest } from "./http";

export type AssetTypeOption = {
  id: number;
  name: string;
  slug: string | null;
  is_system: boolean;
};

export type CreateCustomAssetTypePayload = {
  name: string;
};

export type EquityLookupOption = {
  asset_id: string;
  ticker: string;
  name: string;
  sector: string | null;
  industry: string | null;
  exchange_id: number | null;
  currency_code: string | null;
  is_etf: boolean;
  is_fund: boolean;
};

export async function getAssetTypes(): Promise<AssetTypeOption[]> {
  return apiRequest<AssetTypeOption[]>(API_ENDPOINTS.assets.assetTypes, "GET");
}

export async function createCustomAssetType(payload: CreateCustomAssetTypePayload): Promise<AssetTypeOption> {
  return apiRequest<AssetTypeOption>(API_ENDPOINTS.assets.createCustomAssetType, "POST", payload as unknown as Record<string, unknown>);
}

export async function lookupEquities(query: string): Promise<EquityLookupOption[]> {
  const url = new URL(API_ENDPOINTS.assets.equityLookup, window.location.origin);
  url.searchParams.set("q", query);
  return apiRequest<EquityLookupOption[]>(url.toString(), "GET");
}
