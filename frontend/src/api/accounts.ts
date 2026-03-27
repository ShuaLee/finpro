import { API_ENDPOINTS } from "./config";
import { apiRequest } from "./http";

export type SidebarAccount = {
  id: number;
  name: string;
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
  supported_asset_type_slugs?: string[];
};

export type PortfolioOption = {
  id: number;
  name: string;
  kind: string;
};

export type AccountCreateOptions = {
  portfolios: PortfolioOption[];
  account_types: AccountTypeOption[];
};

export type CreateAccountPayload = {
  portfolio_id?: number;
  name?: string;
  account_type_id: number;
  position_mode?: "manual" | "synced" | "ledger" | "hybrid";
  allow_manual_overrides?: boolean;
  enforce_restrictions?: boolean;
  strict_asset_type_enforcement?: boolean;
  allowed_asset_type_slugs?: string[];
  supported_asset_type_slugs?: string[];
};

export type CreateCustomAccountTypePayload = {
  name: string;
  description?: string;
  allowed_asset_type_slugs: string[];
};

export type AccountListItem = {
  id: number;
  portfolio: number;
  name: string;
  account_type: number;
  account_type_name?: string;
  account_type_slug?: string | null;
  last_synced: string | null;
  holdings_count: number;
  active_schema_id?: number | null;
  position_mode?: "manual" | "synced" | "ledger" | "hybrid";
  allow_manual_overrides?: boolean;
  enforce_restrictions?: boolean;
  strict_asset_type_enforcement?: boolean;
  allowed_asset_type_slugs?: string[];
  supported_asset_type_slugs?: string[];
};

export type UpdateAccountPayload = {
  name?: string;
  position_mode?: "manual" | "synced" | "ledger" | "hybrid";
  allow_manual_overrides?: boolean;
  strict_asset_type_enforcement?: boolean;
  supported_asset_type_slugs?: string[];
};

export type BrokerageConnectionListItem = {
  id: number;
  account: number;
  source_type: string;
  provider: string;
  external_account_id?: string | null;
  connection_label?: string | null;
  status: string;
  last_synced_at?: string | null;
  last_error?: string | null;
  created_at: string;
  updated_at: string;
};

export type AccountHolding = {
  id: number;
  account: number;
  asset: string;
  asset_type: string;
  asset_display_name: string;
  original_ticker: string | null;
  quantity: string;
  average_purchase_price: string | null;
  tracking_mode?: "account_default" | "tracked" | "manual";
  effective_tracking_mode?: "tracked" | "manual";
  price_source_mode?: "account_default" | "market" | "manual" | "unavailable";
  effective_price_source_mode?: "market" | "manual" | "unavailable";
  created_at: string;
  updated_at: string;
};

export type CreateHoldingPayload = {
  asset_id?: string;
  quantity: string;
  average_purchase_price?: string;
  asset_type_slug?: string;
  custom_name?: string;
  currency_code?: string;
  tracking_mode?: "account_default" | "tracked" | "manual";
  price_source_mode?: "account_default" | "market" | "manual" | "unavailable";
};

export async function getAccountsSidebar(): Promise<SidebarGroup[]> {
  return apiRequest<SidebarGroup[]>(API_ENDPOINTS.accounts.sidebar, "GET");
}

export async function getAccountsList(): Promise<AccountListItem[]> {
  return apiRequest<AccountListItem[]>(API_ENDPOINTS.accounts.list, "GET");
}

export async function getAccountHoldings(accountId: number): Promise<AccountHolding[]> {
  return apiRequest<AccountHolding[]>(API_ENDPOINTS.accounts.holdings(accountId), "GET");
}

export async function getAccountCreateOptions(): Promise<AccountCreateOptions> {
  return apiRequest<AccountCreateOptions>(API_ENDPOINTS.accounts.createOptions, "GET");
}

export async function createAccount(payload: CreateAccountPayload): Promise<AccountListItem> {
  return apiRequest<AccountListItem>(API_ENDPOINTS.accounts.create, "POST", payload as unknown as Record<string, unknown>);
}

export async function getAccount(accountId: number): Promise<AccountListItem> {
  return apiRequest<AccountListItem>(API_ENDPOINTS.accounts.detail(accountId), "GET");
}

export async function updateAccount(accountId: number, payload: UpdateAccountPayload): Promise<AccountListItem> {
  return apiRequest<AccountListItem>(API_ENDPOINTS.accounts.detail(accountId), "PATCH", payload as unknown as Record<string, unknown>);
}

export async function createCustomAccountType(payload: CreateCustomAccountTypePayload): Promise<AccountTypeOption> {
  return apiRequest<AccountTypeOption>(API_ENDPOINTS.accounts.createCustomType, "POST", payload as unknown as Record<string, unknown>);
}

export async function createAccountHolding(accountId: number, payload: CreateHoldingPayload): Promise<AccountHolding> {
  return apiRequest<AccountHolding>(API_ENDPOINTS.accounts.holdings(accountId), "POST", payload as unknown as Record<string, unknown>);
}

export async function getBrokerageConnections(): Promise<BrokerageConnectionListItem[]> {
  return apiRequest<BrokerageConnectionListItem[]>(API_ENDPOINTS.accounts.connections, "GET");
}
