import { API_ENDPOINTS } from "./config";
import { apiRequest } from "./http";

export type SidebarAccount = {
  id: number;
  name: string;
  broker: string | null;
  holdings_count: number;
  last_synced: string | null;
};

export type SidebarGroup = {
  group_key: string;
  group_label: string;
  accounts: SidebarAccount[];
};

export type AccountTypeOption = {
  id: number;
  name: string;
  slug: string | null;
  is_system: boolean;
  description: string | null;
  allowed_asset_type_slugs: string[];
};

export type PortfolioOption = {
  id: number;
  name: string;
  kind: string;
};

export type ClassificationDefinitionOption = {
  id: number;
  name: string;
  tax_status: string;
};

export type AccountCreateOptions = {
  portfolios: PortfolioOption[];
  account_types: AccountTypeOption[];
  classification_definitions: ClassificationDefinitionOption[];
};

export type CreateAccountPayload = {
  portfolio_id: number;
  name: string;
  account_type_id: number;
  broker?: string;
  classification_definition_id: number;
  position_mode?: "manual" | "brokerage";
  allow_manual_overrides?: boolean;
};

export type AccountListItem = {
  id: number;
  portfolio: number;
  name: string;
  account_type: number;
  broker: string | null;
  last_synced: string | null;
  holdings_count: number;
};

export async function getAccountsSidebar(): Promise<SidebarGroup[]> {
  return apiRequest<SidebarGroup[]>(API_ENDPOINTS.accounts.sidebar, "GET");
}

export async function getAccountsList(): Promise<AccountListItem[]> {
  return apiRequest<AccountListItem[]>(API_ENDPOINTS.accounts.list, "GET");
}

export async function getAccountCreateOptions(): Promise<AccountCreateOptions> {
  return apiRequest<AccountCreateOptions>(API_ENDPOINTS.accounts.createOptions, "GET");
}

export async function createAccount(payload: CreateAccountPayload): Promise<{ id: number }> {
  return apiRequest<{ id: number }>(API_ENDPOINTS.accounts.create, "POST", payload as unknown as Record<string, unknown>);
}
