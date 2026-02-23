import { API_ENDPOINTS } from "./config";
import { apiRequest } from "./http";

export type AssetTypeOption = {
  id: number;
  name: string;
  slug: string | null;
  is_system: boolean;
};

export async function getAssetTypes(): Promise<AssetTypeOption[]> {
  return apiRequest<AssetTypeOption[]>(API_ENDPOINTS.assets.assetTypes, "GET");
}
