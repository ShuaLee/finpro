import { useCallback, useEffect, useMemo, useRef, useState, type DragEvent } from "react";
import { useLocation } from "react-router-dom";
import {
  CubeIcon as CubeOutlineIcon,
  HomeIcon as HomeOutlineIcon,
  ListBulletIcon as ListBulletOutlineIcon,
  Squares2X2Icon as Squares2X2OutlineIcon,
  UserCircleIcon as UserCircleOutlineIcon,
  WalletIcon as WalletOutlineIcon,
} from "@heroicons/react/24/outline";
import {
  BriefcaseIcon as BriefcaseSolidIcon,
  CubeIcon as CubeSolidIcon,
  HomeIcon as HomeSolidIcon,
  ListBulletIcon as ListBulletSolidIcon,
  Squares2X2Icon as Squares2X2SolidIcon,
  WalletIcon as WalletSolidIcon,
} from "@heroicons/react/24/solid";
import {
  Coins as CoinsIcon,
  CurrencyDollarSimple as CurrencyDollarSimpleIcon,
  HouseSimple as HouseSimpleIcon,
  Shapes as ShapesIcon,
} from "@phosphor-icons/react";
import {
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Ellipsis,
  Eye,
  EyeOff,
  Grid2x2,
  GripVertical,
  Monitor,
  MoveDiagonal2,
  Plus,
  Settings,
  Smartphone,
  Tablet,
  Trash2,
  X,
} from "lucide-react";

import {
  getAccountCreateOptions,
  getAccountHoldings,
  getAccountsList,
  createAccount,
  createAccountHolding,
  type AccountCreateOptions,
  type AccountHolding,
  type AccountListItem,
} from "../api/accounts";
import { createCustomAssetType, getAssetTypes, lookupEquities, type AssetTypeOption, type EquityLookupOption } from "../api/assets";
import { getDashboardLayoutState, upsertDashboardLayoutState } from "../api/dashboardLayouts";
import { ApiError } from "../api/http";
import { getNavigationState, upsertNavigationState } from "../api/navigationState";
import { Card, CardContent } from "../components/ui/card";
import { useAuth } from "../context/AuthContext";

type DashboardTile = {
  id: number;
  slot: number;
  colSpan: number;
  rowSpan: number;
};

type EditViewport = "mobile" | "tablet" | "desktop";

type ViewportLayout = {
  tiles: DashboardTile[];
  targetRows: number;
  targetColumns: number;
};

type ViewportLayouts = Record<EditViewport, ViewportLayout>;
type TilePreset = {
  id: string;
  label: string;
  spans: Record<EditViewport, { colSpan: number; rowSpan: number }>;
};
type HolderTile = {
  id: number;
  colSpan: number;
  rowSpan: number;
  returnColSpan?: number;
  returnRowSpan?: number;
};
type ViewportHolders = Record<EditViewport, HolderTile[]>;
type NavSectionKey = "addAssets" | "assetTypes" | "accounts";
type NavDashboardTileKey = "portfolioOverview" | "favorites" | "assets" | "accounts" | "custom";
type NavDragKind = "section" | "asset" | "account";
type NavDragItem = {
  kind: NavDragKind;
  key: string;
};
type AppShellSection = "portfolio" | "holdings" | "dashboards" | "accounts" | "assetTypes" | "addAccount";
type PortfolioHoldingRow = AccountHolding & {
  account_name: string;
};
type PortfolioGroupedSection = {
  key: string;
  label: string;
  subtitle: string;
  rows: PortfolioHoldingRow[];
};
type ShellSortMode = "name_asc" | "name_desc" | "value_desc" | "value_asc";
type AddAssetStep = "type" | "account" | "asset";

type SavedLayout = {
  id: string;
  name: string;
  viewportLayouts: ViewportLayouts;
  viewportHolders: ViewportHolders;
  isPrimary: boolean;
  updatedAt: string;
};

type ResizeSession = {
  tileId: number;
  startX: number;
  startY: number;
  startSlot: number;
  startColSpan: number;
  startRowSpan: number;
  startLeft: number;
  startTop: number;
  startWidth: number;
  startHeight: number;
  handle: "tl" | "tr" | "bl" | "br";
};

type DragSession = {
  source: "grid" | "holder";
  tileId: number;
  startX: number;
  startY: number;
  pointerOffsetX: number;
  pointerOffsetY: number;
  ghostWidth: number;
  ghostHeight: number;
  ghostColSpan: number;
  ghostRowSpan: number;
  anchorCol: number;
  anchorRow: number;
};

type GridMetrics = {
  columns: number;
  cellWidth: number;
  cellHeight: number;
  colGap: number;
  rowGap: number;
};

const DESKTOP_COLUMNS = 5;
const BASE_DASHBOARD_ROWS = 5;
const MAX_ROW_SPAN = 8;
const MAX_ROWS = 80;
const MAX_LAYOUT_NAME_LENGTH = 30;
const DEFAULT_LAYOUT_ID = "default";
const DEFAULT_TILES: DashboardTile[] = [{ id: 1, slot: 0, colSpan: 1, rowSpan: 1 }];
const VIEWPORT_DEFAULT_COLUMNS: Record<EditViewport, number> = {
  mobile: 2,
  tablet: 4,
  desktop: 5,
};
const VIEWPORT_MAX_COLUMNS: Record<EditViewport, number> = {
  mobile: 2,
  tablet: 6,
  desktop: 8,
};
const VIEWPORT_MIN_COLUMNS = 1;
const VIEWPORT_BASE_ROWS: Record<EditViewport, number> = {
  mobile: 4,
  tablet: 4,
  desktop: 5,
};
const DEFAULT_NAV_SECTION_ORDER: NavSectionKey[] = ["addAssets", "assetTypes", "accounts"];
const DEFAULT_NAV_DASHBOARD_TILE_ORDER: NavDashboardTileKey[] = ["portfolioOverview", "favorites", "assets", "accounts", "custom"];
const TILE_PRESETS: TilePreset[] = [
  {
    id: "compact",
    label: "Compact",
    spans: {
      desktop: { colSpan: 1, rowSpan: 1 },
      tablet: { colSpan: 1, rowSpan: 1 },
      mobile: { colSpan: 1, rowSpan: 1 },
    },
  },
  {
    id: "wide",
    label: "Wide",
    spans: {
      desktop: { colSpan: 2, rowSpan: 1 },
      tablet: { colSpan: 2, rowSpan: 1 },
      mobile: { colSpan: 2, rowSpan: 1 },
    },
  },
  {
    id: "analytics",
    label: "Analytics",
    spans: {
      desktop: { colSpan: 2, rowSpan: 3 },
      tablet: { colSpan: 2, rowSpan: 3 },
      mobile: { colSpan: 2, rowSpan: 2 },
    },
  },
  {
    id: "overview",
    label: "Overview",
    spans: {
      desktop: { colSpan: 2, rowSpan: 4 },
      tablet: { colSpan: 2, rowSpan: 4 },
      mobile: { colSpan: 2, rowSpan: 2 },
    },
  },
  {
    id: "panel",
    label: "Panel",
    spans: {
      desktop: { colSpan: 3, rowSpan: 2 },
      tablet: { colSpan: 3, rowSpan: 2 },
      mobile: { colSpan: 2, rowSpan: 2 },
    },
  },
];

const normalizeLayoutName = (name: string) => name.trim().slice(0, MAX_LAYOUT_NAME_LENGTH);
const getDisplayLayoutName = (name: string) =>
  name.length > MAX_LAYOUT_NAME_LENGTH ? `${name.slice(0, MAX_LAYOUT_NAME_LENGTH)}...` : name;
const formatSlugLabel = (value: string) =>
  value
    .split("_")
    .join(" ")
    .split("-")
    .join(" ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (match) => match.toUpperCase());
const getFirstNameFromEmail = (email: string | null | undefined) => {
  if (!email) return "Profile";
  const prefix = email.split("@")[0]?.trim();
  if (!prefix) return "Profile";
  const normalized = prefix.replace(/[._-]+/g, " ").trim();
  return normalized ? normalized.replace(/\b\w/g, (match) => match.toUpperCase()).split(" ")[0] : "Profile";
};
const formatNumber = (value: string | number | null | undefined, options?: Intl.NumberFormatOptions) => {
  if (value === null || value === undefined || value === "") return "—";
  const parsed = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(parsed)) return "—";
  return new Intl.NumberFormat("en-US", options).format(parsed);
};
const formatCurrency = (value: string | number | null | undefined) => {
  if (value === null || value === undefined || value === "") return "—";
  const parsed = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(parsed)) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: parsed >= 1000 ? 0 : 2,
  }).format(parsed);
};
const formatDateLabel = (value: string | null | undefined) => {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "—";
  return parsed.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};
const getHoldingValue = (holding: Pick<AccountHolding, "quantity" | "average_purchase_price">) => {
  const quantity = Number(holding.quantity ?? 0);
  const averagePurchasePrice = Number(holding.average_purchase_price ?? 0);
  if (!Number.isFinite(quantity) || !Number.isFinite(averagePurchasePrice)) return 0;
  return Math.max(0, quantity * averagePurchasePrice);
};
const getAddAssetTileIcon = (slug: string | null | undefined) => {
  switch ((slug ?? "").trim().toLowerCase()) {
    case "equity":
      return CurrencyDollarSimpleIcon;
    case "crypto":
      return CoinsIcon;
    case "real_estate":
      return HouseSimpleIcon;
    case "commodity":
    case "precious_metal":
      return ShapesIcon;
    default:
      return ShapesIcon;
  }
};
const getAddAssetTileTone = (_slug: string | null | undefined) => {
  return "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50";
};
const normalizeOrder = (order: string[], available: string[]) => {
  const availableSet = new Set(available);
  const seen = new Set<string>();
  const normalized: string[] = [];
  for (const key of order) {
    if (!availableSet.has(key) || seen.has(key)) continue;
    normalized.push(key);
    seen.add(key);
  }
  for (const key of available) {
    if (seen.has(key)) continue;
    normalized.push(key);
    seen.add(key);
  }
  return normalized;
};
const moveKeyForDrag = (items: string[], sourceKey: string, targetKey: string) => {
  const sourceIndex = items.indexOf(sourceKey);
  const targetIndex = items.indexOf(targetKey);
  if (sourceIndex < 0 || targetIndex < 0 || sourceIndex === targetIndex) return items;
  const next = [...items];
  [next[sourceIndex], next[targetIndex]] = [next[targetIndex], next[sourceIndex]];
  return next;
};

export function AppHomePage() {
  const { user } = useAuth();
  const location = useLocation();
  const [activeAppShellSection, setActiveAppShellSection] = useState<AppShellSection>("dashboards");
  const [isSideNavCollapsed, setIsSideNavCollapsed] = useState(false);
  const [activeSidebarCategory, setActiveSidebarCategory] = useState("portfolio");
  const [activeSidebarLabel, setActiveSidebarLabel] = useState("Portfolio");
  const [assetTypes, setAssetTypes] = useState<AssetTypeOption[]>([]);
  const [accountRows, setAccountRows] = useState<AccountListItem[]>([]);
  const [portfolioHoldings, setPortfolioHoldings] = useState<PortfolioHoldingRow[]>([]);
  const [isPortfolioHoldingsLoading, setIsPortfolioHoldingsLoading] = useState(false);
  const [portfolioHoldingsNotice, setPortfolioHoldingsNotice] = useState<string | null>(null);
  const [portfolioGroupingMode, setPortfolioGroupingMode] = useState<"asset" | "account">("account");
  const [accountsShellSortMode, setAccountsShellSortMode] = useState<ShellSortMode>("value_desc");
  const [assetTypesShellSortMode, setAssetTypesShellSortMode] = useState<ShellSortMode>("value_desc");
  const [collapsedAccountTypeGroups, setCollapsedAccountTypeGroups] = useState<string[]>([]);
  const [collapsedAssetTypeGroups, setCollapsedAssetTypeGroups] = useState<string[]>([]);
  const portfolioDetailMode: "basic" | "detailed" = "detailed";
  const [accountCreateOptions, setAccountCreateOptions] = useState<AccountCreateOptions | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [settingsMenuOpen, setSettingsMenuOpen] = useState(false);
  const [holderMenuOpenId, setHolderMenuOpenId] = useState<number | null>(null);
  const [isNewLayoutDialogOpen, setIsNewLayoutDialogOpen] = useState(false);
  const [isAddTileDialogOpen, setIsAddTileDialogOpen] = useState(false);
  const [layoutNameDialogMode, setLayoutNameDialogMode] = useState<"create" | "rename">("create");
  const [layoutActionsMenuOpen, setLayoutActionsMenuOpen] = useState(false);
  const [isGridOptionsMenuOpen, setIsGridOptionsMenuOpen] = useState(false);
  const [isAddAssetModalOpen, setIsAddAssetModalOpen] = useState(false);
  const [addAssetStep, setAddAssetStep] = useState<AddAssetStep>("type");
  const [selectedAddAssetType, setSelectedAddAssetType] = useState<AssetTypeOption | null>(null);
  const [selectedAddAssetAccountId, setSelectedAddAssetAccountId] = useState<number | null>(null);
  const [isAddAccountInlineOpen, setIsAddAccountInlineOpen] = useState(false);
  const [equitySearchQuery, setEquitySearchQuery] = useState("");
  const [equitySearchResults, setEquitySearchResults] = useState<EquityLookupOption[]>([]);
  const [isEquitySearchLoading, setIsEquitySearchLoading] = useState(false);
  const [selectedEquityResult, setSelectedEquityResult] = useState<EquityLookupOption | null>(null);
  const [newHoldingQuantity, setNewHoldingQuantity] = useState("");
  const [newHoldingAverageCost, setNewHoldingAverageCost] = useState("");
  const [addAssetFlowError, setAddAssetFlowError] = useState<string | null>(null);
  const [isSubmittingHolding, setIsSubmittingHolding] = useState(false);
  const [newAccountName, setNewAccountName] = useState("");
  const [newAccountBroker, setNewAccountBroker] = useState("");
  const [newAccountPortfolioId, setNewAccountPortfolioId] = useState<number | null>(null);
  const [newAccountTypeId, setNewAccountTypeId] = useState<number | null>(null);
  const [newAccountClassificationId, setNewAccountClassificationId] = useState<number | null>(null);
  const [isCreatingAccount, setIsCreatingAccount] = useState(false);
  const [isAddAssetTypeViewOpen, setIsAddAssetTypeViewOpen] = useState(false);
  const [newAssetTypeName, setNewAssetTypeName] = useState("");
  const [newAssetTypeError, setNewAssetTypeError] = useState<string | null>(null);
  const [isCreatingAssetType, setIsCreatingAssetType] = useState(false);
  const [overviewCollapsed, setOverviewCollapsed] = useState(false);
  const [favoritesCollapsed, setFavoritesCollapsed] = useState(false);
  const [assetTypesCollapsed, setAssetTypesCollapsed] = useState(false);
  const [accountsCollapsed, setAccountsCollapsed] = useState(false);
  const [customDashboardsCollapsed, setCustomDashboardsCollapsed] = useState(false);
  const [favoritesActionsMenuOpen, setFavoritesActionsMenuOpen] = useState(false);
  const [assetsActionsMenuOpen, setAssetsActionsMenuOpen] = useState(false);
  const [customActionsMenuOpen, setCustomActionsMenuOpen] = useState(false);
  const [favoritesActionsSubmenu, setFavoritesActionsSubmenu] = useState<"filter" | "sort" | null>(null);
  const [assetsActionsSubmenu, setAssetsActionsSubmenu] = useState<"filter" | "sort" | null>(null);
  const [customActionsSubmenu, setCustomActionsSubmenu] = useState<"filter" | "sort" | null>(null);
  const [accountsActionsSubmenu, setAccountsActionsSubmenu] = useState<"filter" | "sort" | null>(null);
  const [accountsActionsMenuOpen, setAccountsActionsMenuOpen] = useState(false);
  const [dashboardTilesEditMode, setDashboardTilesEditMode] = useState(false);
  const [dashboardTilesMenuOpen, setDashboardTilesMenuOpen] = useState(false);
  const [dashboardTilesConfirmOpen, setDashboardTilesConfirmOpen] = useState(false);
  const [dashboardTilesCancelOpen, setDashboardTilesCancelOpen] = useState(false);
  const [hiddenDashboardTileKeys, setHiddenDashboardTileKeys] = useState<NavDashboardTileKey[]>([]);
  const [hiddenNavButtonKeys, setHiddenNavButtonKeys] = useState<string[]>([]);
  const [assetFilterMode, setAssetFilterMode] = useState<"all" | "system" | "custom">("all");
  const [assetSortMode, setAssetSortMode] = useState<"name_asc" | "name_desc">("name_asc");
  const [assetsLiabilitiesTypeSelection, setAssetsLiabilitiesTypeSelection] = useState("investments");
  const [favoritesFilterMode, setFavoritesFilterMode] = useState<"all" | "asset_type" | "account">("all");
  const [favoritesSortMode, setFavoritesSortMode] = useState<"name_asc" | "name_desc">("name_asc");
  const [customFilterMode, setCustomFilterMode] = useState<"all" | "portfolio" | "accounts">("all");
  const [customSortMode, setCustomSortMode] = useState<"recent" | "name_asc" | "name_desc">("recent");
  const [selectedAccountTypeIds, setSelectedAccountTypeIds] = useState<number[]>([]);
  const [accountSortMode, setAccountSortMode] = useState<"name_asc" | "name_desc" | "value_desc" | "value_asc" | "type_asc">("name_asc");
  const [assetTypeSearch] = useState("");
  const [hasHydratedNavState, setHasHydratedNavState] = useState(false);
  const [navEditMode, setNavEditMode] = useState(false);
  const [buttonEditTarget, setButtonEditTarget] = useState<"assetTypes" | "accounts" | "all" | null>(null);
  const [navSectionOrder, setNavSectionOrder] = useState<NavSectionKey[]>(DEFAULT_NAV_SECTION_ORDER);
  const [navDashboardTileOrder, setNavDashboardTileOrder] = useState<NavDashboardTileKey[]>(DEFAULT_NAV_DASHBOARD_TILE_ORDER);
  const [navAssetItemOrder, setNavAssetItemOrder] = useState<string[]>([]);
  const [navAccountItemOrder, setNavAccountItemOrder] = useState<string[]>([]);
  const [draftNavSectionOrder, setDraftNavSectionOrder] = useState<NavSectionKey[]>(DEFAULT_NAV_SECTION_ORDER);
  const [draftNavDashboardTileOrder, setDraftNavDashboardTileOrder] = useState<NavDashboardTileKey[]>(DEFAULT_NAV_DASHBOARD_TILE_ORDER);
  const [draftNavAssetItemOrder, setDraftNavAssetItemOrder] = useState<string[]>([]);
  const [draftNavAccountItemOrder, setDraftNavAccountItemOrder] = useState<string[]>([]);
  const [navDragItem, setNavDragItem] = useState<NavDragItem | null>(null);
  const [navDropTarget, setNavDropTarget] = useState<NavDragItem | null>(null);
  const [navTileDragKey, setNavTileDragKey] = useState<NavDashboardTileKey | null>(null);
  const [navTileDropKey, setNavTileDropKey] = useState<NavDashboardTileKey | null>(null);
  const navDragItemRef = useRef<NavDragItem | null>(null);
  const navHoverTargetRef = useRef<NavDragItem | null>(null);
  const navDropTargetRef = useRef<NavDragItem | null>(null);
  const navSectionSlotRef = useRef<Array<{ key: string; top: number; bottom: number }>>([]);
  const navAssetSlotRef = useRef<Array<{ key: string; top: number; bottom: number }>>([]);
  const navAccountSlotRef = useRef<Array<{ key: string; top: number; bottom: number }>>([]);
  const transparentDragImageRef = useRef<HTMLImageElement | null>(null);
  const navButtonDragImageRef = useRef<HTMLElement | null>(null);
  const navButtonDragOffsetRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const navTileDragImageRef = useRef<HTMLElement | null>(null);
  const navTileDragOffsetRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const [pendingLayoutName, setPendingLayoutName] = useState("");
  const [layoutNameError, setLayoutNameError] = useState<string | null>(null);
  const [isSwitchLayoutDialogOpen, setIsSwitchLayoutDialogOpen] = useState(false);
  const [pendingSwitchLayoutId, setPendingSwitchLayoutId] = useState<string | null>(null);
  const [pendingCreateLayout, setPendingCreateLayout] = useState(false);
  const [isExitActionsMenuOpen, setIsExitActionsMenuOpen] = useState(false);
  const [isExitBlockedDialogOpen, setIsExitBlockedDialogOpen] = useState(false);
  const [isSetActiveDialogOpen, setIsSetActiveDialogOpen] = useState(false);
  const [pendingSetActiveLayoutId, setPendingSetActiveLayoutId] = useState<string | null>(null);
  const [viewportLayouts, setViewportLayouts] = useState<ViewportLayouts>(() => createDefaultViewportLayouts());
  const [viewportHolders, setViewportHolders] = useState<ViewportHolders>(() => createDefaultViewportHolders());
  const [nextTileId, setNextTileId] = useState(2);
  const [savedLayouts, setSavedLayouts] = useState<SavedLayout[]>([]);
  const [activeLayoutId, setActiveLayoutId] = useState(DEFAULT_LAYOUT_ID);
  const [editingViewport, setEditingViewport] = useState<EditViewport>("desktop");
  const [activeDropSlot, setActiveDropSlot] = useState<number | null>(null);
  const [draggingTileId, setDraggingTileId] = useState<number | null>(null);
  const [gridMetrics, setGridMetrics] = useState<GridMetrics | null>(null);
  const [resizeSession, setResizeSession] = useState<ResizeSession | null>(null);
  const [resizePreview, setResizePreview] = useState<{ tileId: number; slot: number; colSpan: number; rowSpan: number } | null>(null);
  const [resizeVisual, setResizeVisual] = useState<{ tileId: number; left: number; top: number; width: number; height: number } | null>(
    null,
  );
  const [dragSession, setDragSession] = useState<DragSession | null>(null);
  const [dragPreview, setDragPreview] = useState<{ tileId: number; x: number; y: number; width: number; height: number } | null>(null);
  const [isOverHolderDrop, setIsOverHolderDrop] = useState(false);
  const [windowWidth, setWindowWidth] = useState<number>(() => (typeof window === "undefined" ? 1440 : window.innerWidth));
  const [isManageGridMode, setIsManageGridMode] = useState(false);
  const [isDeleteStructureMode, setIsDeleteStructureMode] = useState(false);
  const [selectedDeleteRows, setSelectedDeleteRows] = useState<number[]>([]);
  const [selectedDeleteCols, setSelectedDeleteCols] = useState<number[]>([]);
  const [hoveredDeleteRow, setHoveredDeleteRow] = useState<number | null>(null);
  const [hoveredDeleteCol, setHoveredDeleteCol] = useState<number | null>(null);
  const gridRef = useRef<HTMLDivElement | null>(null);
  const gridScrollRef = useRef<HTMLDivElement | null>(null);
  const overlayRef = useRef<HTMLDivElement | null>(null);
  const holderDropRef = useRef<HTMLDivElement | null>(null);
  const navEditPanelRef = useRef<HTMLDivElement | null>(null);
  const tileRefs = useRef<Record<number, HTMLDivElement | null>>({});

  const displayViewport: EditViewport = windowWidth < 768 ? "mobile" : windowWidth < 1280 ? "tablet" : "desktop";
  const profileFirstName = getFirstNameFromEmail(user?.email);
  const activeViewport: EditViewport = isEditing ? editingViewport : displayViewport;
  const columns = clamp(
    viewportLayouts[activeViewport]?.targetColumns ?? VIEWPORT_DEFAULT_COLUMNS[activeViewport],
    VIEWPORT_MIN_COLUMNS,
    VIEWPORT_MAX_COLUMNS[activeViewport],
  );
  const tiles = viewportLayouts[activeViewport].tiles;
  const targetRows = viewportLayouts[activeViewport].targetRows;
  const heldTileIds = viewportHolders[activeViewport];
  const hasParkedTilesAcrossViewports = (["mobile", "tablet", "desktop"] as EditViewport[]).some(
    (viewport) => viewportHolders[viewport].length > 0,
  );
  const setTargetRows = (
    updater: number | ((previous: number) => number),
    viewport: EditViewport = activeViewport,
  ) => {
    setViewportLayouts((previous) => ({
      ...previous,
      [viewport]: {
        ...previous[viewport],
        targetRows: typeof updater === "function" ? (updater as (previous: number) => number)(previous[viewport].targetRows) : updater,
      },
    }));
  };
  const sectionLabel = activeSidebarLabel;
  const defaultLayoutName = `${sectionLabel} Default Layout`;
  const dashboardScope = activeSidebarCategory;
  const navigationScope = "left-nav";
  const navVisibilityStorageKey = `finpro.nav.visibility.${(user?.email ?? "anonymous").toLowerCase()}.${navigationScope}`;
  const legacyStorageKey = `finpro.dashboard.layouts.${(user?.email ?? "anonymous").toLowerCase()}.${dashboardScope}`;

  const normalizePrimary = (layouts: SavedLayout[]) => {
    if (layouts.length === 0) return layouts;
    const primaryCount = layouts.filter((layout) => layout.isPrimary).length;
    if (primaryCount === 1) return layouts;
    return layouts.map((layout, index) => ({ ...layout, isPrimary: index === 0 }));
  };

  const applyLayout = (layout: SavedLayout) => {
    const normalizedViewportLayouts = normalizeAllViewportLayouts(layout.viewportLayouts);
    const normalizedViewportHolders = normalizeViewportHolders(layout.viewportHolders);
    setViewportLayouts(normalizedViewportLayouts);
    setViewportHolders(normalizedViewportHolders);
    const maxId = (Object.values(normalizedViewportLayouts).flatMap((viewport) => viewport.tiles)).reduce(
      (max, tile) => Math.max(max, tile.id),
      0,
    );
    const maxHeldId = Object.values(normalizedViewportHolders).flat().reduce((max, holderTile) => Math.max(max, holderTile.id), 0);
    setNextTileId(Math.max(maxId, maxHeldId) + 1);
  };

  const persistLayouts = (layouts: SavedLayout[], activeId: string) => {
    const normalized = normalizePrimary(layouts);
    localStorage.setItem(legacyStorageKey, JSON.stringify({ activeLayoutId: activeId, layouts: normalized }));
    void upsertDashboardLayoutState({
      scope: dashboardScope,
      active_layout_id: activeId,
      layouts: normalized as unknown as Array<Record<string, unknown>>,
    }).catch(() => {
      // Keep edit flow responsive if persistence fails.
    });
  };

  const saveCurrentLayout = (
    layoutId: string,
    layoutName: string,
    exitEdit: boolean,
    sourceViewportLayouts: ViewportLayouts = viewportLayouts,
    sourceViewportHolders: ViewportHolders = viewportHolders,
  ) => {
    const now = new Date().toISOString();
    const normalizedViewportLayouts = trimAllViewportLayoutsRows(sourceViewportLayouts);
    const normalizedViewportHolders = normalizeViewportHolders(sourceViewportHolders);
    const snapshot: SavedLayout = {
      id: layoutId,
      name: normalizeLayoutName(layoutName),
      viewportLayouts: normalizedViewportLayouts,
      viewportHolders: normalizedViewportHolders,
      isPrimary: savedLayouts.find((layout) => layout.id === layoutId)?.isPrimary ?? false,
      updatedAt: now,
    };

    const nextLayouts = normalizePrimary((() => {
      const index = savedLayouts.findIndex((layout) => layout.id === layoutId);
      if (index === -1) return [...savedLayouts, snapshot];
      return savedLayouts.map((layout, idx) => (idx === index ? snapshot : layout));
    })());

    setSavedLayouts(nextLayouts);
    setActiveLayoutId(layoutId);
    setViewportLayouts(normalizedViewportLayouts);
    setViewportHolders(normalizedViewportHolders);
    persistLayouts(nextLayouts, layoutId);
    if (exitEdit) setIsEditing(false);
    return nextLayouts;
  };

  const switchLayout = (layoutId: string, layoutsSource: SavedLayout[] = savedLayouts) => {
    const layout = layoutsSource.find((item) => item.id === layoutId);
    if (!layout) return;
    setActiveLayoutId(layoutId);
    applyLayout(layout);
    persistLayouts(layoutsSource, layoutId);
  };

  const setPrimaryLayout = (layoutId: string) => {
    const nextLayouts = savedLayouts.map((layout) => ({ ...layout, isPrimary: layout.id === layoutId }));
    setSavedLayouts(nextLayouts);
    setActiveLayoutId(layoutId);
    persistLayouts(nextLayouts, layoutId);
  };

  const activeLayout = useMemo(
    () => savedLayouts.find((layout) => layout.id === activeLayoutId) ?? null,
    [activeLayoutId, savedLayouts],
  );
  const activeMarkedLayout = useMemo(
    () => savedLayouts.find((layout) => layout.isPrimary) ?? savedLayouts[0] ?? null,
    [savedLayouts],
  );
  const fallbackAssetTypesFromAccountTypes = useMemo<AssetTypeOption[]>(() => {
    const slugSet = new Set<string>();
    const next: AssetTypeOption[] = [];
    for (const type of accountCreateOptions?.account_types ?? []) {
      for (const slug of type.allowed_asset_type_slugs ?? []) {
        const clean = slug.trim();
        if (!clean || slugSet.has(clean)) continue;
        slugSet.add(clean);
        next.push({
          id: -next.length - 1,
          name: formatSlugLabel(clean),
          slug: clean,
          is_system: true,
        });
      }
    }
    return next;
  }, [accountCreateOptions]);
  const assetTypesForNav = assetTypes.length > 0 ? assetTypes : fallbackAssetTypesFromAccountTypes;
  const sideNavWidthClass = isSideNavCollapsed ? "w-[84px]" : "w-[228px]";
  const sideNavLeftOffsetClass = isSideNavCollapsed ? "lg:left-[84px]" : "lg:left-[228px]";
  const sideNavContentInsetClass = isSideNavCollapsed ? "lg:pl-[92px] lg:pr-[48px]" : "lg:pl-[252px] lg:pr-[48px]";
  const topNavInsetClass = isSideNavCollapsed ? "lg:pl-4 lg:pr-[48px]" : "lg:pl-6 lg:pr-[48px]";
  const assetTypeNameBySlug = useMemo(
    () =>
      new Map(
        assetTypesForNav
          .filter((assetType): assetType is AssetTypeOption & { slug: string } => typeof assetType.slug === "string" && assetType.slug.trim().length > 0)
          .map((assetType) => [assetType.slug, assetType.name] as const),
      ),
    [assetTypesForNav],
  );
  const assetTypeSortOrder = useMemo(
    () =>
      new Map(
        assetTypesForNav
          .filter((assetType): assetType is AssetTypeOption & { slug: string } => typeof assetType.slug === "string" && assetType.slug.trim().length > 0)
          .map((assetType, index) => [assetType.slug, index] as const),
      ),
    [assetTypesForNav],
  );
  const assetTypeEntries = useMemo(
    () =>
      assetTypesForNav.map((assetType) => ({
        key: `asset-type:${assetType.slug ?? assetType.id}`,
        assetType,
      })),
    [assetTypesForNav],
  );
  const addAssetModalAssetTypes = useMemo(() => {
    const withLabel = assetTypesForNav.map((assetType) => ({
      ...assetType,
      normalizedName: assetType.name.trim().toLowerCase(),
    }));
    return withLabel.sort((a, b) => {
      const aIsEquity = a.normalizedName === "equity" || a.normalizedName === "equities";
      const bIsEquity = b.normalizedName === "equity" || b.normalizedName === "equities";
      if (aIsEquity && !bIsEquity) return -1;
      if (!aIsEquity && bIsEquity) return 1;
      return a.name.localeCompare(b.name);
    });
  }, [assetTypesForNav]);
  const selectedAddAssetSlug = selectedAddAssetType?.slug ?? null;
  const accountEntries = useMemo(
    () =>
      accountRows.map((account) => ({
        key: `account:${account.id}`,
        account,
      })),
    [accountRows],
  );
  const sectionOrderForRender = useMemo(
    () => normalizeOrder(navEditMode ? draftNavSectionOrder : navSectionOrder, DEFAULT_NAV_SECTION_ORDER) as NavSectionKey[],
    [draftNavSectionOrder, navEditMode, navSectionOrder],
  );
  const dashboardTileOrderForRender = useMemo(
    () =>
      (dashboardTilesEditMode || navEditMode
        ? normalizeOrder(draftNavDashboardTileOrder, DEFAULT_NAV_DASHBOARD_TILE_ORDER)
        : normalizeOrder(navDashboardTileOrder, DEFAULT_NAV_DASHBOARD_TILE_ORDER)) as NavDashboardTileKey[],
    [dashboardTilesEditMode, draftNavDashboardTileOrder, navDashboardTileOrder, navEditMode],
  );
  const isButtonSortMode = dashboardTilesEditMode || navEditMode;
  const assetOrderForRender = isButtonSortMode ? draftNavAssetItemOrder : navAssetItemOrder;
  const accountOrderForRender = isButtonSortMode ? draftNavAccountItemOrder : navAccountItemOrder;
  const sectionOrderForView = useMemo(() => {
    if (
      !navDragItem
      || !navDropTarget
      || navDragItem.kind !== "section"
      || navDropTarget.kind !== "section"
      || navDropTarget.key === navDragItem.key
    ) {
      return sectionOrderForRender;
    }
    return moveKeyForDrag(sectionOrderForRender, navDragItem.key, navDropTarget.key) as NavSectionKey[];
  }, [navDragItem, navDropTarget, sectionOrderForRender]);
  const assetOrderForView = useMemo(() => {
    if (dashboardTilesEditMode) {
      return assetOrderForRender;
    }
    if (
      !isButtonSortMode
      || !navDragItem
      || !navDropTarget
      || navDragItem.kind !== "asset"
      || navDropTarget.kind !== "asset"
      || navDropTarget.key === navDragItem.key
    ) {
      return assetOrderForRender;
    }
    return moveKeyForDrag(assetOrderForRender, navDragItem.key, navDropTarget.key);
  }, [assetOrderForRender, isButtonSortMode, navDragItem, navDropTarget]);
  const accountOrderForView = useMemo(() => {
    if (dashboardTilesEditMode) {
      return accountOrderForRender;
    }
    if (
      !isButtonSortMode
      || !navDragItem
      || !navDropTarget
      || navDragItem.kind !== "account"
      || navDropTarget.kind !== "account"
      || navDropTarget.key === navDragItem.key
    ) {
      return accountOrderForRender;
    }
    return moveKeyForDrag(accountOrderForRender, navDragItem.key, navDropTarget.key);
  }, [accountOrderForRender, dashboardTilesEditMode, isButtonSortMode, navDragItem, navDropTarget]);
  const canEditButtonsForKind = (kind: NavDragKind) =>
    (dashboardTilesEditMode && (kind === "asset" || kind === "account"))
    || (navEditMode && (
      (buttonEditTarget === "assetTypes" && kind === "asset")
      || (buttonEditTarget === "accounts" && kind === "account")
    ));
  const isManagingSections = navEditMode && (buttonEditTarget === null || buttonEditTarget === "all");
  const canDragKind = (kind: NavDragKind) => kind === "section" || canEditButtonsForKind(kind);
  const orderedAssetEntries = useMemo(() => {
    const keyToEntry = new Map(assetTypeEntries.map((entry) => [entry.key, entry] as const));
    const orderedKeys = normalizeOrder(assetOrderForView, assetTypeEntries.map((entry) => entry.key));
    return orderedKeys.map((key) => keyToEntry.get(key)).filter(Boolean) as typeof assetTypeEntries;
  }, [assetOrderForView, assetTypeEntries]);
  const filteredOrderedAssetEntries = useMemo(() => {
    const term = assetTypeSearch.trim().toLowerCase();
    if (!term) return orderedAssetEntries;
    return orderedAssetEntries.filter((entry) => entry.assetType.name.toLowerCase().includes(term));
  }, [assetTypeSearch, orderedAssetEntries]);
  const displayedAssetEntries = useMemo(() => {
    return filteredOrderedAssetEntries.filter((entry) => {
      if (assetFilterMode === "system") return entry.assetType.is_system;
      if (assetFilterMode === "custom") return !entry.assetType.is_system;
      return true;
    });
  }, [assetFilterMode, filteredOrderedAssetEntries]);
  const systemAssetTypes = useMemo(
    () => displayedAssetEntries.filter((entry) => entry.assetType.is_system),
    [displayedAssetEntries],
  );
  const customAssetTypes = useMemo(
    () => displayedAssetEntries.filter((entry) => !entry.assetType.is_system),
    [displayedAssetEntries],
  );
  const orderedAccountEntries = useMemo(() => {
    const keyToEntry = new Map(accountEntries.map((entry) => [entry.key, entry] as const));
    const orderedKeys = normalizeOrder(accountOrderForView, accountEntries.map((entry) => entry.key));
    return orderedKeys.map((key) => keyToEntry.get(key)).filter(Boolean) as typeof accountEntries;
  }, [accountEntries, accountOrderForView]);
  const accountTypeNameById = useMemo(
    () => new Map((accountCreateOptions?.account_types ?? []).map((type) => [type.id, type.name] as const)),
    [accountCreateOptions],
  );
  const eligibleAccountTypesForSelectedAsset = useMemo(() => {
    if (!selectedAddAssetSlug) return [];
    return (accountCreateOptions?.account_types ?? []).filter((accountType) =>
      (accountType.allowed_asset_type_slugs ?? []).includes(selectedAddAssetSlug),
    );
  }, [accountCreateOptions?.account_types, selectedAddAssetSlug]);
  const eligibleAccountTypeIds = useMemo(
    () => new Set(eligibleAccountTypesForSelectedAsset.map((accountType) => accountType.id)),
    [eligibleAccountTypesForSelectedAsset],
  );
  const eligibleAccountsForSelectedAsset = useMemo(
    () => accountRows.filter((account) => eligibleAccountTypeIds.has(account.account_type)),
    [accountRows, eligibleAccountTypeIds],
  );
  const brokerageAccountType = useMemo(
    () => eligibleAccountTypesForSelectedAsset.find((accountType) => accountType.slug === "brokerage") ?? null,
    [eligibleAccountTypesForSelectedAsset],
  );
  const accountTypeIdByAccountId = useMemo(
    () => new Map(accountRows.map((account) => [account.id, account.account_type] as const)),
    [accountRows],
  );
  const portfolioHoldingsByType = useMemo<PortfolioGroupedSection[]>(() => {
    const grouped = new Map<string, { slug: string; label: string; rows: PortfolioHoldingRow[] }>();
    for (const holding of portfolioHoldings) {
      const slug = holding.asset_type;
      const existing = grouped.get(slug);
      if (existing) {
        existing.rows.push(holding);
        continue;
      }
      grouped.set(slug, {
        slug,
        label: assetTypeNameBySlug.get(slug) ?? formatSlugLabel(slug),
        rows: [holding],
      });
    }
    return Array.from(grouped.values())
      .map((group) => ({
        key: group.slug,
        ...group,
        subtitle: `${group.rows.length} ${group.rows.length === 1 ? "holding" : "holdings"}`,
        rows: [...group.rows].sort((a, b) => {
          const nameCompare = a.asset_display_name.localeCompare(b.asset_display_name);
          if (nameCompare !== 0) return nameCompare;
          return a.account_name.localeCompare(b.account_name);
        }),
      }))
      .sort((a, b) => {
        const aOrder = assetTypeSortOrder.get(a.slug) ?? Number.MAX_SAFE_INTEGER;
        const bOrder = assetTypeSortOrder.get(b.slug) ?? Number.MAX_SAFE_INTEGER;
        if (aOrder !== bOrder) return aOrder - bOrder;
        return a.label.localeCompare(b.label);
      });
  }, [assetTypeNameBySlug, assetTypeSortOrder, portfolioHoldings]);
  const portfolioHoldingsByAccount = useMemo<PortfolioGroupedSection[]>(() => {
    const grouped = new Map<number, { key: string; label: string; subtitle: string; rows: PortfolioHoldingRow[] }>();
    for (const holding of portfolioHoldings) {
      const existing = grouped.get(holding.account);
      if (existing) {
        existing.rows.push(holding);
        continue;
      }
      grouped.set(holding.account, {
        key: `account-${holding.account}`,
        label: holding.account_name,
        subtitle: accountTypeNameById.get(accountTypeIdByAccountId.get(holding.account) ?? -1) ?? "Account",
        rows: [holding],
      });
    }
    return Array.from(grouped.values())
      .map((group) => ({
        ...group,
        rows: [...group.rows].sort((a, b) => {
          const typeCompare = (assetTypeNameBySlug.get(a.asset_type) ?? formatSlugLabel(a.asset_type)).localeCompare(
            assetTypeNameBySlug.get(b.asset_type) ?? formatSlugLabel(b.asset_type),
          );
          if (typeCompare !== 0) return typeCompare;
          return a.asset_display_name.localeCompare(b.asset_display_name);
        }),
      }))
      .sort((a, b) => a.label.localeCompare(b.label));
  }, [accountTypeIdByAccountId, accountTypeNameById, assetTypeNameBySlug, portfolioHoldings]);
  const portfolioGroupedSections = portfolioGroupingMode === "asset" ? portfolioHoldingsByType : portfolioHoldingsByAccount;
  const holdingValueByAccountId = useMemo(() => {
    const totals = new Map<number, number>();
    for (const holding of portfolioHoldings) {
      totals.set(holding.account, (totals.get(holding.account) ?? 0) + getHoldingValue(holding));
    }
    return totals;
  }, [portfolioHoldings]);
  const sortShellRows = useCallback(<T extends { label: string; value: number }>(items: T[], mode: ShellSortMode) => {
    const next = [...items];
    next.sort((a, b) => {
      if (mode === "value_desc") return b.value - a.value || a.label.localeCompare(b.label);
      if (mode === "value_asc") return a.value - b.value || a.label.localeCompare(b.label);
      if (mode === "name_desc") return b.label.localeCompare(a.label);
      return a.label.localeCompare(b.label);
    });
    return next;
  }, []);
  const accountsShellGroups = useMemo(() => {
    const accountTypeMetaById = new Map((accountCreateOptions?.account_types ?? []).map((type) => [type.id, type] as const));
    const grouped = new Map<
      string,
      {
        key: string;
        label: string;
        totalValue: number;
        items: Array<{ key: string; label: string; subtitle: string | null; value: number }>;
      }
    >();
    for (const account of accountRows) {
      const typeMeta = accountTypeMetaById.get(account.account_type);
      const groupKey = typeMeta?.slug ?? `account-type-${account.account_type}`;
      const groupLabel = typeMeta?.name ?? "Account Type";
      const accountValue = holdingValueByAccountId.get(account.id) ?? 0;
      const existing = grouped.get(groupKey);
      if (existing) {
        existing.totalValue += accountValue;
        existing.items.push({
          key: `account-${account.id}`,
          label: account.name,
          subtitle: account.broker || null,
          value: accountValue,
        });
      } else {
        grouped.set(groupKey, {
          key: groupKey,
          label: groupLabel,
          totalValue: accountValue,
          items: [
            {
              key: `account-${account.id}`,
              label: account.name,
              subtitle: account.broker || null,
              value: accountValue,
            },
          ],
        });
      }
    }
    const groups = Array.from(grouped.values()).map((group) => ({
      ...group,
      items: sortShellRows(group.items, accountsShellSortMode),
    }));
    return sortShellRows(
      groups.map((group) => ({ label: group.label, value: group.totalValue })),
      accountsShellSortMode,
    ).map((sorted) => groups.find((group) => group.label === sorted.label)!).filter(Boolean);
  }, [accountCreateOptions?.account_types, accountRows, accountsShellSortMode, holdingValueByAccountId, sortShellRows]);
  const assetTypesShellGroups = useMemo(() => {
    const grouped = new Map<
      string,
      {
        key: string;
        label: string;
        totalValue: number;
        items: Array<{ key: string; label: string; subtitle: string | null; value: number }>;
      }
    >();
    for (const holding of portfolioHoldings) {
      const assetTypeSlug = holding.asset_type;
      const groupLabel = assetTypeNameBySlug.get(assetTypeSlug) ?? formatSlugLabel(assetTypeSlug);
      const holdingValue = getHoldingValue(holding);
      const itemKey = `${assetTypeSlug}:${holding.asset_display_name}`;
      const existing = grouped.get(assetTypeSlug);
      if (existing) {
        existing.totalValue += holdingValue;
        const item = existing.items.find((entry) => entry.key === itemKey);
        if (item) {
          item.value += holdingValue;
        } else {
          existing.items.push({
            key: itemKey,
            label: holding.asset_display_name,
            subtitle: holding.original_ticker || null,
            value: holdingValue,
          });
        }
      } else {
        grouped.set(assetTypeSlug, {
          key: assetTypeSlug,
          label: groupLabel,
          totalValue: holdingValue,
          items: [
            {
              key: itemKey,
              label: holding.asset_display_name,
              subtitle: holding.original_ticker || null,
              value: holdingValue,
            },
          ],
        });
      }
    }
    const groups = Array.from(grouped.values()).map((group) => ({
      ...group,
      items: sortShellRows(group.items, assetTypesShellSortMode),
    }));
    return sortShellRows(
      groups.map((group) => ({ label: group.label, value: group.totalValue })),
      assetTypesShellSortMode,
    ).map((sorted) => groups.find((group) => group.label === sorted.label)!).filter(Boolean);
  }, [assetTypeNameBySlug, assetTypesShellSortMode, portfolioHoldings, sortShellRows]);
  const displayedAccountEntries = useMemo(() => {
    return selectedAccountTypeIds.length > 0
      ? orderedAccountEntries.filter((entry) => selectedAccountTypeIds.includes(entry.account.account_type))
      : orderedAccountEntries;
  }, [orderedAccountEntries, selectedAccountTypeIds]);
  const addAccountTypeTiles = useMemo(() => {
    const accountTypes = [...(accountCreateOptions?.account_types ?? [])];
    accountTypes.sort((a, b) => {
      if (a.is_system !== b.is_system) return a.is_system ? -1 : 1;
      return a.name.localeCompare(b.name);
    });
    return accountTypes;
  }, [accountCreateOptions?.account_types]);
  const hasUnsavedChanges = useMemo(() => {
    if (!activeLayout) return false;
    const currentSignature = JSON.stringify({
      viewportLayouts: normalizeAllViewportLayouts(viewportLayouts),
      viewportHolders: normalizeViewportHolders(viewportHolders),
    });
    const savedSignature = JSON.stringify({
      viewportLayouts: normalizeAllViewportLayouts(activeLayout.viewportLayouts),
      viewportHolders: normalizeViewportHolders(activeLayout.viewportHolders),
    });
    return currentSignature !== savedSignature;
  }, [activeLayout, viewportHolders, viewportLayouts]);

  const createNewLayout = (layoutName: string) => {
    const id = `layout_${Date.now()}`;
    const name = normalizeLayoutName(layoutName);
    if (!name) return;
    const duplicateExists = savedLayouts.some((layout) => normalizeLayoutName(layout.name).toLowerCase() === name.toLowerCase());
    if (duplicateExists) return;
    saveCurrentLayout(id, name, false, createDefaultViewportLayouts(), createDefaultViewportHolders());
  };

  const renameActiveLayout = (layoutName: string) => {
    if (!activeLayout) return;
    const name = normalizeLayoutName(layoutName);
    if (!name) return;
    const duplicateExists = savedLayouts.some(
      (layout) => layout.id !== activeLayout.id && normalizeLayoutName(layout.name).toLowerCase() === name.toLowerCase(),
    );
    if (duplicateExists) return;
    const nextLayouts = savedLayouts.map((layout) => (layout.id === activeLayout.id ? { ...layout, name, updatedAt: new Date().toISOString() } : layout));
    setSavedLayouts(nextLayouts);
    persistLayouts(nextLayouts, activeLayout.id);
  };

  const requestLayoutSwitch = (layoutId: string) => {
    if (layoutId === activeLayoutId) return;
    if (hasUnsavedChanges) {
      setPendingSwitchLayoutId(layoutId);
      setPendingCreateLayout(false);
      setIsSwitchLayoutDialogOpen(true);
      return;
    }
    switchLayout(layoutId);
  };

  const cancelLayoutSwitchDialog = () => {
    setIsSwitchLayoutDialogOpen(false);
    setPendingSwitchLayoutId(null);
    setPendingCreateLayout(false);
  };

  const confirmLayoutSwitchSave = () => {
    const baseLayoutName = activeLayout?.name ?? defaultLayoutName;
    const nextLayouts = saveCurrentLayout(activeLayoutId, baseLayoutName, false, viewportLayouts, viewportHolders);
    if (pendingSwitchLayoutId) {
      switchLayout(pendingSwitchLayoutId, nextLayouts);
    } else if (pendingCreateLayout) {
      setLayoutNameDialogMode("create");
      setPendingLayoutName(`${sectionLabel} Layout ${savedLayouts.length + 1}`);
      setLayoutNameError(null);
      setIsNewLayoutDialogOpen(true);
    }
    cancelLayoutSwitchDialog();
  };

  const confirmLayoutSwitchLose = () => {
    if (pendingSwitchLayoutId) {
      switchLayout(pendingSwitchLayoutId);
    } else if (pendingCreateLayout) {
      if (activeLayout) {
        applyLayout(activeLayout);
      }
      setLayoutNameDialogMode("create");
      setPendingLayoutName(`${sectionLabel} Layout ${savedLayouts.length + 1}`);
      setLayoutNameError(null);
      setIsNewLayoutDialogOpen(true);
    }
    cancelLayoutSwitchDialog();
  };

  const requestExitEditing = () => {
    if (hasParkedTilesAcrossViewports) {
      setIsExitBlockedDialogOpen(true);
      setIsExitActionsMenuOpen(false);
      return;
    }
    if (!hasUnsavedChanges) {
      if (activeLayout && !activeLayout.isPrimary) {
        setPendingSetActiveLayoutId(activeLayout.id);
        setIsSetActiveDialogOpen(true);
        return;
      }
      setIsEditing(false);
      return;
    }
    setIsExitActionsMenuOpen((previous) => !previous);
  };

  const confirmExitEditSave = () => {
    if (hasParkedTilesAcrossViewports) {
      setIsExitBlockedDialogOpen(true);
      setIsExitActionsMenuOpen(false);
      return;
    }
    const layout = savedLayouts.find((item) => item.id === activeLayoutId);
    const wasActive = Boolean(layout?.isPrimary);
    saveCurrentLayout(activeLayoutId, layout?.name ?? defaultLayoutName, false);
    setIsExitActionsMenuOpen(false);
    if (!wasActive) {
      setPendingSetActiveLayoutId(activeLayoutId);
      setIsSetActiveDialogOpen(true);
      return;
    }
    if (activeMarkedLayout && activeMarkedLayout.id !== activeLayoutId) {
      switchLayout(activeMarkedLayout.id);
    }
    setIsEditing(false);
  };

  const confirmExitEditDiscard = () => {
    if (hasParkedTilesAcrossViewports) {
      setIsExitBlockedDialogOpen(true);
      setIsExitActionsMenuOpen(false);
      return;
    }
    if (activeLayout) {
      applyLayout(activeLayout);
    }
    if (activeLayout && !activeLayout.isPrimary) {
      setPendingSetActiveLayoutId(activeLayout.id);
      setIsSetActiveDialogOpen(true);
      setIsExitActionsMenuOpen(false);
      return;
    }
    setIsEditing(false);
    setIsExitActionsMenuOpen(false);
  };

  const confirmMakeLayoutActive = () => {
    if (pendingSetActiveLayoutId) {
      setPrimaryLayout(pendingSetActiveLayoutId);
      switchLayout(pendingSetActiveLayoutId);
    }
    setPendingSetActiveLayoutId(null);
    setIsSetActiveDialogOpen(false);
    setIsEditing(false);
  };

  const confirmKeepCurrentActive = () => {
    const keepId = activeMarkedLayout?.id ?? activeLayoutId;
    if (keepId !== activeLayoutId) {
      switchLayout(keepId);
    }
    setPendingSetActiveLayoutId(null);
    setIsSetActiveDialogOpen(false);
    setIsEditing(false);
  };

  const deleteActiveLayout = () => {
    if (!activeLayout) return;
    if (activeLayout.isPrimary) return;
    if (savedLayouts.length <= 1) return;

    const remaining = savedLayouts.filter((layout) => layout.id !== activeLayout.id);
    if (remaining.length === 0) return;

    const nextLayouts = normalizePrimary(remaining);
    const nextActive = nextLayouts[0];
    setSavedLayouts(nextLayouts);
    setActiveLayoutId(nextActive.id);
    applyLayout(nextActive);
    persistLayouts(nextLayouts, nextActive.id);
  };

  const startNavigationEdit = (target: "assetTypes" | "accounts") => {
    setNavEditMode(true);
    setButtonEditTarget(target);
    setDraftNavSectionOrder([...sectionOrderForRender]);
    setDraftNavDashboardTileOrder([...dashboardTileOrderForRender]);
    setDraftNavAssetItemOrder([...assetOrderForRender]);
    setDraftNavAccountItemOrder([...accountOrderForRender]);
  };

  const startSectionNavigationEdit = () => {
    setNavEditMode(true);
    setButtonEditTarget(null);
    setDraftNavSectionOrder([...sectionOrderForRender]);
    setDraftNavDashboardTileOrder([...dashboardTileOrderForRender]);
    setDraftNavAssetItemOrder([...assetOrderForRender]);
    setDraftNavAccountItemOrder([...accountOrderForRender]);
  };
  const saveNavigationEdit = () => {
    const assetKeys = assetTypeEntries.map((entry) => entry.key);
    const accountKeys = accountEntries.map((entry) => entry.key);
    const nextSectionOrder = normalizeOrder(draftNavSectionOrder, DEFAULT_NAV_SECTION_ORDER) as NavSectionKey[];
    const nextDashboardTileOrder = normalizeOrder(draftNavDashboardTileOrder, DEFAULT_NAV_DASHBOARD_TILE_ORDER) as NavDashboardTileKey[];
    const nextAssetOrder = normalizeOrder(draftNavAssetItemOrder, assetKeys);
    const nextAccountOrder = normalizeOrder(draftNavAccountItemOrder, accountKeys);
    setNavSectionOrder(nextSectionOrder);
    setNavDashboardTileOrder(nextDashboardTileOrder);
    setNavAssetItemOrder(nextAssetOrder);
    setNavAccountItemOrder(nextAccountOrder);
    setNavEditMode(false);
    setButtonEditTarget(null);
    setNavDragItem(null);
    setNavDropTarget(null);
    setNavTileDragKey(null);
    setNavTileDropKey(null);
  };
  const cancelNavigationEdit = () => {
    setNavEditMode(false);
    setButtonEditTarget(null);
    setNavDragItem(null);
    setNavDropTarget(null);
    setNavTileDragKey(null);
    setNavTileDropKey(null);
    setAccountsActionsMenuOpen(false);
    setAccountsActionsSubmenu(null);
  };

  const reorderDraftByDrag = (kind: NavDragKind, sourceKey: string, targetKey: string) => {
    if (sourceKey === targetKey) return;
    if (kind === "section") {
      if (!navEditMode) {
        setNavSectionOrder((previous) => moveKeyForDrag(previous, sourceKey, targetKey) as NavSectionKey[]);
        return;
      }
      setDraftNavSectionOrder((previous) => moveKeyForDrag(previous, sourceKey, targetKey) as NavSectionKey[]);
      return;
    }
    if (kind === "asset") {
      const assetKeys = assetTypeEntries.map((entry) => entry.key);
      setDraftNavAssetItemOrder((previous) => {
        const base = normalizeOrder(previous, assetKeys);
        return moveKeyForDrag(base, sourceKey, targetKey);
      });
      return;
    }
    const accountKeys = accountEntries.map((entry) => entry.key);
    setDraftNavAccountItemOrder((previous) => {
      const base = normalizeOrder(previous, accountKeys);
      return moveKeyForDrag(base, sourceKey, targetKey);
    });
  };

  const handleNavDragStart = (event: DragEvent<HTMLButtonElement>, kind: NavDragKind, key: string) => {
    if (!canDragKind(kind)) return;
    const dragSource = event.currentTarget.closest("[data-nav-draggable]") as HTMLElement | null;
    const dragItem: NavDragItem = { kind, key };
    navDragItemRef.current = dragItem;
    navHoverTargetRef.current = null;
    navDropTargetRef.current = null;
    navSectionSlotRef.current = [];
    navAssetSlotRef.current = [];
    navAccountSlotRef.current = [];
    if (navEditPanelRef.current) {
      const selector = `[data-nav-target-kind="${kind}"][data-nav-target-key]`;
      const nodes = Array.from(navEditPanelRef.current.querySelectorAll<HTMLElement>(selector));
      const slots = nodes
        .map((node) => {
          const targetKey = node.dataset.navTargetKey?.trim();
          if (!targetKey) return null;
          const rect = node.getBoundingClientRect();
          return { key: targetKey, top: rect.top, bottom: rect.bottom };
        })
        .filter((item): item is { key: string; top: number; bottom: number } => Boolean(item))
        .sort((a, b) => a.top - b.top);
      if (kind === "section") navSectionSlotRef.current = slots;
      if (kind === "asset") navAssetSlotRef.current = slots;
      if (kind === "account") navAccountSlotRef.current = slots;
    }
    setNavDragItem(dragItem);
    setNavDropTarget(null);
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", `${kind}:${key}`);
    if (dragSource) {
      cleanupNavButtonDragMirror();
      const rect = dragSource.getBoundingClientRect();
      const offsetX = clamp(Math.round(event.clientX - rect.left), 0, Math.round(rect.width));
      const offsetY = clamp(Math.round(event.clientY - rect.top), 0, Math.round(rect.height));
      const dragClone = dragSource.cloneNode(true) as HTMLElement;
      dragClone.style.position = "fixed";
      dragClone.style.top = "0px";
      dragClone.style.left = "0px";
      dragClone.style.width = `${rect.width}px`;
      dragClone.style.height = `${rect.height}px`;
      dragClone.style.margin = "0";
      dragClone.style.pointerEvents = "none";
      dragClone.style.opacity = "1";
      dragClone.style.zIndex = "9999";
      dragClone.style.transform = `translate(${rect.left}px, ${rect.top}px)`;
      dragClone.style.boxShadow = "0 14px 32px rgba(15,23,42,0.28)";
      const appRoot = document.querySelector(".app-home");
      if (appRoot) {
        appRoot.appendChild(dragClone);
      } else {
        document.body.appendChild(dragClone);
      }
      navButtonDragOffsetRef.current = { x: offsetX, y: offsetY };
      navButtonDragImageRef.current = dragClone;
      event.dataTransfer.setDragImage(transparentDragImageRef.current ?? dragClone, 0, 0);
    }
  };

  const readNavDragItem = (event?: DragEvent<HTMLElement>): NavDragItem | null => {
    if (navDragItemRef.current) return navDragItemRef.current;
    if (navDragItem) return navDragItem;
    if (!event) return null;
    const raw = event.dataTransfer.getData("text/plain");
    if (!raw) return null;
    const separatorIndex = raw.indexOf(":");
    if (separatorIndex < 0) return null;
    const kindRaw = raw.slice(0, separatorIndex);
    const key = raw.slice(separatorIndex + 1);
    if (!kindRaw || !key) return null;
    if (kindRaw !== "section" && kindRaw !== "asset" && kindRaw !== "account") return null;
    return { kind: kindRaw, key };
  };

  const handleNavDragEnd = () => {
    const currentDrag = navDragItemRef.current;
    const pendingTarget = navDropTargetRef.current;
    if (
      currentDrag
      && pendingTarget
      && currentDrag.kind === pendingTarget.kind
      && currentDrag.key !== pendingTarget.key
    ) {
      reorderDraftByDrag(currentDrag.kind, currentDrag.key, pendingTarget.key);
    }
    navDragItemRef.current = null;
    navHoverTargetRef.current = null;
    navDropTargetRef.current = null;
    navSectionSlotRef.current = [];
    navAssetSlotRef.current = [];
    navAccountSlotRef.current = [];
    setNavDragItem(null);
    setNavDropTarget(null);
    cleanupNavButtonDragMirror();
  };

  const handleNavTargetDragOver = (event: DragEvent<HTMLElement>, kind: NavDragKind, key: string) => {
    if (!canDragKind(kind)) return;
    const currentDrag = readNavDragItem(event);
    if (!currentDrag || currentDrag.kind !== kind) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
    let targetKey = key;
    const slotMap =
      kind === "section"
        ? navSectionSlotRef.current
        : kind === "asset"
          ? navAssetSlotRef.current
          : navAccountSlotRef.current;
    if (slotMap.length > 0) {
      const y = event.clientY;
      const slot = slotMap.find((item) => y >= item.top && y <= item.bottom);
      if (slot) {
        targetKey = slot.key;
      } else {
        const nearest = slotMap.reduce((closest, item) => {
          const mid = (item.top + item.bottom) / 2;
          const distance = Math.abs(y - mid);
          if (!closest || distance < closest.distance) {
            return { key: item.key, distance };
          }
          return closest;
        }, null as { key: string; distance: number } | null);
        if (nearest) targetKey = nearest.key;
      }
    }
    navHoverTargetRef.current = { kind, key: targetKey };
    if (!navDropTargetRef.current || navDropTargetRef.current.kind !== kind || navDropTargetRef.current.key !== targetKey) {
      navDropTargetRef.current = { kind, key: targetKey };
      setNavDropTarget({ kind, key: targetKey });
    }
  };

  const handleNavTargetDrop = (event: DragEvent<HTMLElement>, kind: NavDragKind, key: string) => {
    if (!canDragKind(kind)) return;
    event.preventDefault();
    const currentDrag = readNavDragItem(event);
    if (!currentDrag || currentDrag.kind !== kind) {
      navDragItemRef.current = null;
      navHoverTargetRef.current = null;
      navDropTargetRef.current = null;
      navSectionSlotRef.current = [];
      navAssetSlotRef.current = [];
      navAccountSlotRef.current = [];
      setNavDragItem(null);
      setNavDropTarget(null);
      cleanupNavButtonDragMirror();
      return;
    }
    const targetKey = navDropTargetRef.current?.kind === kind ? navDropTargetRef.current.key : key;
    navHoverTargetRef.current = { kind, key: targetKey };
    if (targetKey !== currentDrag.key) {
      reorderDraftByDrag(kind, currentDrag.key, targetKey);
    }
    navDragItemRef.current = null;
    navHoverTargetRef.current = null;
    navDropTargetRef.current = null;
    navSectionSlotRef.current = [];
    navAssetSlotRef.current = [];
    navAccountSlotRef.current = [];
    setNavDragItem(null);
    setNavDropTarget(null);
    cleanupNavButtonDragMirror();
  };

  const handleNavContainerDragOver = (event: DragEvent<HTMLElement>) => {
    const currentDrag = readNavDragItem(event);
    if (!currentDrag || !canDragKind(currentDrag.kind)) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  };

  const handleNavContainerDrop = (event: DragEvent<HTMLElement>) => {
    event.preventDefault();
    const currentDrag = readNavDragItem(event);
    if (!currentDrag || !canDragKind(currentDrag.kind)) {
      navDragItemRef.current = null;
      navHoverTargetRef.current = null;
      navDropTargetRef.current = null;
      navSectionSlotRef.current = [];
      navAssetSlotRef.current = [];
      navAccountSlotRef.current = [];
      setNavDragItem(null);
      setNavDropTarget(null);
      cleanupNavButtonDragMirror();
      return;
    }
    const targetKey = navDropTargetRef.current?.kind === currentDrag.kind ? navDropTargetRef.current.key : null;
    if (targetKey) {
      navHoverTargetRef.current = { kind: currentDrag.kind, key: targetKey };
    }
    if (targetKey && targetKey !== currentDrag.key) {
      reorderDraftByDrag(currentDrag.kind, currentDrag.key, targetKey);
    }
    navDragItemRef.current = null;
    navHoverTargetRef.current = null;
    navDropTargetRef.current = null;
    navSectionSlotRef.current = [];
    navAssetSlotRef.current = [];
    navAccountSlotRef.current = [];
    setNavDragItem(null);
    setNavDropTarget(null);
    cleanupNavButtonDragMirror();
  };

  useEffect(() => {
    if (!navDragItem || !canDragKind(navDragItem.kind)) return;
    const listenerOptions: AddEventListenerOptions = { capture: true };
    const onWindowDragEnter = (event: Event) => {
      event.preventDefault();
      const dragEvent = event as globalThis.DragEvent;
      if (dragEvent.dataTransfer) {
        dragEvent.dataTransfer.dropEffect = "move";
      }
    };
    const onWindowDragOver = (event: Event) => {
      event.preventDefault();
      const dragEvent = event as globalThis.DragEvent;
      const panel = navEditPanelRef.current;
      if (panel) {
        const rect = panel.getBoundingClientRect();
        const inside =
          dragEvent.clientX >= rect.left
          && dragEvent.clientX <= rect.right
          && dragEvent.clientY >= rect.top
          && dragEvent.clientY <= rect.bottom;
        if (!inside) {
          navHoverTargetRef.current = null;
          navDropTargetRef.current = null;
          navSectionSlotRef.current = [];
          navAssetSlotRef.current = [];
          navAccountSlotRef.current = [];
          setNavDropTarget(null);
        }
      }
      if (dragEvent.dataTransfer) {
        dragEvent.dataTransfer.dropEffect = "move";
      }
    };
    const onWindowDrop = (event: Event) => {
      event.preventDefault();
    };
    window.addEventListener("dragenter", onWindowDragEnter, listenerOptions);
    window.addEventListener("dragover", onWindowDragOver, listenerOptions);
    window.addEventListener("drop", onWindowDrop, listenerOptions);
    return () => {
      window.removeEventListener("dragenter", onWindowDragEnter, listenerOptions);
      window.removeEventListener("dragover", onWindowDragOver, listenerOptions);
      window.removeEventListener("drop", onWindowDrop, listenerOptions);
    };
  }, [navDragItem, navEditMode, buttonEditTarget]);

  useEffect(() => {
    if (transparentDragImageRef.current) return;
    const img = new Image();
    img.src = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==";
    transparentDragImageRef.current = img;
  }, []);

  useEffect(() => {
    if (!navDragItem) return;
    const previousCursor = document.body.style.cursor;
    document.body.style.cursor = "grabbing";
    return () => {
      document.body.style.cursor = previousCursor;
    };
  }, [navDragItem]);

  const cleanupDashboardTileDragMirror = useCallback(() => {
    if (navTileDragImageRef.current?.parentElement) {
      navTileDragImageRef.current.parentElement.removeChild(navTileDragImageRef.current);
    }
    navTileDragImageRef.current = null;
  }, []);

  const cleanupNavButtonDragMirror = useCallback(() => {
    if (navButtonDragImageRef.current?.parentElement) {
      navButtonDragImageRef.current.parentElement.removeChild(navButtonDragImageRef.current);
    }
    navButtonDragImageRef.current = null;
  }, []);

  useEffect(() => {
    if (!navTileDragKey || !navTileDragImageRef.current) return;
    const onWindowDragOver = (event: globalThis.DragEvent) => {
      const mirror = navTileDragImageRef.current;
      if (!mirror) return;
      const x = event.clientX - navTileDragOffsetRef.current.x;
      const y = event.clientY - navTileDragOffsetRef.current.y;
      mirror.style.transform = `translate(${x}px, ${y}px)`;
    };
    window.addEventListener("dragover", onWindowDragOver);
    return () => window.removeEventListener("dragover", onWindowDragOver);
  }, [navTileDragKey]);

  useEffect(() => {
    if (!navDragItem || !navButtonDragImageRef.current) return;
    const onWindowDragOver = (event: globalThis.DragEvent) => {
      const mirror = navButtonDragImageRef.current;
      if (!mirror) return;
      const x = event.clientX - navButtonDragOffsetRef.current.x;
      const y = event.clientY - navButtonDragOffsetRef.current.y;
      mirror.style.transform = `translate(${x}px, ${y}px)`;
    };
    window.addEventListener("dragover", onWindowDragOver);
    return () => window.removeEventListener("dragover", onWindowDragOver);
  }, [navDragItem]);

  useEffect(() => {
    if (dashboardTilesEditMode) return;
    cleanupDashboardTileDragMirror();
    cleanupNavButtonDragMirror();
  }, [cleanupDashboardTileDragMirror, cleanupNavButtonDragMirror, dashboardTilesEditMode]);

  useEffect(() => {
    const onWindowDrop = () => {
      cleanupDashboardTileDragMirror();
      cleanupNavButtonDragMirror();
    };
    const onWindowDragEnd = () => {
      cleanupDashboardTileDragMirror();
      cleanupNavButtonDragMirror();
    };
    window.addEventListener("drop", onWindowDrop);
    window.addEventListener("dragend", onWindowDragEnd);
    return () => {
      window.removeEventListener("drop", onWindowDrop);
      window.removeEventListener("dragend", onWindowDragEnd);
    };
  }, [cleanupDashboardTileDragMirror, cleanupNavButtonDragMirror]);

  const loadSidebarData = useCallback(async () => {
    const fetchAll = async () =>
      Promise.allSettled([getAssetTypes(), getAccountsList(), getAccountCreateOptions()]);

    let [assetTypeResult, accountListResult, createOptionsResult] = await fetchAll();
    const shouldRetry =
      assetTypeResult.status === "rejected"
      || accountListResult.status === "rejected"
      || createOptionsResult.status === "rejected";

    if (shouldRetry) {
      await new Promise((resolve) => window.setTimeout(resolve, 350));
      [assetTypeResult, accountListResult, createOptionsResult] = await fetchAll();
    }

    if (assetTypeResult.status === "fulfilled") {
      setAssetTypes(assetTypeResult.value);
    }

    if (accountListResult.status === "fulfilled") {
      setAccountRows(accountListResult.value);
    }

    if (createOptionsResult.status === "fulfilled") {
      setAccountCreateOptions(createOptionsResult.value);
    }
  }, []);

  const closeAddAssetsModal = useCallback(() => {
    setIsAddAssetModalOpen(false);
    setAddAssetStep("type");
    setSelectedAddAssetType(null);
    setSelectedAddAssetAccountId(null);
    setIsAddAccountInlineOpen(false);
    setEquitySearchQuery("");
    setEquitySearchResults([]);
    setIsEquitySearchLoading(false);
    setSelectedEquityResult(null);
    setNewHoldingQuantity("");
    setNewHoldingAverageCost("");
    setAddAssetFlowError(null);
    setIsSubmittingHolding(false);
    setNewAccountName("");
    setNewAccountBroker("");
    setNewAccountPortfolioId(accountCreateOptions?.portfolios[0]?.id ?? null);
    setNewAccountTypeId(null);
    setNewAccountClassificationId(accountCreateOptions?.classification_definitions[0]?.id ?? null);
    setIsCreatingAccount(false);
    setIsAddAssetTypeViewOpen(false);
    setNewAssetTypeName("");
    setNewAssetTypeError(null);
    setIsCreatingAssetType(false);
  }, [accountCreateOptions?.classification_definitions, accountCreateOptions?.portfolios]);

  const beginAddAssetFlow = useCallback((assetType: AssetTypeOption) => {
    setSelectedAddAssetType(assetType);
    setAddAssetFlowError(null);
    setSelectedAddAssetAccountId(null);
    setIsAddAccountInlineOpen(false);
    setSelectedEquityResult(null);
    setEquitySearchQuery("");
    setEquitySearchResults([]);
    setNewHoldingQuantity("");
    setNewHoldingAverageCost("");
    setAddAssetStep(assetType.slug === "equity" ? "account" : "type");
  }, []);

  const handleCreateAssetType = useCallback(async () => {
    const trimmedName = newAssetTypeName.trim();
    if (!trimmedName) {
      setNewAssetTypeError("Enter an asset type name.");
      return;
    }

    try {
      setIsCreatingAssetType(true);
      setNewAssetTypeError(null);
      await createCustomAssetType({ name: trimmedName });
      await loadSidebarData();
      setNewAssetTypeName("");
      setIsAddAssetTypeViewOpen(false);
    } catch (error) {
      setNewAssetTypeError(error instanceof Error ? error.message : "Unable to create asset type.");
    } finally {
      setIsCreatingAssetType(false);
    }
  }, [loadSidebarData, newAssetTypeName]);

  const handleCreateEligibleAccount = useCallback(async () => {
    if (
      !newAccountName.trim()
      || newAccountPortfolioId === null
      || newAccountTypeId === null
      || newAccountClassificationId === null
    ) {
      setAddAssetFlowError("Complete the account details first.");
      return;
    }

    try {
      setIsCreatingAccount(true);
      setAddAssetFlowError(null);
      const created = await createAccount({
        portfolio_id: newAccountPortfolioId,
        name: newAccountName.trim(),
        account_type_id: newAccountTypeId,
        broker: newAccountBroker.trim() || undefined,
        classification_definition_id: newAccountClassificationId,
      });
      await loadSidebarData();
      setSelectedAddAssetAccountId(created.id);
      setAddAssetStep("asset");
    } catch (error) {
      if (error instanceof ApiError) {
        setAddAssetFlowError(error.message);
      } else {
        setAddAssetFlowError("Unable to create account.");
      }
    } finally {
      setIsCreatingAccount(false);
    }
  }, [loadSidebarData, newAccountBroker, newAccountClassificationId, newAccountName, newAccountPortfolioId, newAccountTypeId]);

  const handleSubmitEquityHolding = useCallback(async () => {
    if (!selectedAddAssetAccountId || !selectedEquityResult || !newHoldingQuantity.trim()) {
      setAddAssetFlowError("Select an equity and enter a quantity.");
      return;
    }

    try {
      setIsSubmittingHolding(true);
      setAddAssetFlowError(null);
      await createAccountHolding(selectedAddAssetAccountId, {
        asset_id: selectedEquityResult.asset_id,
        quantity: newHoldingQuantity.trim(),
        average_purchase_price: newHoldingAverageCost.trim() || undefined,
      });
      await loadSidebarData();
      closeAddAssetsModal();
      setActiveAppShellSection("portfolio");
      setActiveSidebarCategory("portfolio");
      setActiveSidebarLabel("Portfolio");
    } catch (error) {
      if (error instanceof ApiError) {
        setAddAssetFlowError(error.message);
      } else {
        setAddAssetFlowError("Unable to add holding.");
      }
    } finally {
      setIsSubmittingHolding(false);
    }
  }, [
    closeAddAssetsModal,
    loadSidebarData,
    newHoldingAverageCost,
    newHoldingQuantity,
    selectedAddAssetAccountId,
    selectedEquityResult,
  ]);

  useEffect(() => {
    const onDocClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement | null;
      if (!target) return;
      const inDashboardMenu = Boolean(target.closest("[data-dashboard-menu]"));
      const inHolderMenu = Boolean(target.closest("[data-holder-menu]"));
      const inAccountActionsMenu = Boolean(target.closest("[data-account-actions-menu]"));
      const inFavoritesActionsMenu = Boolean(target.closest("[data-favorites-actions-menu]"));
      const inAssetsActionsMenu = Boolean(target.closest("[data-assets-actions-menu]"));
      const inCustomActionsMenu = Boolean(target.closest("[data-custom-actions-menu]"));
      const inDashboardTilesMenu = Boolean(target.closest("[data-dashboard-tiles-menu]"));
      const inGridAddMenu = Boolean(target.closest("[data-grid-add-menu]"));
      const inExitActionsMenu = Boolean(target.closest("[data-exit-actions-menu]"));

      if (!inDashboardMenu) setSettingsMenuOpen(false);
      if (!inDashboardMenu) setLayoutActionsMenuOpen(false);
      if (!inHolderMenu) setHolderMenuOpenId(null);

      if (!inAccountActionsMenu) {
        setAccountsActionsMenuOpen(false);
        setAccountsActionsSubmenu(null);
      }
      if (!inFavoritesActionsMenu) {
        setFavoritesActionsMenuOpen(false);
        setFavoritesActionsSubmenu(null);
      }
      if (!inAssetsActionsMenu) {
        setAssetsActionsMenuOpen(false);
        setAssetsActionsSubmenu(null);
      }
      if (!inCustomActionsMenu) {
        setCustomActionsMenuOpen(false);
        setCustomActionsSubmenu(null);
      }
      if (!inDashboardTilesMenu) {
        setDashboardTilesMenuOpen(false);
        setDashboardTilesConfirmOpen(false);
        setDashboardTilesCancelOpen(false);
      }
      if (!inGridAddMenu) setIsGridOptionsMenuOpen(false);
      if (!inExitActionsMenu) setIsExitActionsMenuOpen(false);
    };

    window.addEventListener("mousedown", onDocClick);
    return () => window.removeEventListener("mousedown", onDocClick);
  }, []);

  useEffect(() => {
    if (isEditing) return;
    if (!activeMarkedLayout) return;
    if (activeLayoutId === activeMarkedLayout.id) return;
    switchLayout(activeMarkedLayout.id);
  }, [activeLayoutId, activeMarkedLayout, isEditing]);

  useEffect(() => {
    void loadSidebarData();
  }, [loadSidebarData, user?.email]);

  useEffect(() => {
    let isCancelled = false;

    const loadPortfolioHoldings = async () => {
      if (accountRows.length === 0) {
        setPortfolioHoldings([]);
        setPortfolioHoldingsNotice(null);
        setIsPortfolioHoldingsLoading(false);
        return;
      }

      setIsPortfolioHoldingsLoading(true);
      setPortfolioHoldingsNotice(null);

      const results = await Promise.allSettled(
        accountRows.map(async (account) => ({
          account,
          holdings: await getAccountHoldings(account.id),
        })),
      );

      if (isCancelled) return;

      const nextRows: PortfolioHoldingRow[] = [];
      let failedCount = 0;

      for (const result of results) {
        if (result.status !== "fulfilled") {
          failedCount += 1;
          continue;
        }
        for (const holding of result.value.holdings) {
          nextRows.push({
            ...holding,
            account_name: result.value.account.name,
          });
        }
      }

      setPortfolioHoldings(nextRows);
      setPortfolioHoldingsNotice(
        failedCount > 0 ? "Some account holdings could not be loaded yet." : null,
      );
      setIsPortfolioHoldingsLoading(false);
    };

    void loadPortfolioHoldings();

    return () => {
      isCancelled = true;
    };
  }, [accountRows]);

  useEffect(() => {
    let isCancelled = false;
    const bootNavigationState = async () => {
      try {
        const payload = await getNavigationState(navigationScope);
        if (isCancelled) return;
        const normalizedSections = normalizeOrder(payload.section_order ?? [], DEFAULT_NAV_SECTION_ORDER) as NavSectionKey[];
        setNavSectionOrder(normalizedSections);
        setNavAssetItemOrder(payload.asset_item_order ?? []);
        setNavAccountItemOrder(payload.account_item_order ?? []);
        setAssetTypesCollapsed(Boolean(payload.asset_types_collapsed));
        setAccountsCollapsed(Boolean(payload.accounts_collapsed));
        const nextActiveKey = (payload.active_item_key ?? "").trim() || "portfolio";
        setActiveSidebarCategory(nextActiveKey);
        setHasHydratedNavState(true);
      } catch {
        if (isCancelled) return;
        setNavSectionOrder(DEFAULT_NAV_SECTION_ORDER);
        setNavAssetItemOrder([]);
        setNavAccountItemOrder([]);
        setAssetTypesCollapsed(false);
        setAccountsCollapsed(false);
        setActiveSidebarCategory("portfolio");
        setHasHydratedNavState(true);
      }
    };
    setHasHydratedNavState(false);
    void bootNavigationState();
    return () => {
      isCancelled = true;
    };
  }, [navigationScope, user?.email]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(navVisibilityStorageKey);
      if (!raw) {
        setHiddenDashboardTileKeys([]);
        setHiddenNavButtonKeys([]);
        return;
      }
      const parsed = JSON.parse(raw) as { hidden_tiles?: string[]; hidden_buttons?: string[] };
      const nextHiddenTiles = Array.from(
        new Set(
          (parsed.hidden_tiles ?? []).filter((key): key is NavDashboardTileKey =>
            DEFAULT_NAV_DASHBOARD_TILE_ORDER.includes(key as NavDashboardTileKey),
          ),
        ),
      );
      const nextHiddenButtons = Array.from(new Set((parsed.hidden_buttons ?? []).filter((key) => typeof key === "string" && key.trim())));
      setHiddenDashboardTileKeys(nextHiddenTiles);
      setHiddenNavButtonKeys(nextHiddenButtons);
    } catch {
      setHiddenDashboardTileKeys([]);
      setHiddenNavButtonKeys([]);
    }
  }, [navVisibilityStorageKey]);

  useEffect(() => {
    localStorage.setItem(
      navVisibilityStorageKey,
      JSON.stringify({
        hidden_tiles: hiddenDashboardTileKeys,
        hidden_buttons: hiddenNavButtonKeys,
      }),
    );
  }, [hiddenDashboardTileKeys, hiddenNavButtonKeys, navVisibilityStorageKey]);

  // Keep nav reorder hooks callable for future UI re-enable.
  useEffect(() => {
    (window as typeof window & { __finproNavReorder?: unknown }).__finproNavReorder = {
      startAssetTypes: () => startNavigationEdit("assetTypes"),
      startAccounts: () => startNavigationEdit("accounts"),
      startSections: startSectionNavigationEdit,
      save: saveNavigationEdit,
      stop: () => {
        setNavEditMode(false);
        setButtonEditTarget(null);
        setNavDragItem(null);
        setNavDropTarget(null);
      },
    };
    return () => {
      delete (window as typeof window & { __finproNavReorder?: unknown }).__finproNavReorder;
    };
  }, [saveNavigationEdit, startNavigationEdit, startSectionNavigationEdit]);

  useEffect(() => {
    const assetKeys = assetTypeEntries.map((entry) => entry.key);
    const accountKeys = accountEntries.map((entry) => entry.key);
    setNavAssetItemOrder((previous) => normalizeOrder(previous, assetKeys));
    setNavAccountItemOrder((previous) => normalizeOrder(previous, accountKeys));
    if (navEditMode) {
      setDraftNavAssetItemOrder((previous) => normalizeOrder(previous, assetKeys));
      setDraftNavAccountItemOrder((previous) => normalizeOrder(previous, accountKeys));
    }
  }, [accountEntries, assetTypeEntries, navEditMode]);

  useEffect(() => {
    const isSortMode = navEditMode && buttonEditTarget === "all";
    if (!isSortMode) {
      document.body.style.overflow = "";
      return;
    }
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [buttonEditTarget, navEditMode]);

  useEffect(() => {
    if (activeSidebarCategory === "portfolio") {
      setActiveSidebarLabel("Portfolio");
      return;
    }
    if (activeSidebarCategory === "assets-liabilities") {
      setActiveSidebarLabel("Assets & Liabilities");
      return;
    }
    if (activeSidebarCategory === "holdings") {
      setActiveSidebarLabel("Holdings");
      return;
    }
    if (activeSidebarCategory === "accounts") {
      setActiveSidebarLabel("Accounts");
      return;
    }
    const assetMatch = assetTypeEntries.find((entry) => entry.key === activeSidebarCategory);
    if (assetMatch) {
      setActiveSidebarLabel(assetMatch.assetType.name);
      return;
    }
    const accountMatch = accountEntries.find((entry) => entry.key === activeSidebarCategory);
    if (accountMatch) {
      setActiveSidebarLabel(accountMatch.account.name);
      return;
    }
    setActiveSidebarCategory("portfolio");
    setActiveSidebarLabel("Portfolio");
  }, [accountEntries, activeSidebarCategory, assetTypeEntries]);

  useEffect(() => {
    const query = new URLSearchParams(location.search);
    if (query.get("action") !== "add-modify") return;
    if (isEditing) return;
    setIsAddAssetModalOpen(true);
  }, [isEditing, location.search]);

  useEffect(() => {
    const handleOpenAddAssetsModal = () => {
      if (isEditing) return;
      setIsAddAssetModalOpen(true);
    };
    window.addEventListener("finpro:open-add-assets-modal", handleOpenAddAssetsModal);
    return () => {
      window.removeEventListener("finpro:open-add-assets-modal", handleOpenAddAssetsModal);
    };
  }, [isEditing]);

  useEffect(() => {
    let isCancelled = false;

    const createFallbackLayout = (): SavedLayout => ({
      id: DEFAULT_LAYOUT_ID,
      name: defaultLayoutName,
      viewportLayouts: createDefaultViewportLayouts(),
      viewportHolders: createDefaultViewportHolders(),
      isPrimary: true,
      updatedAt: new Date().toISOString(),
    });

    const hydrateFromPayload = (
      payload: { activeLayoutId?: string; layouts?: Array<SavedLayout & { tiles?: DashboardTile[]; targetRows?: number }> },
    ): { layouts: SavedLayout[]; activeId: string } => {
      const layoutsRaw = Array.isArray(payload.layouts) && payload.layouts.length > 0 ? payload.layouts : [];
      const layouts = normalizePrimary(
        layoutsRaw.map((layout) => ({
          id: layout.id,
          name: normalizeLayoutName(layout.name || defaultLayoutName),
          viewportLayouts: layout.viewportLayouts
            ? normalizeAllViewportLayouts(layout.viewportLayouts)
            : createViewportLayoutsFromLegacy(layout.tiles ?? DEFAULT_TILES, layout.targetRows ?? BASE_DASHBOARD_ROWS),
          viewportHolders: normalizeViewportHolders(layout.viewportHolders ?? createDefaultViewportHolders()),
          isPrimary: Boolean(layout.isPrimary),
          updatedAt: layout.updatedAt ?? new Date().toISOString(),
        })),
      );
      if (layouts.length === 0) {
        const fallback = createFallbackLayout();
        return { layouts: [fallback], activeId: fallback.id };
      }
      const activeId = payload.activeLayoutId && layouts.some((layout) => layout.id === payload.activeLayoutId)
        ? payload.activeLayoutId
        : layouts[0].id;
      return { layouts, activeId };
    };

    const applyHydrated = (layouts: SavedLayout[], activeId: string) => {
      if (isCancelled) return;
      const activeLayout = layouts.find((layout) => layout.id === activeId) ?? layouts[0];
      setSavedLayouts(layouts);
      setActiveLayoutId(activeId);
      applyLayout(activeLayout);
      persistLayouts(layouts, activeId);
    };

    const boot = async () => {
      try {
        const backendState = await getDashboardLayoutState(dashboardScope);
        const backendPayload = {
          activeLayoutId: backendState.active_layout_id,
          layouts: backendState.layouts as Array<SavedLayout & { tiles?: DashboardTile[]; targetRows?: number }>,
        };
        if (Array.isArray(backendPayload.layouts) && backendPayload.layouts.length > 0) {
          const hydrated = hydrateFromPayload(backendPayload);
          applyHydrated(hydrated.layouts, hydrated.activeId);
          return;
        }

        const raw = localStorage.getItem(legacyStorageKey);
        if (raw) {
          const parsed = JSON.parse(raw) as { activeLayoutId?: string; layouts?: Array<SavedLayout & { tiles?: DashboardTile[]; targetRows?: number }> };
          const hydrated = hydrateFromPayload(parsed);
          applyHydrated(hydrated.layouts, hydrated.activeId);
          return;
        }

        const fallback = createFallbackLayout();
        applyHydrated([fallback], fallback.id);
      } catch {
        try {
          const raw = localStorage.getItem(legacyStorageKey);
          if (raw) {
            const parsed = JSON.parse(raw) as { activeLayoutId?: string; layouts?: Array<SavedLayout & { tiles?: DashboardTile[]; targetRows?: number }> };
            const hydrated = hydrateFromPayload(parsed);
            applyHydrated(hydrated.layouts, hydrated.activeId);
            return;
          }
        } catch {
          // Ignore local parsing errors and fall back to defaults below.
        }

        const fallback = createFallbackLayout();
        applyHydrated([fallback], fallback.id);
      }
    };

    void boot();
    return () => {
      isCancelled = true;
    };
  }, [dashboardScope, defaultLayoutName, legacyStorageKey]);

  useEffect(() => {
    if (!hasHydratedNavState) return;
    if (navEditMode) return;
    void upsertNavigationState({
      scope: navigationScope,
      section_order: navSectionOrder,
      asset_item_order: navAssetItemOrder,
      account_item_order: navAccountItemOrder,
      asset_types_collapsed: assetTypesCollapsed,
      accounts_collapsed: accountsCollapsed,
      active_item_key: activeSidebarCategory,
    }).catch(() => {
      // Keep UI responsive if persistence fails.
    });
  }, [
    hasHydratedNavState,
    navEditMode,
    navigationScope,
    navSectionOrder,
    navAssetItemOrder,
    navAccountItemOrder,
    assetTypesCollapsed,
    accountsCollapsed,
    activeSidebarCategory,
  ]);

  useEffect(() => {
    if (isEditing) return;
    setActiveDropSlot(null);
    setDraggingTileId(null);
    setDragSession(null);
    setDragPreview(null);
    setResizeSession(null);
    setResizePreview(null);
    setResizeVisual(null);
    setHolderMenuOpenId(null);
    setIsOverHolderDrop(false);
    setIsAddTileDialogOpen(false);
    setIsNewLayoutDialogOpen(false);
    setIsSwitchLayoutDialogOpen(false);
    setIsExitActionsMenuOpen(false);
    setIsExitBlockedDialogOpen(false);
    setIsGridOptionsMenuOpen(false);
    setPendingSwitchLayoutId(null);
    setIsManageGridMode(false);
    setIsDeleteStructureMode(false);
    setSelectedDeleteRows([]);
    setSelectedDeleteCols([]);
    setHoveredDeleteRow(null);
    setHoveredDeleteCol(null);
    
  }, [isEditing]);

  useEffect(() => {
    if (!isEditing) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isEditing]);

  useEffect(() => {
    if (!isAddAssetModalOpen || isEditing) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isAddAssetModalOpen, isEditing]);

  useEffect(() => {
    if (!isAddAssetModalOpen) return;
    if (newAccountPortfolioId === null) {
      setNewAccountPortfolioId(accountCreateOptions?.portfolios[0]?.id ?? null);
    }
    if (newAccountClassificationId === null) {
      setNewAccountClassificationId(accountCreateOptions?.classification_definitions[0]?.id ?? null);
    }
  }, [accountCreateOptions?.classification_definitions, accountCreateOptions?.portfolios, isAddAssetModalOpen, newAccountClassificationId, newAccountPortfolioId]);

  useEffect(() => {
    if (!isAddAssetModalOpen || addAssetStep !== "account") return;
    if (eligibleAccountTypesForSelectedAsset.length === 0) {
      setNewAccountTypeId(null);
      return;
    }
    const fallbackAccountTypeId = brokerageAccountType?.id ?? eligibleAccountTypesForSelectedAsset[0]?.id ?? null;
    if (newAccountTypeId === null || !eligibleAccountTypeIds.has(newAccountTypeId)) {
      setNewAccountTypeId(fallbackAccountTypeId);
    }
  }, [addAssetStep, brokerageAccountType?.id, eligibleAccountTypeIds, eligibleAccountTypesForSelectedAsset, isAddAssetModalOpen, newAccountTypeId]);

  useEffect(() => {
    if (!isAddAssetModalOpen || addAssetStep !== "asset" || selectedAddAssetSlug !== "equity") return;
    const query = equitySearchQuery.trim();
    if (query.length < 1) {
      setEquitySearchResults([]);
      setIsEquitySearchLoading(false);
      return;
    }

    let isCancelled = false;
    setIsEquitySearchLoading(true);
    const timeoutId = window.setTimeout(async () => {
      try {
        const results = await lookupEquities(query);
        if (isCancelled) return;
        setEquitySearchResults(results);
      } catch {
        if (isCancelled) return;
        setEquitySearchResults([]);
      } finally {
        if (!isCancelled) setIsEquitySearchLoading(false);
      }
    }, 220);

    return () => {
      isCancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [addAssetStep, equitySearchQuery, isAddAssetModalOpen, selectedAddAssetSlug]);

  useEffect(() => {
    const root = document.documentElement;
    root.dataset.dashboardTilesEditMode = dashboardTilesEditMode ? "true" : "false";

    return () => {
      delete root.dataset.dashboardTilesEditMode;
    };
  }, [dashboardTilesEditMode]);

  useEffect(() => {
    const onResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    setSelectedDeleteRows([]);
    setSelectedDeleteCols([]);
    setHoveredDeleteRow(null);
    setHoveredDeleteCol(null);
    
    setHolderMenuOpenId(null);
    setIsGridOptionsMenuOpen(false);
  }, [activeViewport]);

  useEffect(() => {
    if (isDeleteStructureMode) return;
    setHoveredDeleteRow(null);
    setHoveredDeleteCol(null);
  }, [isDeleteStructureMode]);

  useEffect(() => {
    if (!isEditing) return;
    setIsDeleteStructureMode(true);
  }, [isEditing]);

  useEffect(() => {
    const updateMetrics = () => {
      const grid = gridRef.current;
      if (!grid) return;
      const styles = window.getComputedStyle(grid);
      const templateCols = styles.gridTemplateColumns
        .split(" ")
        .map((part) => part.trim())
        .filter(Boolean);
      const colCount = templateCols.length > 0 ? templateCols.length : DESKTOP_COLUMNS;
      const colGap = Number.parseFloat(styles.columnGap || "0");
      const rowGap = Number.parseFloat(styles.rowGap || "0");
      const rowSize = Number.parseFloat(styles.gridAutoRows || "132");
      const cellWidth = (grid.clientWidth - colGap * (colCount - 1)) / colCount;

      setGridMetrics({
        columns: colCount,
        cellWidth: Number.isFinite(cellWidth) ? cellWidth : 132,
        cellHeight: Number.isFinite(rowSize) ? rowSize : 132,
        colGap: Number.isFinite(colGap) ? colGap : 0,
        rowGap: Number.isFinite(rowGap) ? rowGap : 0,
      });
    };

    updateMetrics();
    const frameId = window.requestAnimationFrame(updateMetrics);
    const resizeObserver = new ResizeObserver(() => updateMetrics());
    if (gridRef.current) {
      resizeObserver.observe(gridRef.current);
    }
    window.addEventListener("resize", updateMetrics);
    return () => {
      window.cancelAnimationFrame(frameId);
      resizeObserver.disconnect();
      window.removeEventListener("resize", updateMetrics);
    };
  }, [isEditing, editingViewport, activeViewport, columns]);

  const addTile = (preset: TilePreset = TILE_PRESETS[0]) => {
    const newTileId = nextTileId;
    setViewportLayouts((previous) => {
      const next: ViewportLayouts = {
        mobile: { ...previous.mobile, tiles: [...previous.mobile.tiles] },
        tablet: { ...previous.tablet, tiles: [...previous.tablet.tiles] },
        desktop: { ...previous.desktop, tiles: [...previous.desktop.tiles] },
      };

      (["mobile", "tablet", "desktop"] as EditViewport[]).forEach((viewport) => {
        const viewportColumns = previous[viewport].targetColumns;
        const presetSpan = preset.spans[viewport];
        const colSpan = clamp(presetSpan.colSpan, 1, viewportColumns);
        const rowSpan = clamp(presetSpan.rowSpan, 1, MAX_ROW_SPAN);
        let nextSlot = 0;
        while (!canPlaceTile(next[viewport].tiles, null, nextSlot, colSpan, rowSpan, viewportColumns)) nextSlot += 1;
        next[viewport].tiles.push({ id: newTileId, slot: nextSlot, colSpan, rowSpan });
        next[viewport].targetRows = Math.max(
          previous[viewport].targetRows,
          getRequiredRows(next[viewport].tiles, viewportColumns),
          VIEWPORT_BASE_ROWS[viewport],
        );
      });

      return next;
    });
    setNextTileId((previous) => previous + 1);
  };

  const addColumn = () => {
    addColumnAtSide("right");
  };

  const addColumnAtSide = (side: "left" | "right") => {
    setViewportLayouts((previous) => {
      const current = previous[activeViewport];
      const currentColumns = current.targetColumns;
      const maxColumns = VIEWPORT_MAX_COLUMNS[activeViewport];
      if (currentColumns >= maxColumns) return previous;
      const nextColumns = currentColumns + 1;
      const nextTiles = current.tiles.map((tile) => {
        const pos = getGridPosition(tile.slot, currentColumns);
        const nextCol = side === "left" ? pos.col + 1 : pos.col;
        return {
          ...tile,
          slot: pos.row * nextColumns + nextCol,
          colSpan: clamp(tile.colSpan, 1, nextColumns),
        };
      });
      return {
        ...previous,
        [activeViewport]: {
          ...current,
          targetColumns: nextColumns,
          tiles: nextTiles,
          targetRows: Math.max(current.targetRows, getRequiredRows(nextTiles, nextColumns), VIEWPORT_BASE_ROWS[activeViewport]),
        },
      };
    });
  };

  const addRowAtSide = (side: "top" | "bottom") => {
    setViewportLayouts((previous) => {
      const current = previous[activeViewport];
      if (current.targetRows >= MAX_ROWS) return previous;
      const columnsForViewport = current.targetColumns;
      const nextRows = Math.min(MAX_ROWS, current.targetRows + 1);
      const nextTiles =
        side === "top"
          ? current.tiles.map((tile) => {
              const pos = getGridPosition(tile.slot, columnsForViewport);
              return {
                ...tile,
                slot: (pos.row + 1) * columnsForViewport + pos.col,
              };
            })
          : current.tiles.map((tile) => ({ ...tile }));
      return {
        ...previous,
        [activeViewport]: {
          ...current,
          tiles: nextTiles,
          targetRows: Math.max(
            nextRows,
            getRequiredRows(nextTiles, columnsForViewport),
            VIEWPORT_BASE_ROWS[activeViewport],
          ),
        },
      };
    });
  };

  const confirmDeleteStructure = (
    rowsToDelete: number[] = selectedDeleteRows,
    colsToDelete: number[] = selectedDeleteCols,
  ) => {
    setViewportLayouts((previous) => {
      const current = previous[activeViewport];
      let nextLayout: ViewportLayout = {
        ...current,
        tiles: current.tiles.map((tile) => ({ ...tile })),
      };

      if (colsToDelete.length > 0 && nextLayout.targetColumns > VIEWPORT_MIN_COLUMNS) {
        const deletableCols = colsToDelete
          .filter((col) => col >= 0 && col < nextLayout.targetColumns)
          .filter((col) => !isColumnOccupied(nextLayout.tiles, nextLayout.targetColumns, col))
          .sort((a, b) => a - b);
        if (deletableCols.length > 0) {
          const maxRemovable = nextLayout.targetColumns - VIEWPORT_MIN_COLUMNS;
          const toRemove = new Set(deletableCols.slice(0, maxRemovable));
          if (toRemove.size > 0) {
            nextLayout = removeColumnsFromLayout(nextLayout, toRemove, VIEWPORT_BASE_ROWS[activeViewport]);
          }
        }
      }

      if (rowsToDelete.length > 0) {
        const removableRows = rowsToDelete
          .filter((row) => row >= 0 && row < nextLayout.targetRows)
          .filter((row) => !isRowOccupied(nextLayout.tiles, nextLayout.targetColumns, row));
        if (removableRows.length > 0) {
          nextLayout = removeRowsFromLayout(nextLayout, new Set(removableRows), VIEWPORT_BASE_ROWS[activeViewport]);
        }
      }

      return {
        ...previous,
        [activeViewport]: nextLayout,
      };
    });
    setSelectedDeleteRows([]);
    setSelectedDeleteCols([]);
    setIsDeleteStructureMode(true);
  };

  const moveTileToHolder = (tileId: number) => {
    const tile = viewportLayouts[activeViewport].tiles.find((item) => item.id === tileId);
    if (!tile) return;
    setViewportLayouts((previous) => {
      const viewportColumns = previous[activeViewport].targetColumns;
      const current = previous[activeViewport];
      const nextTiles = current.tiles.filter((tile) => tile.id !== tileId);
      if (nextTiles.length === current.tiles.length) return previous;
      return {
        ...previous,
        [activeViewport]: {
          ...current,
          tiles: nextTiles,
          targetRows: Math.max(current.targetRows, getRequiredRows(nextTiles, viewportColumns), VIEWPORT_BASE_ROWS[activeViewport]),
        },
      };
    });
    setViewportHolders((previous) => {
      const current = previous[activeViewport];
      if (current.some((holderTile) => holderTile.id === tileId)) return previous;
      return {
        ...previous,
        [activeViewport]: [
          ...current,
          {
            id: tile.id,
            colSpan: tile.colSpan,
            rowSpan: tile.rowSpan,
            returnColSpan: tile.colSpan,
            returnRowSpan: tile.rowSpan,
          },
        ],
      };
    });
  };

  const restoreHeldTileToViewport = (
    tileId: number,
    preferredSlot: number | null,
    sizeOverride?: { colSpan: number; rowSpan: number },
  ) => {
    const heldTile = viewportHolders[activeViewport].find((holderTile) => holderTile.id === tileId);
    const restoreColSpan = clamp(
      sizeOverride?.colSpan ?? heldTile?.returnColSpan ?? heldTile?.colSpan ?? 1,
      1,
      viewportLayouts[activeViewport].targetColumns,
    );
    const restoreRowSpan = clamp(sizeOverride?.rowSpan ?? heldTile?.returnRowSpan ?? heldTile?.rowSpan ?? 1, 1, MAX_ROW_SPAN);

    setViewportLayouts((previous) => {
      const viewportColumns = previous[activeViewport].targetColumns;
      const current = previous[activeViewport];
      if (current.tiles.some((tile) => tile.id === tileId)) return previous;
      let slot = preferredSlot ?? 0;
      while (!canPlaceTile(current.tiles, null, slot, restoreColSpan, restoreRowSpan, viewportColumns)) slot += 1;
      const nextTiles = [...current.tiles, { id: tileId, slot, colSpan: restoreColSpan, rowSpan: restoreRowSpan }];
      return {
        ...previous,
        [activeViewport]: {
          ...current,
          tiles: nextTiles,
          targetRows: Math.max(current.targetRows, getRequiredRows(nextTiles, viewportColumns)),
        },
      };
    });
    setViewportHolders((previous) => ({
      ...previous,
      [activeViewport]: previous[activeViewport].filter((holderTile) => holderTile.id !== tileId),
    }));
  };

  const deleteTile = (tileId: number) => {
    setViewportLayouts((previous) => {
      const next: ViewportLayouts = {
        mobile: {
          ...previous.mobile,
          tiles: previous.mobile.tiles.filter((tile) => tile.id !== tileId),
        },
        tablet: {
          ...previous.tablet,
          tiles: previous.tablet.tiles.filter((tile) => tile.id !== tileId),
        },
        desktop: {
          ...previous.desktop,
          tiles: previous.desktop.tiles.filter((tile) => tile.id !== tileId),
        },
      };

      return {
        mobile: {
          ...next.mobile,
          targetRows: Math.max(previous.mobile.targetRows, getRequiredRows(next.mobile.tiles, next.mobile.targetColumns), VIEWPORT_BASE_ROWS.mobile),
        },
        tablet: {
          ...next.tablet,
          targetRows: Math.max(previous.tablet.targetRows, getRequiredRows(next.tablet.tiles, next.tablet.targetColumns), VIEWPORT_BASE_ROWS.tablet),
        },
        desktop: {
          ...next.desktop,
          targetRows: Math.max(previous.desktop.targetRows, getRequiredRows(next.desktop.tiles, next.desktop.targetColumns), VIEWPORT_BASE_ROWS.desktop),
        },
      };
    });
    if (draggingTileId === tileId) {
      setDraggingTileId(null);
      setActiveDropSlot(null);
      setDragSession(null);
      setDragPreview(null);
    }
    if (resizeSession?.tileId === tileId) {
      setResizeSession(null);
      setResizePreview(null);
      setResizeVisual(null);
    }
    setViewportHolders((previous) => ({
      mobile: previous.mobile.filter((holderTile) => holderTile.id !== tileId),
      tablet: previous.tablet.filter((holderTile) => holderTile.id !== tileId),
      desktop: previous.desktop.filter((holderTile) => holderTile.id !== tileId),
    }));
  };

  const moveTileToSlot = (tileId: number, targetSlot: number) => {
    setViewportLayouts((previous) => {
      const currentLayout = previous[activeViewport];
      const viewportColumns = currentLayout.targetColumns;
      const tile = currentLayout.tiles.find((item) => item.id === tileId);
      if (!tile) return previous;
      if (tile.slot === targetSlot) return previous;
      if (!canPlaceTile(currentLayout.tiles, tile.id, targetSlot, tile.colSpan, tile.rowSpan, viewportColumns)) return previous;
      const nextTiles = currentLayout.tiles.map((item) => (item.id === tile.id ? { ...item, slot: targetSlot } : item));
      const requiredRows = getRequiredRows(nextTiles, viewportColumns);
      const nextTargetRows = Math.max(currentLayout.targetRows, requiredRows, VIEWPORT_BASE_ROWS[activeViewport]);

      return {
        ...previous,
        [activeViewport]: {
          ...currentLayout,
          tiles: nextTiles,
          targetRows: Math.min(MAX_ROWS, nextTargetRows),
        },
      };
    });
  };

  useEffect(() => {
    if (!resizeSession || !gridMetrics) return;

    const previousCursor = document.body.style.cursor;
    document.body.style.cursor = "se-resize";

    const onMouseMove = (event: MouseEvent) => {
      const tile = tiles.find((item) => item.id === resizeSession.tileId);
      if (!tile) return;

      const dx = event.clientX - resizeSession.startX;
      const dy = event.clientY - resizeSession.startY;
      const stepX = Math.max(1, gridMetrics.cellWidth + gridMetrics.colGap);
      const stepY = Math.max(1, gridMetrics.cellHeight + gridMetrics.rowGap);
      const colDelta = Math.round(dx / stepX);
      const rowDelta = Math.round(dy / stepY);
      const startPos = getGridPosition(resizeSession.startSlot, columns);
      const startEndCol = startPos.col + resizeSession.startColSpan - 1;
      const startEndRow = startPos.row + resizeSession.startRowSpan - 1;

      let nextStartCol = startPos.col;
      let nextEndCol = startEndCol;
      let nextStartRow = startPos.row;
      let nextEndRow = startEndRow;

      if (resizeSession.handle === "br") {
        nextEndCol = clamp(startEndCol + colDelta, startPos.col, columns - 1);
        nextEndRow = Math.max(startPos.row, startEndRow + rowDelta);
      } else if (resizeSession.handle === "tl") {
        nextStartCol = clamp(startPos.col + colDelta, 0, startEndCol);
        nextStartRow = Math.max(0, Math.min(startPos.row + rowDelta, startEndRow));
      } else if (resizeSession.handle === "tr") {
        nextEndCol = clamp(startEndCol + colDelta, startPos.col, columns - 1);
        nextStartRow = Math.max(0, Math.min(startPos.row + rowDelta, startEndRow));
      } else if (resizeSession.handle === "bl") {
        nextStartCol = clamp(startPos.col + colDelta, 0, startEndCol);
        nextEndRow = Math.max(startPos.row, startEndRow + rowDelta);
      }

      const nextColSpan = clamp(nextEndCol - nextStartCol + 1, 1, columns);
      const nextRowSpan = clamp(nextEndRow - nextStartRow + 1, 1, MAX_ROW_SPAN);
      const nextSlot = nextStartRow * columns + nextStartCol;

      setResizePreview({ tileId: tile.id, slot: nextSlot, colSpan: nextColSpan, rowSpan: nextRowSpan });

      let visualLeft = resizeSession.startLeft;
      let visualTop = resizeSession.startTop;
      let visualWidth = resizeSession.startWidth;
      let visualHeight = resizeSession.startHeight;
      if (resizeSession.handle === "br") {
        visualWidth = Math.max(72, resizeSession.startWidth + dx);
        visualHeight = Math.max(72, resizeSession.startHeight + dy);
      } else if (resizeSession.handle === "tl") {
        visualLeft = resizeSession.startLeft + dx;
        visualTop = resizeSession.startTop + dy;
        visualWidth = Math.max(72, resizeSession.startWidth - dx);
        visualHeight = Math.max(72, resizeSession.startHeight - dy);
      } else if (resizeSession.handle === "tr") {
        visualTop = resizeSession.startTop + dy;
        visualWidth = Math.max(72, resizeSession.startWidth + dx);
        visualHeight = Math.max(72, resizeSession.startHeight - dy);
      } else if (resizeSession.handle === "bl") {
        visualLeft = resizeSession.startLeft + dx;
        visualWidth = Math.max(72, resizeSession.startWidth - dx);
        visualHeight = Math.max(72, resizeSession.startHeight + dy);
      }

      setResizeVisual({
        tileId: tile.id,
        left: visualLeft,
        top: visualTop,
        width: visualWidth,
        height: visualHeight,
      });
    };

    const onMouseUp = () => {
      setViewportLayouts((previous) => {
        if (!resizePreview || resizePreview.tileId !== resizeSession.tileId) return previous;

        const sourceViewport = activeViewport;
        const sourceColumns = previous[sourceViewport].targetColumns;
        const sourceLayout = previous[sourceViewport];
        const sourceTile = sourceLayout.tiles.find((item) => item.id === resizeSession.tileId);
        if (!sourceTile) return previous;

        const valid = canPlaceTile(
          sourceLayout.tiles,
          sourceTile.id,
          resizePreview.slot,
          resizePreview.colSpan,
          resizePreview.rowSpan,
          sourceColumns,
        );
        if (!valid) return previous;

        const nextLayouts = { ...previous };

        (["mobile", "tablet", "desktop"] as EditViewport[]).forEach((viewport) => {
          const viewportColumns = previous[viewport].targetColumns;
          let nextTiles = previous[viewport].tiles.map((tile) => ({ ...tile }));
          const tileIndex = nextTiles.findIndex((tile) => tile.id === resizeSession.tileId);
          if (tileIndex === -1) return;

          if (viewport === sourceViewport) {
            nextTiles[tileIndex] = {
              ...nextTiles[tileIndex],
              slot: resizePreview.slot,
              colSpan: clamp(resizePreview.colSpan, 1, viewportColumns),
              rowSpan: clamp(resizePreview.rowSpan, 1, MAX_ROW_SPAN),
            };
          } else {
            const syncedColSpan = clamp(resizePreview.colSpan, 1, viewportColumns);
            nextTiles[tileIndex] = {
              ...nextTiles[tileIndex],
              colSpan: syncedColSpan,
              rowSpan: clamp(resizePreview.rowSpan, 1, MAX_ROW_SPAN),
            };
            nextTiles = fitTilesToColumns(nextTiles, viewportColumns, viewportColumns);
          }

          nextLayouts[viewport] = {
            ...previous[viewport],
            tiles: nextTiles,
            targetRows: Math.max(previous[viewport].targetRows, getRequiredRows(nextTiles, viewportColumns), VIEWPORT_BASE_ROWS[viewport]),
          };
        });

        return nextLayouts;
      });

      setResizeSession(null);
      setResizePreview(null);
      setResizeVisual(null);
    };

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
      document.body.style.cursor = previousCursor;
    };
  }, [activeViewport, columns, gridMetrics, resizePreview, resizeSession, tiles]);

  useEffect(() => {
    if (!dragSession || !gridMetrics || !gridRef.current) return;

    const onMouseMove = (event: MouseEvent) => {
      const scrollContainer = gridScrollRef.current;
      if (scrollContainer) {
        const rect = scrollContainer.getBoundingClientRect();
        const edge = 84;
        const maxStep = 10;
        let dx = 0;
        let dy = 0;

        if (event.clientY < rect.top + edge) {
          dy = -Math.ceil(((rect.top + edge - event.clientY) / edge) * maxStep);
        } else if (event.clientY > rect.bottom - edge) {
          dy = Math.ceil(((event.clientY - (rect.bottom - edge)) / edge) * maxStep);
        }

        if (event.clientX < rect.left + edge) {
          dx = -Math.ceil(((rect.left + edge - event.clientX) / edge) * maxStep);
        } else if (event.clientX > rect.right - edge) {
          dx = Math.ceil(((event.clientX - (rect.right - edge)) / edge) * maxStep);
        }

        if (dx !== 0 || dy !== 0) {
          scrollContainer.scrollBy({ left: dx, top: dy });
        }
      }

      setDragPreview({
        tileId: dragSession.tileId,
        x: event.clientX - dragSession.pointerOffsetX,
        y: event.clientY - dragSession.pointerOffsetY,
        width: dragSession.ghostWidth,
        height: dragSession.ghostHeight,
      });

      const slot = getSlotFromPoint(event.clientX, event.clientY, gridRef.current!, gridMetrics, columns);
      const holderRect = holderDropRef.current?.getBoundingClientRect();
      const overHolder = holderRect
        ? event.clientX >= holderRect.left
          && event.clientX <= holderRect.right
          && event.clientY >= holderRect.top
          && event.clientY <= holderRect.bottom
        : false;

      setActiveDropSlot(slot);
      setIsOverHolderDrop(overHolder);
    };

    const onMouseUp = (event: MouseEvent) => {
      const slot = getSlotFromPoint(event.clientX, event.clientY, gridRef.current!, gridMetrics, columns);
      if (dragSession.source === "holder") {
        if (slot !== null) {
          restoreHeldTileToViewport(dragSession.tileId, slot);
        }
      } else if (slot !== null) {
        const tile = tiles.find((item) => item.id === dragSession.tileId);
        if (tile) {
          const alignedSlot = getAlignedTopLeftSlot(slot, dragSession.anchorCol, dragSession.anchorRow, tile, columns);
          moveTileToSlot(dragSession.tileId, alignedSlot);
        }
      } else if (isOverHolderDrop) {
        moveTileToHolder(dragSession.tileId);
      }
      setDraggingTileId(null);
      setActiveDropSlot(null);
      setDragSession(null);
      setDragPreview(null);
      setIsOverHolderDrop(false);
    };

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, [columns, dragSession, gridMetrics, isOverHolderDrop, moveTileToHolder, restoreHeldTileToViewport, tiles]);

  const maxUsedRow =
    tiles.length > 0
      ? Math.max(...tiles.map((tile) => getGridPosition(tile.slot, columns).row + tile.rowSpan))
      : 0;
  const viewportMinRows = VIEWPORT_BASE_ROWS[activeViewport];
  const computeTotalRows = (candidateTargetRows: number) => {
    const rows = Math.max(viewportMinRows, maxUsedRow, isEditing ? candidateTargetRows : viewportMinRows);
    return Math.min(MAX_ROWS, rows);
  };
  const totalRows = computeTotalRows(targetRows);
  const totalSlots = totalRows * columns;
  const occupiedSlots = getOccupiedSlots(
    tiles.map((tile) => {
      const preview = resizePreview?.tileId === tile.id ? resizePreview : null;
      return preview ? { ...tile, slot: preview.slot, colSpan: preview.colSpan, rowSpan: preview.rowSpan } : tile;
    }),
    columns,
  );

  const canAddRow = totalRows < MAX_ROWS;
  const canAddColumn = columns < VIEWPORT_MAX_COLUMNS[activeViewport];
  const deletableRows = Array.from({ length: totalRows }, (_, rowIndex) => rowIndex).filter(
    (rowIndex) => !isRowOccupied(tiles, columns, rowIndex),
  );
  const deletableColumns = Array.from({ length: columns }, (_, colIndex) => colIndex).filter(
    (colIndex) => !isColumnOccupied(tiles, columns, colIndex),
  );
  useEffect(() => {
    setSelectedDeleteRows((previous) => {
      const next = previous.filter((row) => deletableRows.includes(row));
      return next.length === previous.length ? previous : next;
    });
    setSelectedDeleteCols((previous) => {
      const next = previous.filter((col) => deletableColumns.includes(col));
      return next.length === previous.length ? previous : next;
    });
    setHoveredDeleteRow((previous) => (previous !== null && !deletableRows.includes(previous) ? null : previous));
    setHoveredDeleteCol((previous) => (previous !== null && !deletableColumns.includes(previous) ? null : previous));
  }, [deletableColumns, deletableRows]);
  const editViewportIndex = editingViewport === "mobile" ? 0 : editingViewport === "tablet" ? 1 : 2;
  const editPreviewWidthClass =
    windowWidth < 860
      ? "max-w-[420px]"
      : windowWidth < 1200
        ? "max-w-[900px]"
        : "max-w-[1320px]";
  const editGridViewportWidthClass =
    activeViewport === "mobile"
      ? "max-w-[420px]"
      : activeViewport === "tablet"
        ? "max-w-[900px]"
        : "max-w-none";
  const useCompactEditToolbar = windowWidth < 860;
  const useTabletEditToolbar = !useCompactEditToolbar && windowWidth < 1200;
  const gridControlRailWidthClass =
    activeViewport === "desktop" ? "w-16" : activeViewport === "tablet" ? "w-14" : "w-12";
  const gridControlLeftSpacerDesktopClass =
    activeViewport === "desktop" ? "lg:w-16" : activeViewport === "tablet" ? "lg:w-14" : "lg:w-12";
  const navSectionsBelowAddAssets = sectionOrderForView.filter((section) => section !== "addAssets");
  const accountsSectionIndex = navSectionsBelowAddAssets.indexOf("accounts");
  const isNavDragging = (kind: NavDragKind, key: string) =>
    navDragItem?.kind === kind && navDragItem.key === key;
  const handleDashboardTileDragStart = (event: DragEvent<HTMLElement>, key: NavDashboardTileKey) => {
    if (!isSortNavAndButtons) return;
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", key);
    const tileElement = (event.target as HTMLElement | null)?.closest("[data-dashboard-tile]") as HTMLElement | null;
    if (tileElement) {
      cleanupDashboardTileDragMirror();
      const rect = tileElement.getBoundingClientRect();
      const offsetX = Math.max(0, Math.min(rect.width, event.clientX - rect.left));
      const offsetY = Math.max(0, Math.min(rect.height, event.clientY - rect.top));
      const dragClone = tileElement.cloneNode(true) as HTMLElement;
      dragClone.style.position = "fixed";
      dragClone.style.top = "0px";
      dragClone.style.left = "0px";
      dragClone.style.width = `${rect.width}px`;
      dragClone.style.height = `${rect.height}px`;
      dragClone.style.margin = "0";
      dragClone.style.pointerEvents = "none";
      dragClone.style.opacity = "1";
      dragClone.style.zIndex = "9999";
      dragClone.style.transform = `translate(${rect.left}px, ${rect.top}px)`;
      dragClone.style.boxShadow = "0 14px 32px rgba(15,23,42,0.28)";
      const appRoot = document.querySelector(".app-home");
      if (appRoot) {
        appRoot.appendChild(dragClone);
      } else {
        document.body.appendChild(dragClone);
      }
      navTileDragOffsetRef.current = { x: offsetX, y: offsetY };
      navTileDragImageRef.current = dragClone;
      event.dataTransfer.setDragImage(transparentDragImageRef.current ?? dragClone, 0, 0);
    }
    setNavTileDragKey(key);
    setNavTileDropKey(null);
  };
  const handleDashboardTileDragOver = (event: DragEvent<HTMLElement>, key: NavDashboardTileKey) => {
    if (!isSortNavAndButtons || !navTileDragKey) return;
    event.preventDefault();
    if (navTileDropKey !== key) setNavTileDropKey(key);
  };
  const handleDashboardTileDrop = (event: DragEvent<HTMLElement>, _key: NavDashboardTileKey) => {
    if (!isSortNavAndButtons || !navTileDragKey) return;
    event.preventDefault();
    if (navTileDropKey) {
      setDraftNavDashboardTileOrder((previous) => moveKeyForDrag(previous, navTileDragKey, navTileDropKey) as NavDashboardTileKey[]);
    }
    setNavTileDragKey(null);
    setNavTileDropKey(null);
    cleanupDashboardTileDragMirror();
  };
  const handleDashboardTileDragEnd = () => {
    setNavTileDragKey(null);
    setNavTileDropKey(null);
    cleanupDashboardTileDragMirror();
  };
  const getDashboardTileOrder = (key: NavDashboardTileKey) => dashboardTileOrderForRender.indexOf(key);
  const saveDashboardTilesEdit = () => {
    const nextDashboardTileOrder = normalizeOrder(draftNavDashboardTileOrder, DEFAULT_NAV_DASHBOARD_TILE_ORDER) as NavDashboardTileKey[];
    const assetKeys = assetTypeEntries.map((entry) => entry.key);
    const accountKeys = accountEntries.map((entry) => entry.key);
    const nextAssetOrder = normalizeOrder(draftNavAssetItemOrder, assetKeys);
    const nextAccountOrder = normalizeOrder(draftNavAccountItemOrder, accountKeys);
    setNavDashboardTileOrder(nextDashboardTileOrder);
    setNavAssetItemOrder(nextAssetOrder);
    setNavAccountItemOrder(nextAccountOrder);
    setDraftNavDashboardTileOrder(nextDashboardTileOrder);
    setDraftNavAssetItemOrder(nextAssetOrder);
    setDraftNavAccountItemOrder(nextAccountOrder);
    if (hasHydratedNavState) {
      void upsertNavigationState({
        scope: navigationScope,
        section_order: navSectionOrder,
        asset_item_order: nextAssetOrder,
        account_item_order: nextAccountOrder,
        asset_types_collapsed: assetTypesCollapsed,
        accounts_collapsed: accountsCollapsed,
        active_item_key: activeSidebarCategory,
      }).catch(() => {
        // Keep UI responsive if persistence fails.
      });
    }
    setDashboardTilesEditMode(false);
    setDashboardTilesConfirmOpen(false);
    setDashboardTilesCancelOpen(false);
  };
  const cancelDashboardTilesEdit = () => {
    setDraftNavDashboardTileOrder([...dashboardTileOrderForRender]);
    setDraftNavAssetItemOrder([...navAssetItemOrder]);
    setDraftNavAccountItemOrder([...navAccountItemOrder]);
    setDashboardTilesEditMode(false);
    setDashboardTilesConfirmOpen(false);
    setDashboardTilesCancelOpen(false);
    setNavTileDragKey(null);
    setNavTileDropKey(null);
  };
  const isSortNavAndButtons = dashboardTilesEditMode;
  const isAssetsLiabilitiesDashboard = activeSidebarCategory === "assets-liabilities";
  const isNavRearranging = false;
  const overviewCollapsedInView = dashboardTilesEditMode ? false : overviewCollapsed;
  const favoritesCollapsedInView = dashboardTilesEditMode ? false : favoritesCollapsed;
  const assetTypesCollapsedInView = dashboardTilesEditMode ? false : assetTypesCollapsed;
  const accountsCollapsedInView = dashboardTilesEditMode ? false : accountsCollapsed;
  const customDashboardsCollapsedInView = dashboardTilesEditMode ? false : customDashboardsCollapsed;
  const hiddenDashboardTileSet = useMemo(() => new Set(hiddenDashboardTileKeys), [hiddenDashboardTileKeys]);
  const hiddenNavButtonSet = useMemo(() => new Set(hiddenNavButtonKeys), [hiddenNavButtonKeys]);
  const isDashboardTileHidden = useCallback((key: NavDashboardTileKey) => hiddenDashboardTileSet.has(key), [hiddenDashboardTileSet]);
  const isNavButtonHidden = useCallback((key: string) => hiddenNavButtonSet.has(key), [hiddenNavButtonSet]);
  const shouldRenderDashboardTile = useCallback(
    (key: NavDashboardTileKey) => dashboardTilesEditMode || !hiddenDashboardTileSet.has(key),
    [dashboardTilesEditMode, hiddenDashboardTileSet],
  );
  const shouldRenderNavButton = useCallback(
    (key: string) => dashboardTilesEditMode || !hiddenNavButtonSet.has(key),
    [dashboardTilesEditMode, hiddenNavButtonSet],
  );
  const toggleDashboardTileVisibility = useCallback((key: NavDashboardTileKey) => {
    setHiddenDashboardTileKeys((previous) => (previous.includes(key) ? previous.filter((entry) => entry !== key) : [...previous, key]));
  }, []);
  const toggleNavButtonVisibility = useCallback((key: string) => {
    setHiddenNavButtonKeys((previous) => (previous.includes(key) ? previous.filter((entry) => entry !== key) : [...previous, key]));
  }, []);
  const hiddenInEditClass = (hidden: boolean) =>
    dashboardTilesEditMode && hidden ? "opacity-45 ring-1 ring-dashed ring-slate-300 dark:ring-border" : "";

  const assetsLiabilitiesTypeOptions = useMemo(() => {
    const options: Array<{ key: string; label: string }> = [{ key: "investments", label: "Investments" }];
    const accountTypesById = new Map((accountCreateOptions?.account_types ?? []).map((type) => [type.id, type] as const));
    const slugToName = new Map(
      assetTypes
        .filter((assetType): assetType is AssetTypeOption & { slug: string } => Boolean(assetType.slug))
        .map((assetType) => [assetType.slug, assetType.name] as const),
    );
    const heldAssetTypeSlugs = new Set<string>();
    accountRows.forEach((account) => {
      if (account.holdings_count <= 0) return;
      const accountType = accountTypesById.get(account.account_type);
      for (const slug of accountType?.allowed_asset_type_slugs ?? []) {
        if (slug) heldAssetTypeSlugs.add(slug);
      }
    });
    Array.from(heldAssetTypeSlugs)
      .sort((a, b) => {
        const nameA = slugToName.get(a) ?? formatSlugLabel(a);
        const nameB = slugToName.get(b) ?? formatSlugLabel(b);
        return nameA.localeCompare(nameB);
      })
      .forEach((slug) => {
        const label = slugToName.get(slug) ?? formatSlugLabel(slug);
        if (label.toLowerCase() === "investments") return;
        options.push({ key: `asset-type:${slug}`, label });
      });
    return options;
  }, [accountCreateOptions?.account_types, accountRows, assetTypes]);
  const totalAccountHoldings = useMemo(
    () => accountRows.reduce((sum, account) => sum + Math.max(0, account.holdings_count ?? 0), 0),
    [accountRows],
  );

  useEffect(() => {
    if (!isAssetsLiabilitiesDashboard || !isEditing) return;
    setIsEditing(false);
  }, [isAssetsLiabilitiesDashboard, isEditing]);

  useEffect(() => {
    if (activeAppShellSection === "addAccount") return;
    if (activeAppShellSection === "portfolio" && activeSidebarCategory === "portfolio") return;
    if (activeSidebarCategory === "accounts" || activeSidebarCategory.startsWith("account:")) {
      setActiveAppShellSection("accounts");
      return;
    }
    if (activeSidebarCategory.startsWith("asset-type:")) {
      setActiveAppShellSection("assetTypes");
      return;
    }
    setActiveAppShellSection("dashboards");
  }, [activeAppShellSection, activeSidebarCategory]);

  return (
    <main className="app-home min-h-screen w-full bg-background dark:bg-background dark:text-foreground">
      {isNavRearranging ? <div className="fixed inset-0 z-50 bg-slate-900/20 backdrop-blur-[1px]" aria-hidden="true" /> : null}
      {dashboardTilesEditMode ? <div className="pointer-events-none fixed inset-0 z-20 bg-slate-900/25 backdrop-blur-[4px]" aria-hidden="true" /> : null}
      <div className="flex min-h-screen w-full">
        <aside
          className={`fixed left-0 top-0 hidden h-screen shrink-0 flex-col border-r border-background bg-background py-6 transition-[width,padding] duration-200 lg:flex ${
            isSideNavCollapsed ? "px-[10px]" : "pl-6 pr-2"
          } ${sideNavWidthClass}`}
        >
          <div className={`flex h-[72px] items-center px-2 ${isSideNavCollapsed ? "justify-center" : "gap-3"}`}>
            <div className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
              <BriefcaseSolidIcon className="h-5 w-5" />
            </div>
            {!isSideNavCollapsed ? <p className="text-lg font-semibold tracking-tight text-foreground">FinPro</p> : null}
          </div>
          <div className={`mt-8 flex flex-1 flex-col gap-1 ${isSideNavCollapsed ? "" : "px-0"}`}>
            <button
              type="button"
              onClick={() => {
                setActiveAppShellSection("portfolio");
                setActiveSidebarCategory("portfolio");
                setActiveSidebarLabel("Portfolio");
              }}
              className={`relative flex items-center rounded-xl py-3 text-left text-[0.92rem] transition-colors ${
                isSideNavCollapsed ? "w-full px-3" : "w-full px-3"
              } ${
                isSideNavCollapsed ? "justify-center" : "gap-3"
              } ${
                activeAppShellSection === "portfolio"
                  ? "bg-foreground/[0.07] font-bold text-foreground"
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground"
              }`}
              aria-label="Portfolio"
            >
              <span className="inline-flex h-7 w-7 shrink-0 items-center justify-center text-muted-foreground transition-colors">
                {activeAppShellSection === "portfolio" ? (
                  <HomeSolidIcon className="h-[18px] w-[18px] text-foreground" />
                ) : (
                  <HomeOutlineIcon className="h-4 w-4 text-muted-foreground" />
                )}
              </span>
              {!isSideNavCollapsed ? <span>Portfolio</span> : null}
            </button>
            <button
              type="button"
              onClick={() => {
                setActiveAppShellSection("holdings");
                setActiveSidebarCategory("portfolio");
                setActiveSidebarLabel("Portfolio");
              }}
              className={`relative flex items-center rounded-xl py-3 text-left text-[0.92rem] transition-colors ${
                isSideNavCollapsed ? "w-full px-3" : "w-full px-3"
              } ${
                isSideNavCollapsed ? "justify-center" : "gap-3"
              } ${
                activeAppShellSection === "holdings"
                  ? "bg-foreground/[0.07] font-bold text-foreground"
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground"
              }`}
              aria-label="Holdings"
            >
              <span className="inline-flex h-7 w-7 shrink-0 items-center justify-center text-muted-foreground transition-colors">
                {activeAppShellSection === "holdings" ? (
                  <ListBulletSolidIcon className="h-[18px] w-[18px] text-foreground" />
                ) : (
                  <ListBulletOutlineIcon className="h-4 w-4 text-muted-foreground" />
                )}
              </span>
              {!isSideNavCollapsed ? <span>Holdings</span> : null}
            </button>
            <button
              type="button"
              onClick={() => {
                setActiveAppShellSection("dashboards");
                setActiveSidebarCategory("portfolio");
                setActiveSidebarLabel("Portfolio");
              }}
              className={`relative flex items-center rounded-xl py-3 text-left text-[0.92rem] transition-colors ${
                isSideNavCollapsed ? "w-full px-3" : "w-full px-3"
              } ${
                isSideNavCollapsed ? "justify-center" : "gap-3"
              } ${
                activeAppShellSection === "dashboards"
                  ? "bg-foreground/[0.07] font-bold text-foreground"
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground"
              }`}
              aria-label="Dashboards"
            >
              <span className="inline-flex h-7 w-7 shrink-0 items-center justify-center text-muted-foreground transition-colors">
                {activeAppShellSection === "dashboards" ? (
                  <Squares2X2SolidIcon className="h-[18px] w-[18px] text-foreground" />
                ) : (
                  <Squares2X2OutlineIcon className="h-4 w-4 text-muted-foreground" />
                )}
              </span>
              {!isSideNavCollapsed ? <span>Dashboards</span> : null}
            </button>
            <button
              type="button"
              onClick={() => {
                setActiveAppShellSection("accounts");
                setActiveSidebarCategory("accounts");
                setActiveSidebarLabel("Accounts");
              }}
              className={`relative flex items-center rounded-xl py-3 text-left text-[0.92rem] transition-colors ${
                isSideNavCollapsed ? "w-full px-3" : "w-full px-3"
              } ${
                isSideNavCollapsed ? "justify-center" : "gap-3"
              } ${
                activeAppShellSection === "accounts"
                  ? "bg-foreground/[0.07] font-bold text-foreground"
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground"
              }`}
              aria-label="Accounts"
            >
              <span className="inline-flex h-7 w-7 shrink-0 items-center justify-center text-muted-foreground transition-colors">
                {activeAppShellSection === "accounts" ? (
                  <WalletSolidIcon className="h-[18px] w-[18px] text-foreground" />
                ) : (
                  <WalletOutlineIcon className="h-4 w-4 text-muted-foreground" />
                )}
              </span>
              {!isSideNavCollapsed ? <span>Accounts</span> : null}
            </button>
            <button
              type="button"
              onClick={() => {
                setActiveAppShellSection("assetTypes");
                const firstAssetType = assetTypeEntries[0];
                if (firstAssetType) {
                  setActiveSidebarCategory(firstAssetType.key);
                  setActiveSidebarLabel(firstAssetType.assetType.name);
                  return;
                }
                setActiveSidebarCategory("portfolio");
                setActiveSidebarLabel("Portfolio");
              }}
              className={`relative flex items-center rounded-xl py-3 text-left text-[0.92rem] transition-colors ${
                isSideNavCollapsed ? "w-full px-3" : "w-full px-3"
              } ${
                isSideNavCollapsed ? "justify-center" : "gap-3"
              } ${
                activeAppShellSection === "assetTypes"
                  ? "bg-foreground/[0.07] font-bold text-foreground"
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground"
              }`}
              aria-label="Asset Types"
            >
              <span className="inline-flex h-7 w-7 shrink-0 items-center justify-center text-muted-foreground transition-colors">
                {activeAppShellSection === "assetTypes" ? (
                  <CubeSolidIcon className="h-[18px] w-[18px] text-foreground" />
                ) : (
                  <CubeOutlineIcon className="h-4 w-4 text-muted-foreground" />
                )}
              </span>
              {!isSideNavCollapsed ? <span>Asset Types</span> : null}
            </button>
          </div>
          <button
            type="button"
            className={`mt-6 flex items-center rounded-xl px-3 py-3 text-left text-sm text-foreground transition-colors hover:bg-secondary ${
              isSideNavCollapsed ? "justify-center" : "gap-3"
            }`}
            aria-label="Profile"
          >
            <UserCircleOutlineIcon className="h-5 w-5 shrink-0 text-muted-foreground" />
            {!isSideNavCollapsed ? <span className="truncate">{profileFirstName}</span> : null}
          </button>
          <button
            type="button"
            onClick={() => setIsSideNavCollapsed((previous) => !previous)}
            className={`mt-2 flex items-center rounded-xl px-3 py-3 text-left text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground ${
              isSideNavCollapsed ? "justify-center" : "gap-3"
            }`}
            aria-label={isSideNavCollapsed ? "Expand side navigation" : "Collapse side navigation"}
          >
            {isSideNavCollapsed ? <ChevronRight className="h-5 w-5 shrink-0" /> : <ChevronLeft className="h-5 w-5 shrink-0" />}
            {!isSideNavCollapsed ? <span>Collapse</span> : null}
          </button>
        </aside>
        <div className={`min-w-0 flex-1 px-4 pb-2 pt-[88px] sm:px-6 sm:pt-[92px] ${sideNavContentInsetClass}`}>
          <div className={`fixed left-0 right-0 top-2 z-40 ${sideNavLeftOffsetClass}`}>
            <div className={`px-4 sm:px-6 ${topNavInsetClass}`}>
              <div className="w-full max-w-none lg:ml-auto lg:mr-0">
                <div className="flex h-[72px] items-center justify-between gap-4 border border-background bg-background px-5 shadow-none">
                  <div className="min-w-0">
                    <h1 className="truncate text-xl font-semibold tracking-tight text-foreground">
                      {activeAppShellSection === "portfolio"
                        ? "Portfolio"
                        : activeAppShellSection === "holdings"
                          ? "Holdings"
                          : activeAppShellSection === "dashboards"
                            ? "Dashboards"
                            : activeAppShellSection === "accounts"
                              ? "Accounts"
                              : activeAppShellSection === "addAccount"
                                ? "Add Account"
                              : "Asset Types"}
                    </h1>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setIsAddAssetModalOpen(true)}
                      className="inline-flex items-center gap-2 rounded-full bg-white/90 px-4 py-2 text-[0.92rem] font-bold text-foreground shadow-[0_6px_14px_rgba(28,24,20,0.08)] transition-colors hover:bg-white"
                    >
                      <Plus className="h-4 w-4" />
                      <span>Add Assets</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setActiveAppShellSection("addAccount");
                        setActiveSidebarCategory("accounts");
                        setActiveSidebarLabel("Accounts");
                      }}
                      className="inline-flex items-center gap-2 rounded-full bg-white/90 px-4 py-2 text-[0.92rem] font-bold text-foreground shadow-[0_6px_14px_rgba(28,24,20,0.08)] transition-colors hover:bg-white"
                      aria-label="Add account"
                    >
                      <Plus className="h-4 w-4" />
                      <span>Add Account</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="w-full max-w-none lg:ml-auto lg:mr-0">
            <div>
              <section>
                <div className="flex flex-col gap-4">
              <Card
                className={`hidden relative mt-0 h-fit overflow-visible border-0 bg-transparent shadow-none xl:order-2 xl:mt-0 xl:sticky xl:bottom-6 xl:self-start ${
                  dashboardTilesEditMode ? "z-30" : isNavRearranging ? "z-auto" : "z-30"
                }`}
              >
                <CardContent
                  ref={navEditPanelRef}
                  className="side-nav-panel relative flex h-full flex-col gap-4 overflow-visible p-0"
                  onDragOver={handleNavContainerDragOver}
                  onDrop={handleNavContainerDrop}
                >
                          {dashboardTilesEditMode ? (
                            <div className="pointer-events-none absolute inset-0 z-50 rounded-xl bg-slate-900/12 backdrop-blur-[2px]" aria-hidden="true" />
                          ) : null}
                          <div
                            data-nav-draggable="true"
                            data-nav-target-kind="section"
                            data-nav-target-key="addAssets"
                            className={`relative transition-all duration-150 will-change-transform ${
                              isNavDragging("section", "addAssets")
                                ? "rounded-lg border border-dashed border-slate-500 bg-slate-100/90 shadow-[0_14px_28px_rgba(15,23,42,0.20)]"
                                : ""
                            } ${isNavRearranging || dashboardTilesEditMode ? "pointer-events-none select-none" : ""}`}
                            style={{ order: 0 }}
                            onDragOver={(event) => handleNavTargetDragOver(event, "section", "addAssets")}
                            onDrop={(event) => handleNavTargetDrop(event, "section", "addAssets")}
                          >
                            <div className="space-y-5">
                              {isManagingSections ? (
                                <button
                                  type="button"
                                  draggable
                                  onDragStart={(event) => handleNavDragStart(event, "section", "addAssets")}
                                  onDragEnd={handleNavDragEnd}
                                  className={`inline-flex h-7 w-7 items-center justify-center rounded-full border border-blue-100 bg-white text-slate-600 transition-colors hover:bg-slate-200 ${
                                    isNavDragging("section", "addAssets") ? "cursor-grabbing" : "cursor-grab active:cursor-grabbing"
                                  }`}
                                  aria-label="Reorder Add Assets section"
                                >
                                  <GripVertical className="h-3.5 w-3.5" />
                                </button>
                              ) : null}
                              <div className="grid grid-cols-2 gap-3">
                                <button
                                  type="button"
                                  onClick={() => {
                                    if (canEditButtonsForKind("asset") || canEditButtonsForKind("account")) return;
                                    setActiveSidebarCategory("portfolio");
                                    setActiveSidebarLabel("Portfolio");
                                  }}
                                  className={`flex h-[92px] w-full flex-col items-center justify-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-3 py-3 text-center text-sm font-normal transition-colors dark:border-border dark:bg-card ${
                                    activeSidebarCategory === "portfolio"
                                      ? "sidebar-nav-item-active text-foreground dark:text-foreground"
                                      : "text-slate-600 hover:bg-zinc-300/70 hover:text-slate-900 dark:text-slate-200 dark:hover:bg-accent dark:hover:text-foreground"
                                  }`}
                                  aria-label="Portfolio"
                                >
                                  {activeSidebarCategory === "portfolio" ? (
                                    <HomeSolidIcon className="h-4 w-4 text-current" />
                                  ) : (
                                    <HomeOutlineIcon className="h-4 w-4 text-current" />
                                  )}
                                  <span className={`relative inline-flex min-h-[1.1rem] items-center text-sm leading-none ${activeSidebarCategory === "portfolio" ? "font-bold" : "font-normal"}`}>
                                    Portfolio
                                    {activeSidebarCategory === "portfolio" ? <span className="absolute -bottom-1.5 left-1 right-1 h-0.5 bg-current" /> : null}
                                  </span>
                                </button>
                                <button
                                  type="button"
                                  onClick={() => {
                                    if (canEditButtonsForKind("asset") || canEditButtonsForKind("account")) return;
                                    setActiveSidebarCategory("assets-liabilities");
                                    setActiveSidebarLabel("Assets & Liabilities");
                                  }}
                                  className={`flex h-[92px] w-full flex-col items-center justify-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-3 py-3 text-center text-sm font-normal transition-colors dark:border-border dark:bg-card ${
                                    activeSidebarCategory === "assets-liabilities"
                                      ? "sidebar-nav-item-active text-foreground dark:text-foreground"
                                      : "text-slate-600 hover:bg-zinc-300/70 hover:text-slate-900 dark:text-slate-200 dark:hover:bg-accent dark:hover:text-foreground"
                                  }`}
                                  aria-label="Assets and liabilities"
                                >
                                  <CurrencyDollarSimpleIcon className="h-4 w-4 text-current" weight="regular" />
                                  <span className={`relative inline-flex min-h-[1.1rem] items-center text-sm leading-none ${activeSidebarCategory === "assets-liabilities" ? "font-bold" : "font-normal"}`}>
                                    Assets & Liabilities
                                    {activeSidebarCategory === "assets-liabilities" ? <span className="absolute -bottom-1.5 left-1 right-1 h-0.5 bg-current" /> : null}
                                  </span>
                                </button>
                              </div>
                            </div>
                          </div>

                          <div
                            data-dashboard-tiles-scroll
                            data-nav-draggable="true"
                            data-nav-target-kind="section"
                            data-nav-target-key="accounts"
                            className={`relative overflow-visible transition-all duration-150 will-change-transform ${
                              dashboardTilesEditMode
                                ? "z-[120]"
                                : isNavRearranging
                                  ? "z-[70] max-h-[calc(100vh-7.5rem)] overflow-y-auto pr-1"
                                  : "z-20"
                            } ${
                              isNavDragging("section", "accounts")
                                ? "rounded-xl border border-dashed border-slate-500 bg-slate-100/90 shadow-[0_14px_28px_rgba(15,23,42,0.20)]"
                                : ""
                            }`}
                            style={{ order: accountsSectionIndex + 1 }}
                            onDragOver={(event) => handleNavTargetDragOver(event, "section", "accounts")}
                            onDrop={(event) => handleNavTargetDrop(event, "section", "accounts")}
                          >
                            <CardContent className="p-0">
                              <div className="flex flex-col gap-4 dark:text-foreground">
                                {isManagingSections ? (
                                  <div className="flex items-center">
                                    <button
                                      type="button"
                                      draggable
                                      onDragStart={(event) => handleNavDragStart(event, "section", "accounts")}
                                      onDragEnd={handleNavDragEnd}
                                      className={`inline-flex h-7 w-7 items-center justify-center rounded-full border border-blue-100 bg-white text-slate-600 transition-colors hover:bg-slate-200 ${
                                        isNavDragging("section", "accounts") ? "cursor-grabbing" : "cursor-grab active:cursor-grabbing"
                                      }`}
                                      aria-label="Reorder Accounts section"
                                    >
                                      <GripVertical className="h-3.5 w-3.5" />
                                    </button>
                                  </div>
                                ) : null}
                                <div className="mt-2 flex items-center justify-between px-1">
                                  <p className="text-lg font-semibold text-slate-500 dark:text-foreground">Dashboards</p>
                                  <div className="relative" data-dashboard-tiles-menu>
                                    {dashboardTilesEditMode ? (
                                      <div className="flex items-center gap-2">
                                        <div className="relative">
                                          <button
                                            type="button"
                                            onClick={() => {
                                              setDashboardTilesConfirmOpen((previous) => !previous);
                                              setDashboardTilesCancelOpen(false);
                                            }}
                                            className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-slate-50 text-slate-700 transition-colors hover:bg-slate-200 hover:text-slate-900 dark:border-border dark:bg-card dark:text-foreground dark:hover:bg-accent"
                                            aria-label="Open confirm changes menu"
                                            title="Confirm changes"
                                          >
                                            <Check className="h-5 w-5" />
                                          </button>
                                          {dashboardTilesConfirmOpen ? (
                                            <div className="absolute right-0 z-[140] mt-1 w-44 rounded-md border border-border bg-white p-1.5 shadow-md dark:bg-popover">
                                              <button
                                                type="button"
                                                onClick={saveDashboardTilesEdit}
                                                className="w-full rounded px-2 py-1.5 text-left text-xs font-semibold text-foreground transition-colors hover:bg-secondary"
                                              >
                                                Confirm Changes
                                              </button>
                                            </div>
                                          ) : null}
                                        </div>
                                        <div className="relative">
                                          <button
                                            type="button"
                                            onClick={() => {
                                              setDashboardTilesCancelOpen((previous) => !previous);
                                              setDashboardTilesConfirmOpen(false);
                                            }}
                                            className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-slate-50 text-slate-700 transition-colors hover:bg-slate-200 hover:text-slate-900 dark:border-border dark:bg-card dark:text-foreground dark:hover:bg-accent"
                                            aria-label="Open cancel editing menu"
                                            title="Cancel editing"
                                          >
                                            <X className="h-5 w-5" />
                                          </button>
                                          {dashboardTilesCancelOpen ? (
                                            <div className="absolute right-0 z-[140] mt-1 w-44 rounded-md border border-border bg-white p-1.5 shadow-md dark:bg-popover">
                                              <button
                                                type="button"
                                                onClick={cancelDashboardTilesEdit}
                                                className="w-full rounded px-2 py-1.5 text-left text-xs font-semibold text-foreground transition-colors hover:bg-secondary"
                                              >
                                                Cancel Editing
                                              </button>
                                            </div>
                                          ) : null}
                                        </div>
                                      </div>
                                    ) : (
                                      <>
                                        <button
                                          type="button"
                                          onClick={() => setDashboardTilesMenuOpen((previous) => !previous)}
                                          className="inline-flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 bg-white text-muted-foreground transition-colors hover:bg-slate-200 hover:text-foreground dark:border-border dark:bg-secondary dark:text-foreground dark:hover:bg-accent"
                                          aria-label="Dashboard tile settings"
                                        >
                                          <Ellipsis className="h-3.5 w-3.5" />
                                        </button>
                                        {dashboardTilesMenuOpen ? (
                                          <div className="absolute right-0 z-[75] mt-1 w-44 rounded-md border border-slate-200 bg-white p-1 shadow-md dark:border-border dark:bg-popover">
                                            <button
                                              type="button"
                                              onClick={() => {
                                                setDraftNavDashboardTileOrder([...dashboardTileOrderForRender]);
                                                setDraftNavAssetItemOrder([...navAssetItemOrder]);
                                                setDraftNavAccountItemOrder([...navAccountItemOrder]);
                                                setDashboardTilesEditMode(true);
                                                setDashboardTilesConfirmOpen(false);
                                                setDashboardTilesCancelOpen(false);
                                                setDashboardTilesMenuOpen(false);
                                              }}
                                              className="w-full rounded px-2 py-1.5 text-left text-xs text-slate-700 transition-colors hover:bg-slate-200 dark:text-foreground dark:hover:bg-accent"
                                            >
                                              Edit Tiles
                                            </button>
                                          </div>
                                        ) : null}
                                      </>
                                    )}
                                  </div>
                                </div>
                                  {shouldRenderDashboardTile("portfolioOverview") ? (
                                  <div
                                    data-dashboard-tile="portfolioOverview"
                                    draggable={false}
                                    onDragOver={(event) => handleDashboardTileDragOver(event, "portfolioOverview")}
                                    onDrop={(event) => handleDashboardTileDrop(event, "portfolioOverview")}
                                    onDragEnd={handleDashboardTileDragEnd}
                                    style={{ order: getDashboardTileOrder("portfolioOverview") }}
                                    className={`rounded-lg border border-slate-200 bg-slate-50 p-2.5 dark:border-border dark:bg-card ${
                                      navTileDropKey === "portfolioOverview" ? "ring-2 ring-slate-400 bg-slate-100/60 dark:bg-muted" : ""
                                    } ${navTileDragKey === "portfolioOverview" ? "opacity-0" : ""} ${hiddenInEditClass(
                                      isDashboardTileHidden("portfolioOverview"),
                                    )}`}
                                  >
                                    <div className="flex items-center justify-between px-1 py-1">
                                      <p className="text-sm font-normal text-slate-500 dark:text-foreground">Overview</p>
                                      <div className="flex items-center gap-1">
                                        {dashboardTilesEditMode ? (
                                          <>
                                            <button
                                              type="button"
                                              onClick={() => toggleDashboardTileVisibility("portfolioOverview")}
                                              className="inline-flex h-7 w-7 items-center justify-center rounded-md border border-border bg-transparent text-foreground transition-colors hover:text-foreground"
                                              aria-label={isDashboardTileHidden("portfolioOverview") ? "Show overview tile" : "Hide overview tile"}
                                              title={isDashboardTileHidden("portfolioOverview") ? "Show overview tile" : "Hide overview tile"}
                                            >
                                              {isDashboardTileHidden("portfolioOverview") ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                                            </button>
                                            <button
                                              type="button"
                                              draggable
                                              onDragStart={(event) => handleDashboardTileDragStart(event, "portfolioOverview")}
                                              onDragEnd={handleDashboardTileDragEnd}
                                              className="inline-flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 bg-white text-muted-foreground transition-colors hover:bg-slate-200 hover:text-foreground dark:border-border dark:bg-secondary dark:text-foreground dark:hover:bg-accent cursor-grab active:cursor-grabbing"
                                              aria-label="Reorder overview tile"
                                              title="Reorder overview tile"
                                            >
                                              <GripVertical className="h-3.5 w-3.5" />
                                            </button>
                                          </>
                                        ) : (
                                          <button
                                            type="button"
                                            onClick={() => setOverviewCollapsed((previous) => !previous)}
                                            className="inline-flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 bg-white text-muted-foreground transition-colors hover:bg-slate-200 hover:text-foreground dark:border-border dark:bg-secondary dark:text-foreground dark:hover:bg-accent"
                                            aria-label={overviewCollapsedInView ? "Expand overview" : "Collapse overview"}
                                            title={overviewCollapsedInView ? "Expand overview" : "Collapse overview"}
                                          >
                                            <ChevronDown className={`h-3.5 w-3.5 transition-transform ${overviewCollapsedInView ? "" : "rotate-180"}`} />
                                          </button>
                                        )}
                                      </div>
                                    </div>
                                    {!overviewCollapsedInView ? (
                                      <button
                                        type="button"
                                        onClick={() => {
                                          setActiveSidebarCategory("portfolio");
                                          setActiveSidebarLabel("Portfolio");
                                        }}
                                        className={`sidebar-nav-item relative w-full rounded-md px-2.5 py-2.5 text-left transition-colors ${
                                          activeSidebarCategory === "portfolio"
                                            ? "sidebar-nav-item-active text-foreground dark:text-foreground"
                                            : "text-slate-600 hover:bg-slate-200 hover:text-slate-900 dark:text-slate-200 dark:hover:bg-accent dark:hover:text-foreground"
                                        }`}
                                      >
                                        <div className="flex items-center gap-2">
                                          {activeSidebarCategory === "portfolio" ? (
                                            <HomeSolidIcon className="h-4 w-4 shrink-0 text-foreground dark:text-foreground" />
                                          ) : (
                                            <HomeOutlineIcon className="h-4 w-4 shrink-0 text-muted-foreground dark:text-muted-foreground" />
                                          )}
                                          <span className={`truncate text-sm ${activeSidebarCategory === "portfolio" ? "font-medium" : "font-normal"}`}>
                                            Portfolio
                                          </span>
                                        </div>
                                        {activeSidebarCategory === "portfolio" ? (
                                          <span className="sidebar-active-indicator absolute bottom-1 right-0 top-1 w-1 rounded-full bg-current" />
                                        ) : null}
                                      </button>
                                    ) : null}
                                  </div>
                                  ) : null}
                                  {shouldRenderDashboardTile("favorites") ? (
                                  <div
                                    data-dashboard-tile="favorites"
                                    draggable={false}
                                    onDragOver={(event) => handleDashboardTileDragOver(event, "favorites")}
                                    onDrop={(event) => handleDashboardTileDrop(event, "favorites")}
                                    onDragEnd={handleDashboardTileDragEnd}
                                    style={{ order: getDashboardTileOrder("favorites") }}
                                    className={`rounded-lg border border-slate-200 bg-slate-50 p-2.5 dark:border-border dark:bg-card ${
                                      navTileDropKey === "favorites" ? "ring-2 ring-slate-400 bg-slate-100/60 dark:bg-muted" : ""
                                    } ${navTileDragKey === "favorites" ? "opacity-0" : ""} ${hiddenInEditClass(
                                      isDashboardTileHidden("favorites"),
                                    )}`}
                                  >
                                    <div className="flex items-center justify-between px-1 py-1">
                                      <p className="text-sm font-normal text-slate-500 dark:text-foreground">Favorites</p>
                                      <div className="flex items-center gap-1">
                                        {dashboardTilesEditMode ? (
                                          <>
                                            <button
                                              type="button"
                                              onClick={() => toggleDashboardTileVisibility("favorites")}
                                              className="inline-flex h-7 w-7 items-center justify-center rounded-md border border-border bg-transparent text-foreground transition-colors hover:text-foreground"
                                              aria-label={isDashboardTileHidden("favorites") ? "Show favorites tile" : "Hide favorites tile"}
                                              title={isDashboardTileHidden("favorites") ? "Show favorites tile" : "Hide favorites tile"}
                                            >
                                              {isDashboardTileHidden("favorites") ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                                            </button>
                                            <button
                                              type="button"
                                              draggable
                                              onDragStart={(event) => handleDashboardTileDragStart(event, "favorites")}
                                              onDragEnd={handleDashboardTileDragEnd}
                                              className="inline-flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 bg-white text-muted-foreground transition-colors hover:bg-slate-200 hover:text-foreground dark:border-border dark:bg-secondary dark:text-foreground dark:hover:bg-accent cursor-grab active:cursor-grabbing"
                                              aria-label="Reorder favorites tile"
                                              title="Reorder favorites tile"
                                            >
                                              <GripVertical className="h-3.5 w-3.5" />
                                            </button>
                                          </>
                                        ) : (
                                          <>
                                            <button
                                              type="button"
                                              onClick={() => setFavoritesCollapsed((previous) => !previous)}
                                              className="inline-flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 bg-white text-muted-foreground transition-colors hover:bg-slate-200 hover:text-foreground dark:border-border dark:bg-secondary dark:text-foreground dark:hover:bg-accent dark:hover:text-foreground"
                                              aria-label={favoritesCollapsedInView ? "Expand favorites" : "Collapse favorites"}
                                              title={favoritesCollapsedInView ? "Expand favorites" : "Collapse favorites"}
                                            >
                                              <ChevronDown className={`h-3.5 w-3.5 transition-transform ${favoritesCollapsedInView ? "" : "rotate-180"}`} />
                                            </button>
                                            <div className="hidden" data-favorites-actions-menu>
                                          <button
                                            type="button"
                                            onClick={() =>
                                              setFavoritesActionsMenuOpen((previous) => {
                                                const next = !previous;
                                                if (!next) setFavoritesActionsSubmenu(null);
                                                setAssetsActionsMenuOpen(false);
                                                setCustomActionsMenuOpen(false);
                                                setAccountsActionsMenuOpen(false);
                                                return next;
                                              })
                                            }
                                            className={`inline-flex h-7 w-7 items-center justify-center rounded-md border transition-colors dark:border-border dark:bg-secondary dark:text-foreground dark:hover:bg-accent dark:hover:text-foreground ${
                                              favoritesActionsMenuOpen
                                                ? "border-slate-300 bg-slate-200 text-slate-800"
                                                : "border-slate-200 bg-white text-slate-600 hover:bg-slate-200 hover:text-slate-900"
                                            }`}
                                            aria-label="More favorite actions"
                                            title="More favorite actions"
                                          >
                                            <Ellipsis className="h-3.5 w-3.5" />
                                          </button>
                                          {favoritesActionsMenuOpen ? (
                                            <div className="absolute right-0 z-[70] mt-1 w-40 rounded-md border border-slate-200 bg-white p-1 shadow-md dark:border-border dark:bg-popover dark:border-border dark:bg-popover">
                                              <div className="relative">
                                                <button
                                                  type="button"
                                                  onClick={() =>
                                                    setFavoritesActionsSubmenu((previous) => (previous === "filter" ? null : "filter"))
                                                  }
                                                  className={`flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-xs transition-colors ${
                                                    favoritesActionsSubmenu === "filter"
                                                      ? "bg-slate-100 text-slate-900"
                                                      : "text-slate-700 hover:bg-slate-200 dark:text-foreground dark:hover:bg-accent"
                                                  }`}
                                                >
                                                  <span>Filter by</span>
                                                  <ChevronDown className="-rotate-90 h-3.5 w-3.5" />
                                                </button>
                                                {favoritesActionsSubmenu === "filter" ? (
                                                  <div className="absolute left-full top-0 z-[80] ml-1 w-52 rounded-md border border-slate-200 bg-white p-2 shadow-md dark:border-border dark:bg-popover dark:border-border dark:bg-popover">
                                                    <label className="text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500" htmlFor="favorites-filter-mode">
                                                      Type
                                                    </label>
                                                    <select
                                                      id="favorites-filter-mode"
                                                      value={favoritesFilterMode}
                                                      onChange={(event) => setFavoritesFilterMode(event.target.value as typeof favoritesFilterMode)}
                                                      className="mt-1 w-full rounded-md border border-slate-200 bg-slate-50 px-2 py-1.5 text-xs text-slate-700 dark:border-border dark:bg-muted dark:text-foreground"
                                                    >
                                                      <option value="all">All favorites</option>
                                                      <option value="asset_type">Asset favorites</option>
                                                      <option value="account">Account favorites</option>
                                                    </select>
                                                  </div>
                                                ) : null}
                                              </div>
                                              <div className="relative">
                                                <button
                                                  type="button"
                                                  onClick={() =>
                                                    setFavoritesActionsSubmenu((previous) => (previous === "sort" ? null : "sort"))
                                                  }
                                                  className={`flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-xs transition-colors ${
                                                    favoritesActionsSubmenu === "sort"
                                                      ? "bg-slate-100 text-slate-900"
                                                      : "text-slate-700 hover:bg-slate-200 dark:text-foreground dark:hover:bg-accent"
                                                  }`}
                                                >
                                                  <span>Sort by</span>
                                                  <ChevronDown className="-rotate-90 h-3.5 w-3.5" />
                                                </button>
                                                {favoritesActionsSubmenu === "sort" ? (
                                                  <div className="absolute left-full top-0 z-[80] ml-1 w-52 rounded-md border border-slate-200 bg-white p-2 shadow-md dark:border-border dark:bg-popover dark:border-border dark:bg-popover">
                                                    <label className="text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500" htmlFor="favorites-sort-mode">
                                                      Sort
                                                    </label>
                                                    <select
                                                      id="favorites-sort-mode"
                                                      value={favoritesSortMode}
                                                      onChange={(event) => setFavoritesSortMode(event.target.value as typeof favoritesSortMode)}
                                                      className="mt-1 w-full rounded-md border border-slate-200 bg-slate-50 px-2 py-1.5 text-xs text-slate-700 dark:border-border dark:bg-muted dark:text-foreground"
                                                    >
                                                      <option value="name_asc">Name (A-Z)</option>
                                                      <option value="name_desc">Name (Z-A)</option>
                                                    </select>
                                                  </div>
                                                ) : null}
                                              </div>
                                            </div>
                                          ) : null}
                                            </div>
                                          </>
                                        )}
                                      </div>
                                    </div>
                                    {isNavRearranging ? (
                                      <div className="mb-1 flex items-center gap-2 px-1">
                                        <button
                                          type="button"
                                          onClick={saveNavigationEdit}
                                          className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-emerald-300 bg-emerald-50 text-emerald-700 transition-colors hover:bg-emerald-100"
                                          aria-label="Save sidebar order"
                                          title="Save sidebar order"
                                        >
                                          <Check className="h-4 w-4" />
                                        </button>
                                        <button
                                          type="button"
                                          onClick={cancelNavigationEdit}
                                          className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-rose-300 bg-rose-50 text-rose-700 transition-colors hover:bg-rose-100"
                                          aria-label="Cancel sidebar rearrange"
                                          title="Cancel sidebar rearrange"
                                        >
                                          <X className="h-4 w-4" />
                                        </button>
                                      </div>
                                    ) : null}
                                    {!dashboardTilesEditMode && !favoritesCollapsedInView && shouldRenderNavButton("action:favorites-add") ? (
                                      <button
                                        type="button"
                                        className={`sidebar-add-dashed w-full rounded-md border border-dashed border-slate-300 px-2.5 py-3 text-left text-sm font-normal text-slate-500 transition-colors hover:bg-slate-200 hover:text-slate-700 dark:border-border dark:text-slate-200 dark:hover:bg-accent dark:hover:text-foreground ${hiddenInEditClass(
                                          isNavButtonHidden("action:favorites-add"),
                                        )}`}
                                      >
                                        + Add Favourite Dashboards
                                      </button>
                                    ) : null}
                                  </div>
                                  ) : null}
                                  {shouldRenderDashboardTile("assets") ? (
                                  <div
                                    data-dashboard-tile="assets"
                                    draggable={false}
                                    onDragOver={(event) => handleDashboardTileDragOver(event, "assets")}
                                    onDrop={(event) => handleDashboardTileDrop(event, "assets")}
                                    onDragEnd={handleDashboardTileDragEnd}
                                    style={{ order: getDashboardTileOrder("assets") }}
                                    className={`rounded-lg border border-slate-200 bg-slate-50 p-2.5 dark:border-border dark:bg-card ${
                                      navTileDropKey === "assets" ? "ring-2 ring-slate-400 bg-slate-100/60 dark:bg-muted" : ""
                                    } ${navTileDragKey === "assets" ? "opacity-0" : ""} ${hiddenInEditClass(isDashboardTileHidden("assets"))}`}
                                  >
                                    <div className="flex items-center justify-between px-1 py-1">
                                      <p className="text-sm font-normal text-slate-500 dark:text-foreground">Assets</p>
                                      <div className="flex items-center gap-1">
                                        {dashboardTilesEditMode ? (
                                          <>
                                            <button
                                              type="button"
                                              onClick={() => toggleDashboardTileVisibility("assets")}
                                              className="inline-flex h-7 w-7 items-center justify-center rounded-md border border-border bg-transparent text-foreground transition-colors hover:text-foreground"
                                              aria-label={isDashboardTileHidden("assets") ? "Show assets tile" : "Hide assets tile"}
                                              title={isDashboardTileHidden("assets") ? "Show assets tile" : "Hide assets tile"}
                                            >
                                              {isDashboardTileHidden("assets") ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                                            </button>
                                            <button
                                              type="button"
                                              draggable
                                              onDragStart={(event) => handleDashboardTileDragStart(event, "assets")}
                                              onDragEnd={handleDashboardTileDragEnd}
                                              className="inline-flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 bg-white text-muted-foreground transition-colors hover:bg-slate-200 hover:text-foreground dark:border-border dark:bg-secondary dark:text-foreground dark:hover:bg-accent cursor-grab active:cursor-grabbing"
                                              aria-label="Reorder assets tile"
                                              title="Reorder assets tile"
                                            >
                                              <GripVertical className="h-3.5 w-3.5" />
                                            </button>
                                          </>
                                        ) : (
                                          <>
                                            <button
                                              type="button"
                                              onClick={() => setAssetTypesCollapsed((previous) => !previous)}
                                              className="inline-flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 bg-white text-muted-foreground transition-colors hover:bg-slate-200 hover:text-foreground dark:border-border dark:bg-secondary dark:text-foreground dark:hover:bg-accent dark:hover:text-foreground"
                                              aria-label={assetTypesCollapsedInView ? "Expand assets" : "Collapse assets"}
                                              title={assetTypesCollapsedInView ? "Expand assets" : "Collapse assets"}
                                            >
                                              <ChevronDown className={`h-3.5 w-3.5 transition-transform ${assetTypesCollapsedInView ? "" : "rotate-180"}`} />
                                            </button>
                                            <div className="hidden" data-assets-actions-menu>
                                          <button
                                            type="button"
                                            onClick={() =>
                                              setAssetsActionsMenuOpen((previous) => {
                                                const next = !previous;
                                                if (!next) setAssetsActionsSubmenu(null);
                                                setFavoritesActionsMenuOpen(false);
                                                setCustomActionsMenuOpen(false);
                                                setAccountsActionsMenuOpen(false);
                                                return next;
                                              })
                                            }
                                            className={`inline-flex h-7 w-7 items-center justify-center rounded-md border transition-colors dark:border-border dark:bg-secondary dark:text-foreground dark:hover:bg-accent dark:hover:text-foreground ${
                                              assetsActionsMenuOpen
                                                ? "border-slate-300 bg-slate-200 text-slate-800"
                                                : "border-slate-200 bg-white text-slate-600 hover:bg-slate-200 hover:text-slate-900"
                                            }`}
                                            aria-label="More asset actions"
                                            title="More asset actions"
                                          >
                                            <Ellipsis className="h-3.5 w-3.5" />
                                          </button>
                                          {assetsActionsMenuOpen ? (
                                            <div className="absolute right-0 z-[70] mt-1 w-40 rounded-md border border-slate-200 bg-white p-1 shadow-md dark:border-border dark:bg-popover">
                                              <div className="relative">
                                                <button
                                                  type="button"
                                                  onClick={() =>
                                                    setAssetsActionsSubmenu((previous) => (previous === "filter" ? null : "filter"))
                                                  }
                                                  className={`flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-xs transition-colors ${
                                                    assetsActionsSubmenu === "filter"
                                                      ? "bg-slate-100 text-slate-900"
                                                      : "text-slate-700 hover:bg-slate-200 dark:text-foreground dark:hover:bg-accent"
                                                  }`}
                                                >
                                                  <span>Filter by</span>
                                                  <ChevronDown className="-rotate-90 h-3.5 w-3.5" />
                                                </button>
                                                {assetsActionsSubmenu === "filter" ? (
                                                  <div className="absolute left-full top-0 z-[80] ml-1 w-52 rounded-md border border-slate-200 bg-white p-2 shadow-md dark:border-border dark:bg-popover">
                                                    <label className="text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500" htmlFor="assets-filter-mode">
                                                      Asset type
                                                    </label>
                                                    <select
                                                      id="assets-filter-mode"
                                                      value={assetFilterMode}
                                                      onChange={(event) => setAssetFilterMode(event.target.value as typeof assetFilterMode)}
                                                      className="mt-1 w-full rounded-md border border-slate-200 bg-slate-50 px-2 py-1.5 text-xs text-slate-700 dark:border-border dark:bg-muted dark:text-foreground"
                                                    >
                                                      <option value="all">All assets</option>
                                                      <option value="system">System assets</option>
                                                      <option value="custom">Custom assets</option>
                                                    </select>
                                                  </div>
                                                ) : null}
                                              </div>
                                              <div className="relative">
                                                <button
                                                  type="button"
                                                  onClick={() =>
                                                    setAssetsActionsSubmenu((previous) => (previous === "sort" ? null : "sort"))
                                                  }
                                                  className={`flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-xs transition-colors ${
                                                    assetsActionsSubmenu === "sort"
                                                      ? "bg-slate-100 text-slate-900"
                                                      : "text-slate-700 hover:bg-slate-200 dark:text-foreground dark:hover:bg-accent"
                                                  }`}
                                                >
                                                  <span>Sort by</span>
                                                  <ChevronDown className="-rotate-90 h-3.5 w-3.5" />
                                                </button>
                                                {assetsActionsSubmenu === "sort" ? (
                                                  <div className="absolute left-full top-0 z-[80] ml-1 w-52 rounded-md border border-slate-200 bg-white p-2 shadow-md dark:border-border dark:bg-popover">
                                                    <label className="text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500" htmlFor="assets-sort-mode">
                                                      Sort
                                                    </label>
                                                    <select
                                                      id="assets-sort-mode"
                                                      value={assetSortMode}
                                                      onChange={(event) => setAssetSortMode(event.target.value as typeof assetSortMode)}
                                                      className="mt-1 w-full rounded-md border border-slate-200 bg-slate-50 px-2 py-1.5 text-xs text-slate-700 dark:border-border dark:bg-muted dark:text-foreground"
                                                    >
                                                      <option value="name_asc">Name (A-Z)</option>
                                                      <option value="name_desc">Name (Z-A)</option>
                                                    </select>
                                                  </div>
                                                ) : null}
                                              </div>
                                            </div>
                                          ) : null}
                                            </div>
                                          </>
                                        )}
                                      </div>
                                    </div>
                                    {isNavRearranging ? (
                                      <div className="mb-1 flex items-center gap-2 px-1">
                                        <button
                                          type="button"
                                          onClick={saveNavigationEdit}
                                          className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-emerald-300 bg-emerald-50 text-emerald-700 transition-colors hover:bg-emerald-100"
                                          aria-label="Save asset order"
                                          title="Save asset order"
                                        >
                                          <Check className="h-4 w-4" />
                                        </button>
                                        <button
                                          type="button"
                                          onClick={cancelNavigationEdit}
                                          className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-rose-300 bg-rose-50 text-rose-700 transition-colors hover:bg-rose-100"
                                          aria-label="Cancel asset rearrange"
                                          title="Cancel asset rearrange"
                                        >
                                          <X className="h-4 w-4" />
                                        </button>
                                      </div>
                                    ) : null}
                                    {!assetTypesCollapsedInView ? (
                                      <div className="space-y-0">
                                      {systemAssetTypes.map((entry) => {
                                          const key = entry.key;
                                          const assetType = entry.assetType;
                                          const buttonVisibilityKey = `asset:${key}`;
                                          const hidden = isNavButtonHidden(buttonVisibilityKey);
                                          if (!dashboardTilesEditMode && hidden) return null;
                                          return (
                                            <div
                                              key={key}
                                              data-nav-draggable={canEditButtonsForKind("asset") ? "true" : undefined}
                                              data-nav-target-kind="asset"
                                              data-nav-target-key={key}
                                              className={`flex items-center gap-1.5 rounded-lg border border-transparent px-0 py-0 transition-colors duration-100 ${
                                                isNavDragging("asset", key)
                                                  ? "opacity-0"
                                                  : navDropTarget?.kind === "asset" && navDropTarget.key === key
                                                    ? "ring-2 ring-slate-400"
                                                  : ""
                                              }`}
                                              onDragOver={(event) => handleNavTargetDragOver(event, "asset", key)}
                                              onDrop={(event) => handleNavTargetDrop(event, "asset", key)}
                                            >
                                              {canEditButtonsForKind("asset") ? (
                                                <>
                                                  <button
                                                    type="button"
                                                    draggable
                                                    onDragStart={(event) => handleNavDragStart(event, "asset", key)}
                                                    onDragEnd={handleNavDragEnd}
                                                    className={`inline-flex h-7 w-7 items-center justify-center rounded-full border border-border bg-transparent text-foreground transition-colors hover:bg-accent hover:text-accent-foreground ${
                                                      isNavDragging("asset", key) ? "cursor-grabbing" : "cursor-grab active:cursor-grabbing"
                                                    }`}
                                                    aria-label={`Reorder ${assetType.name}`}
                                                  >
                                                    <GripVertical className="h-3 w-3" />
                                                  </button>
                                                  <button
                                                    type="button"
                                                    onClick={() => toggleNavButtonVisibility(buttonVisibilityKey)}
                                                    className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-border bg-transparent text-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
                                                    aria-label={hidden ? `Show ${assetType.name}` : `Hide ${assetType.name}`}
                                                    title={hidden ? `Show ${assetType.name}` : `Hide ${assetType.name}`}
                                                  >
                                                    {hidden ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                                                  </button>
                                                </>
                                              ) : null}
                                              <button
                                                type="button"
                                                onClick={() => {
                                                  if (canEditButtonsForKind("asset")) return;
                                                  setActiveSidebarCategory(key);
                                                  setActiveSidebarLabel(assetType.name);
                                                }}
                                                className={`sidebar-nav-item relative flex-1 rounded-md px-2.5 py-2.5 text-left transition-colors ${
                                                  activeSidebarCategory === key
                                                    ? "sidebar-nav-item-active text-foreground dark:text-foreground"
                                                    : "text-slate-600 hover:bg-slate-200 hover:text-slate-900 dark:text-slate-200 dark:hover:bg-accent dark:hover:text-foreground"
                                                } ${hiddenInEditClass(hidden)}`}
                                              >
                                                <div className="flex items-center gap-2">
                                                  <ShapesIcon
                                                    className={`h-4 w-4 shrink-0 ${
                                                      activeSidebarCategory === key ? "text-foreground dark:text-foreground" : "text-muted-foreground dark:text-muted-foreground"
                                                    }`}
                                                    weight={activeSidebarCategory === key ? "fill" : "regular"}
                                                  />
                                                  <span className={`truncate text-sm ${activeSidebarCategory === key ? "font-medium" : "font-normal"}`}>{assetType.name}</span>
                                                </div>
                                                {activeSidebarCategory === key ? (
                                                  <span className="sidebar-active-indicator absolute bottom-1 right-0 top-1 w-1 rounded-full bg-current" />
                                                ) : null}
                                              </button>
                                            </div>
                                          );
                                        })}
                                      {customAssetTypes.length > 0 ? (
                                        <p className="pt-1 text-sm font-normal text-slate-500 dark:text-slate-300">
                                            Custom
                                        </p>
                                      ) : null}
                                      {customAssetTypes.map((entry) => {
                                          const key = entry.key;
                                          const assetType = entry.assetType;
                                          const buttonVisibilityKey = `asset:${key}`;
                                          const hidden = isNavButtonHidden(buttonVisibilityKey);
                                          if (!dashboardTilesEditMode && hidden) return null;
                                          return (
                                            <div
                                              key={key}
                                              data-nav-draggable={canEditButtonsForKind("asset") ? "true" : undefined}
                                              data-nav-target-kind="asset"
                                              data-nav-target-key={key}
                                              className={`flex items-center gap-1.5 rounded-lg border border-transparent px-0 py-0 transition-colors duration-100 ${
                                                isNavDragging("asset", key)
                                                  ? "opacity-0"
                                                  : navDropTarget?.kind === "asset" && navDropTarget.key === key
                                                    ? "ring-2 ring-slate-400"
                                                  : ""
                                              }`}
                                              onDragOver={(event) => handleNavTargetDragOver(event, "asset", key)}
                                              onDrop={(event) => handleNavTargetDrop(event, "asset", key)}
                                            >
                                              {canEditButtonsForKind("asset") ? (
                                                <>
                                                  <button
                                                    type="button"
                                                    draggable
                                                    onDragStart={(event) => handleNavDragStart(event, "asset", key)}
                                                    onDragEnd={handleNavDragEnd}
                                                    className={`inline-flex h-7 w-7 items-center justify-center rounded-full border border-border bg-transparent text-foreground transition-colors hover:bg-accent hover:text-accent-foreground ${
                                                      isNavDragging("asset", key) ? "cursor-grabbing" : "cursor-grab active:cursor-grabbing"
                                                    }`}
                                                    aria-label={`Reorder ${assetType.name}`}
                                                  >
                                                    <GripVertical className="h-3 w-3" />
                                                  </button>
                                                  <button
                                                    type="button"
                                                    onClick={() => toggleNavButtonVisibility(buttonVisibilityKey)}
                                                    className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-border bg-transparent text-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
                                                    aria-label={hidden ? `Show ${assetType.name}` : `Hide ${assetType.name}`}
                                                    title={hidden ? `Show ${assetType.name}` : `Hide ${assetType.name}`}
                                                  >
                                                    {hidden ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                                                  </button>
                                                </>
                                              ) : null}
                                              <button
                                                type="button"
                                                onClick={() => {
                                                  if (canEditButtonsForKind("asset")) return;
                                                  setActiveSidebarCategory(key);
                                                  setActiveSidebarLabel(assetType.name);
                                                }}
                                                className={`sidebar-nav-item relative flex-1 rounded-md px-2.5 py-2.5 text-left transition-colors ${
                                                  activeSidebarCategory === key
                                                    ? "sidebar-nav-item-active text-foreground dark:text-foreground"
                                                    : "text-slate-600 hover:bg-slate-200 hover:text-slate-900 dark:text-slate-200 dark:hover:bg-accent dark:hover:text-foreground"
                                                } ${hiddenInEditClass(hidden)}`}
                                              >
                                                <div className="flex items-center gap-2">
                                                  <ShapesIcon
                                                    className={`h-4 w-4 shrink-0 ${
                                                      activeSidebarCategory === key ? "text-foreground dark:text-foreground" : "text-muted-foreground dark:text-muted-foreground"
                                                    }`}
                                                    weight={activeSidebarCategory === key ? "fill" : "regular"}
                                                  />
                                                  <span className={`truncate text-sm ${activeSidebarCategory === key ? "font-medium" : "font-normal"}`}>{assetType.name}</span>
                                                </div>
                                                {activeSidebarCategory === key ? (
                                                  <span className="sidebar-active-indicator absolute bottom-1 right-0 top-1 w-1 rounded-full bg-current" />
                                                ) : null}
                                              </button>
                                            </div>
                                          );
                                        })}
                                      {!dashboardTilesEditMode && displayedAssetEntries.length === 0 ? (
                                        <div className="rounded-md border border-dashed border-blue-100 bg-slate-50 px-3 py-2 text-xs text-slate-500 dark:border-border dark:bg-card dark:text-slate-200">
                                          No asset types found.
                                        </div>
                                      ) : null}
                                      </div>
                                    ) : null}
                                  </div>
                                  ) : null}
                                  {shouldRenderDashboardTile("accounts") ? (
                                  <div
                                    data-dashboard-tile="accounts"
                                    draggable={false}
                                    onDragOver={(event) => handleDashboardTileDragOver(event, "accounts")}
                                    onDrop={(event) => handleDashboardTileDrop(event, "accounts")}
                                    onDragEnd={handleDashboardTileDragEnd}
                                    style={{ order: getDashboardTileOrder("accounts") }}
                                    className={`rounded-lg border border-slate-200 bg-slate-50 p-2.5 dark:border-border dark:bg-card ${
                                      navTileDropKey === "accounts" ? "ring-2 ring-slate-400 bg-slate-100/60 dark:bg-muted" : ""
                                    } ${navTileDragKey === "accounts" ? "opacity-0" : ""} ${hiddenInEditClass(
                                      isDashboardTileHidden("accounts"),
                                    )}`}
                                  >
                                    <div className="flex items-center justify-between px-1 py-1">
                                      <p className="text-sm font-normal text-slate-500 dark:text-foreground">Accounts</p>
                                      <div className="flex items-center gap-1">
                                        {isSortNavAndButtons ? (
                                          <>
                                            <button
                                              type="button"
                                              onClick={() => toggleDashboardTileVisibility("accounts")}
                                              className="inline-flex h-7 w-7 items-center justify-center rounded-md border border-border bg-transparent text-foreground transition-colors hover:text-foreground"
                                              aria-label={isDashboardTileHidden("accounts") ? "Show accounts tile" : "Hide accounts tile"}
                                              title={isDashboardTileHidden("accounts") ? "Show accounts tile" : "Hide accounts tile"}
                                            >
                                              {isDashboardTileHidden("accounts") ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                                            </button>
                                            <button
                                              type="button"
                                              draggable
                                              onDragStart={(event) => handleDashboardTileDragStart(event, "accounts")}
                                              onDragEnd={handleDashboardTileDragEnd}
                                              className="inline-flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-600 cursor-grab active:cursor-grabbing dark:border-border dark:bg-secondary dark:text-foreground"
                                              aria-label="Reorder accounts tile"
                                              title="Reorder accounts tile"
                                            >
                                              <GripVertical className="h-3.5 w-3.5" />
                                            </button>
                                          </>
                                        ) : (
                                          <>
                                            <button
                                              type="button"
                                              onClick={() => setAccountsCollapsed((previous) => !previous)}
                                              className="inline-flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 bg-white text-muted-foreground transition-colors hover:bg-slate-200 hover:text-foreground dark:border-border dark:bg-secondary dark:text-foreground dark:hover:bg-accent dark:hover:text-foreground"
                                              aria-label={accountsCollapsedInView ? "Expand account dashboards" : "Collapse account dashboards"}
                                              title={accountsCollapsedInView ? "Expand account dashboards" : "Collapse account dashboards"}
                                            >
                                              <ChevronDown className={`h-3.5 w-3.5 transition-transform ${accountsCollapsedInView ? "" : "rotate-180"}`} />
                                            </button>
                                            <div className="hidden" data-account-actions-menu>
                                              <button
                                                type="button"
                                                onClick={() =>
                                                  setAccountsActionsMenuOpen((previous) => {
                                                    const next = !previous;
                                                    if (!next) setAccountsActionsSubmenu(null);
                                                    setFavoritesActionsMenuOpen(false);
                                                    setAssetsActionsMenuOpen(false);
                                                    setCustomActionsMenuOpen(false);
                                                    return next;
                                                  })
                                                }
                                                className={`inline-flex h-7 w-7 items-center justify-center rounded-md border transition-colors dark:border-border dark:bg-secondary dark:text-foreground dark:hover:bg-accent dark:hover:text-foreground ${
                                                  accountsActionsMenuOpen
                                                    ? "border-slate-300 bg-slate-200 text-slate-800"
                                                    : "border-slate-200 bg-white text-slate-600 hover:bg-slate-200 hover:text-slate-900"
                                                }`}
                                                aria-label="Account actions"
                                                title="Account actions"
                                              >
                                                <Ellipsis className="h-3.5 w-3.5" />
                                              </button>
                                          {accountsActionsMenuOpen ? (
                                            <div className="pointer-events-auto absolute right-0 z-[70] mt-1 w-40 rounded-md border border-slate-200 bg-white p-1 shadow-md dark:border-border dark:bg-popover">
                                              <div className="relative">
                                                <button
                                                  type="button"
                                                  onClick={() =>
                                                    setAccountsActionsSubmenu((previous) => (previous === "filter" ? null : "filter"))
                                                  }
                                                  className={`flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-xs transition-colors ${
                                                    accountsActionsSubmenu === "filter"
                                                      ? "bg-slate-100 text-slate-900"
                                                      : "text-slate-700 hover:bg-slate-200 dark:text-foreground dark:hover:bg-accent"
                                                  }`}
                                                >
                                                  <span>Filter by</span>
                                                  <ChevronDown className="-rotate-90 h-3.5 w-3.5" />
                                                </button>
                                                {accountsActionsSubmenu === "filter" ? (
                                                  <div className="pointer-events-auto absolute left-full top-0 z-[80] ml-1 w-56 rounded-md border border-slate-200 bg-white p-2 shadow-md dark:border-border dark:bg-popover">
                                                    <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500">Account Type</p>
                                                    <div className="mt-1 flex flex-wrap gap-1">
                                                      <button
                                                        type="button"
                                                        onClick={() => setSelectedAccountTypeIds([])}
                                                        className={`rounded-md border px-2 py-1 text-xs transition-colors ${
                                                          selectedAccountTypeIds.length === 0
                                                            ? "border-slate-300 bg-slate-200 text-slate-900"
                                                            : "border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-200"
                                                        }`}
                                                      >
                                                        All
                                                      </button>
                                                      {(accountCreateOptions?.account_types ?? []).map((type) => {
                                                        const selected = selectedAccountTypeIds.includes(type.id);
                                                        return (
                                                          <button
                                                            key={`acct-type-filter-${type.id}`}
                                                            type="button"
                                                            onClick={() =>
                                                              setSelectedAccountTypeIds((previous) =>
                                                                previous.includes(type.id) ? previous.filter((id) => id !== type.id) : [...previous, type.id],
                                                              )
                                                            }
                                                            className={`rounded-md border px-2 py-1 text-xs transition-colors ${
                                                              selected
                                                                ? "border-slate-300 bg-slate-200 text-slate-900"
                                                                : "border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-200"
                                                            }`}
                                                          >
                                                            {type.name}
                                                          </button>
                                                        );
                                                      })}
                                                    </div>
                                                  </div>
                                                ) : null}
                                              </div>
                                              <div className="relative">
                                                <button
                                                  type="button"
                                                  onClick={() =>
                                                    setAccountsActionsSubmenu((previous) => (previous === "sort" ? null : "sort"))
                                                  }
                                                  className={`flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-xs transition-colors ${
                                                    accountsActionsSubmenu === "sort"
                                                      ? "bg-slate-100 text-slate-900"
                                                      : "text-slate-700 hover:bg-slate-200 dark:text-foreground dark:hover:bg-accent"
                                                  }`}
                                                >
                                                  <span>Sort by</span>
                                                  <ChevronDown className="-rotate-90 h-3.5 w-3.5" />
                                                </button>
                                                {accountsActionsSubmenu === "sort" ? (
                                                  <div className="pointer-events-auto absolute left-full top-0 z-[80] ml-1 w-56 rounded-md border border-slate-200 bg-white p-2 shadow-md dark:border-border dark:bg-popover">
                                                    <label className="text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500" htmlFor="accounts-sort-mode">
                                                      Sort
                                                    </label>
                                                    <select
                                                      id="accounts-sort-mode"
                                                      value={accountSortMode}
                                                      onChange={(event) => setAccountSortMode(event.target.value as typeof accountSortMode)}
                                                      className="mt-1 w-full rounded-md border border-slate-200 bg-slate-50 px-2 py-1.5 text-xs text-slate-700 dark:border-border dark:bg-muted dark:text-foreground"
                                                    >
                                                      <option value="name_asc">Name (A-Z)</option>
                                                      <option value="name_desc">Name (Z-A)</option>
                                                      <option value="type_asc">Account Type (A-Z)</option>
                                                      <option value="value_desc">Account value (High-Low)</option>
                                                      <option value="value_asc">Account value (Low-High)</option>
                                                    </select>
                                                    <p className="mt-1 text-[10px] text-slate-400">
                                                      Value sort uses account value when available, otherwise holdings count.
                                                    </p>
                                                  </div>
                                                ) : null}
                                              </div>
                                            </div>
                                          ) : null}
                                            </div>
                                          </>
                                        )}
                                      </div>
                                    </div>
                                    {isNavRearranging ? (
                                      <div className="mb-1 flex items-center gap-2 px-1">
                                        <button
                                          type="button"
                                          onClick={() => {
                                            saveNavigationEdit();
                                            setAccountsActionsMenuOpen(false);
                                            setAccountsActionsSubmenu(null);
                                          }}
                                          className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-emerald-300 bg-emerald-50 text-emerald-700 transition-colors hover:bg-emerald-100"
                                          aria-label="Save account order"
                                          title="Save account order"
                                        >
                                          <Check className="h-4 w-4" />
                                        </button>
                                        <button
                                          type="button"
                                          onClick={cancelNavigationEdit}
                                          className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-rose-300 bg-rose-50 text-rose-700 transition-colors hover:bg-rose-100"
                                          aria-label="Cancel account rearrange"
                                          title="Cancel account rearrange"
                                        >
                                          <X className="h-4 w-4" />
                                        </button>
                                      </div>
                                    ) : null}
                                    {!accountsCollapsedInView ? (
                                      <div className="mt-0 space-y-0">
                                      {displayedAccountEntries.map((entry) => {
                                          const account = entry.account;
                                          const key = entry.key;
                                          const typeName = accountTypeNameById.get(account.account_type);
                                          const buttonVisibilityKey = `account:${key}`;
                                          const hidden = isNavButtonHidden(buttonVisibilityKey);
                                          if (!dashboardTilesEditMode && hidden) return null;
                                          return (
                                            <div
                                              key={account.id}
                                              data-nav-draggable={canEditButtonsForKind("account") ? "true" : undefined}
                                              data-nav-target-kind="account"
                                              data-nav-target-key={key}
                                              className={`flex items-center gap-1.5 rounded-lg border border-transparent px-0 py-0 transition-colors duration-100 ${
                                                isNavDragging("account", key)
                                                  ? "opacity-0"
                                                  : navDropTarget?.kind === "account" && navDropTarget.key === key
                                                    ? "ring-2 ring-slate-400"
                                                  : ""
                                              }`}
                                              onDragOver={(event) => handleNavTargetDragOver(event, "account", key)}
                                              onDrop={(event) => handleNavTargetDrop(event, "account", key)}
                                            >
                                              {canEditButtonsForKind("account") ? (
                                                <>
                                                  <button
                                                    type="button"
                                                    draggable
                                                    onDragStart={(event) => handleNavDragStart(event, "account", key)}
                                                    onDragEnd={handleNavDragEnd}
                                                    className={`inline-flex h-7 w-7 items-center justify-center rounded-full border border-border bg-transparent text-foreground transition-colors hover:bg-accent hover:text-accent-foreground ${
                                                      isNavDragging("account", key) ? "cursor-grabbing" : "cursor-grab active:cursor-grabbing"
                                                    }`}
                                                    aria-label={`Reorder ${account.name}`}
                                                  >
                                                    <GripVertical className="h-3 w-3" />
                                                  </button>
                                                  <button
                                                    type="button"
                                                    onClick={() => toggleNavButtonVisibility(buttonVisibilityKey)}
                                                    className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-border bg-transparent text-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
                                                    aria-label={hidden ? `Show ${account.name}` : `Hide ${account.name}`}
                                                    title={hidden ? `Show ${account.name}` : `Hide ${account.name}`}
                                                  >
                                                    {hidden ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                                                  </button>
                                                </>
                                              ) : null}
                                              <button
                                                type="button"
                                                onClick={() => {
                                                  if (canEditButtonsForKind("account")) return;
                                                  setActiveSidebarCategory(key);
                                                  setActiveSidebarLabel(account.name);
                                                }}
                                                className={`sidebar-nav-item relative flex-1 rounded-md px-2.5 py-2.5 text-left transition-colors ${
                                                  activeSidebarCategory === key
                                                    ? "sidebar-nav-item-active text-foreground dark:text-foreground"
                                                    : "text-slate-600 hover:bg-slate-200 hover:text-slate-900 dark:text-slate-200 dark:hover:bg-accent dark:hover:text-foreground"
                                                } ${hiddenInEditClass(hidden)}`}
                                              >
                                                <div className="flex items-start gap-2">
                                                  <CurrencyDollarSimpleIcon
                                                    className={`mt-0.5 h-4 w-4 shrink-0 ${
                                                      activeSidebarCategory === key ? "text-foreground dark:text-foreground" : "text-muted-foreground dark:text-muted-foreground"
                                                    }`}
                                                    weight={activeSidebarCategory === key ? "fill" : "regular"}
                                                  />
                                                  <div className="min-w-0">
                                                    <p className={`truncate text-sm ${activeSidebarCategory === key ? "font-medium" : "font-normal"}`}>{account.name}</p>
                                                    {typeName ? <p className="truncate text-[11px] text-muted-foreground dark:text-muted-foreground">{typeName}</p> : null}
                                                  </div>
                                                </div>
                                                {activeSidebarCategory === key ? (
                                                  <span className="sidebar-active-indicator absolute bottom-1 right-0 top-1 w-1 rounded-full bg-current" />
                                                ) : null}
                                              </button>
                                            </div>
                                          );
                                      })}
                                      {!dashboardTilesEditMode && displayedAccountEntries.length === 0 ? (
                                        <div className="rounded-md border border-dashed border-blue-100 bg-slate-50 px-3 py-2 text-xs text-slate-500 dark:border-border dark:bg-card dark:text-slate-200">
                                          No accounts found.
                                        </div>
                                      ) : null}
                                      </div>
                                    ) : null}
                                  </div>
                                  ) : null}
                                  {shouldRenderDashboardTile("custom") ? (
                                  <div
                                    data-dashboard-tile="custom"
                                    draggable={false}
                                    onDragOver={(event) => handleDashboardTileDragOver(event, "custom")}
                                    onDrop={(event) => handleDashboardTileDrop(event, "custom")}
                                    onDragEnd={handleDashboardTileDragEnd}
                                    style={{ order: getDashboardTileOrder("custom") }}
                                    className={`rounded-lg border border-slate-200 bg-slate-50 p-2.5 dark:border-border dark:bg-card ${
                                      navTileDropKey === "custom" ? "ring-2 ring-slate-400 bg-slate-100/60 dark:bg-muted" : ""
                                    } ${navTileDragKey === "custom" ? "opacity-0" : ""} ${hiddenInEditClass(isDashboardTileHidden("custom"))}`}
                                  >
                                    <div className="flex items-center justify-between px-1 py-1">
                                      <p className="text-sm font-normal text-slate-500 dark:text-foreground">Custom Dashboards</p>
                                      <div className="flex items-center gap-1">
                                        {dashboardTilesEditMode ? (
                                          <>
                                            <button
                                              type="button"
                                              onClick={() => toggleDashboardTileVisibility("custom")}
                                              className="inline-flex h-7 w-7 items-center justify-center rounded-md border border-border bg-transparent text-foreground transition-colors hover:text-foreground"
                                              aria-label={isDashboardTileHidden("custom") ? "Show custom dashboards tile" : "Hide custom dashboards tile"}
                                              title={isDashboardTileHidden("custom") ? "Show custom dashboards tile" : "Hide custom dashboards tile"}
                                            >
                                              {isDashboardTileHidden("custom") ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                                            </button>
                                            <button
                                              type="button"
                                              draggable
                                              onDragStart={(event) => handleDashboardTileDragStart(event, "custom")}
                                              onDragEnd={handleDashboardTileDragEnd}
                                              className="inline-flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 bg-white text-muted-foreground transition-colors hover:bg-slate-200 hover:text-foreground dark:border-border dark:bg-secondary dark:text-foreground dark:hover:bg-accent cursor-grab active:cursor-grabbing"
                                              aria-label="Reorder custom dashboards tile"
                                              title="Reorder custom dashboards tile"
                                            >
                                              <GripVertical className="h-3.5 w-3.5" />
                                            </button>
                                          </>
                                        ) : (
                                          <>
                                            <button
                                              type="button"
                                              onClick={() => setCustomDashboardsCollapsed((previous) => !previous)}
                                              className="inline-flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 bg-white text-muted-foreground transition-colors hover:bg-slate-200 hover:text-foreground dark:border-border dark:bg-secondary dark:text-foreground dark:hover:bg-accent dark:hover:text-foreground"
                                              aria-label={customDashboardsCollapsedInView ? "Expand custom dashboards" : "Collapse custom dashboards"}
                                              title={customDashboardsCollapsedInView ? "Expand custom dashboards" : "Collapse custom dashboards"}
                                            >
                                              <ChevronDown className={`h-3.5 w-3.5 transition-transform ${customDashboardsCollapsedInView ? "" : "rotate-180"}`} />
                                            </button>
                                            <div className="hidden" data-custom-actions-menu>
                                          <button
                                            type="button"
                                            onClick={() =>
                                              setCustomActionsMenuOpen((previous) => {
                                                const next = !previous;
                                                if (!next) setCustomActionsSubmenu(null);
                                                setFavoritesActionsMenuOpen(false);
                                                setAssetsActionsMenuOpen(false);
                                                setAccountsActionsMenuOpen(false);
                                                return next;
                                              })
                                            }
                                            className={`inline-flex h-7 w-7 items-center justify-center rounded-md border transition-colors dark:border-border dark:bg-secondary dark:text-foreground dark:hover:bg-accent dark:hover:text-foreground ${
                                              customActionsMenuOpen
                                                ? "border-slate-300 bg-slate-200 text-slate-800"
                                                : "border-slate-200 bg-white text-slate-600 hover:bg-slate-200 hover:text-slate-900"
                                            }`}
                                            aria-label="More custom actions"
                                            title="More custom actions"
                                          >
                                            <Ellipsis className="h-3.5 w-3.5" />
                                          </button>
                                          {customActionsMenuOpen ? (
                                            <div className="absolute right-0 z-[70] mt-1 w-40 rounded-md border border-slate-200 bg-white p-1 shadow-md dark:border-border dark:bg-popover">
                                              <div className="relative">
                                                <button
                                                  type="button"
                                                  onClick={() =>
                                                    setCustomActionsSubmenu((previous) => (previous === "filter" ? null : "filter"))
                                                  }
                                                  className={`flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-xs transition-colors ${
                                                    customActionsSubmenu === "filter"
                                                      ? "bg-slate-100 text-slate-900"
                                                      : "text-slate-700 hover:bg-slate-200 dark:text-foreground dark:hover:bg-accent"
                                                  }`}
                                                >
                                                  <span>Filter by</span>
                                                  <ChevronDown className="-rotate-90 h-3.5 w-3.5" />
                                                </button>
                                                {customActionsSubmenu === "filter" ? (
                                                  <div className="absolute left-full top-0 z-[80] ml-1 w-52 rounded-md border border-slate-200 bg-white p-2 shadow-md dark:border-border dark:bg-popover">
                                                    <label className="text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500" htmlFor="custom-filter-mode">
                                                      Scope
                                                    </label>
                                                    <select
                                                      id="custom-filter-mode"
                                                      value={customFilterMode}
                                                      onChange={(event) => setCustomFilterMode(event.target.value as typeof customFilterMode)}
                                                      className="mt-1 w-full rounded-md border border-slate-200 bg-slate-50 px-2 py-1.5 text-xs text-slate-700 dark:border-border dark:bg-muted dark:text-foreground"
                                                    >
                                                      <option value="all">All custom dashboards</option>
                                                      <option value="portfolio">Portfolio dashboards</option>
                                                      <option value="accounts">Account dashboards</option>
                                                    </select>
                                                  </div>
                                                ) : null}
                                              </div>
                                              <div className="relative">
                                                <button
                                                  type="button"
                                                  onClick={() =>
                                                    setCustomActionsSubmenu((previous) => (previous === "sort" ? null : "sort"))
                                                  }
                                                  className={`flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-xs transition-colors ${
                                                    customActionsSubmenu === "sort"
                                                      ? "bg-slate-100 text-slate-900"
                                                      : "text-slate-700 hover:bg-slate-200 dark:text-foreground dark:hover:bg-accent"
                                                  }`}
                                                >
                                                  <span>Sort by</span>
                                                  <ChevronDown className="-rotate-90 h-3.5 w-3.5" />
                                                </button>
                                                {customActionsSubmenu === "sort" ? (
                                                  <div className="absolute left-full top-0 z-[80] ml-1 w-52 rounded-md border border-slate-200 bg-white p-2 shadow-md dark:border-border dark:bg-popover">
                                                    <label className="text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500" htmlFor="custom-sort-mode">
                                                      Sort
                                                    </label>
                                                    <select
                                                      id="custom-sort-mode"
                                                      value={customSortMode}
                                                      onChange={(event) => setCustomSortMode(event.target.value as typeof customSortMode)}
                                                      className="mt-1 w-full rounded-md border border-slate-200 bg-slate-50 px-2 py-1.5 text-xs text-slate-700 dark:border-border dark:bg-muted dark:text-foreground"
                                                    >
                                                      <option value="recent">Recently updated</option>
                                                      <option value="name_asc">Name (A-Z)</option>
                                                      <option value="name_desc">Name (Z-A)</option>
                                                    </select>
                                                  </div>
                                                ) : null}
                                              </div>
                                            </div>
                                          ) : null}
                                            </div>
                                          </>
                                        )}
                                      </div>
                                    </div>
                                    {isNavRearranging ? (
                                      <div className="mb-1 flex items-center gap-2 px-1">
                                        <button
                                          type="button"
                                          onClick={saveNavigationEdit}
                                          className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-emerald-300 bg-emerald-50 text-emerald-700 transition-colors hover:bg-emerald-100"
                                          aria-label="Save nav and button order"
                                          title="Save nav and button order"
                                        >
                                          <Check className="h-4 w-4" />
                                        </button>
                                        <button
                                          type="button"
                                          onClick={cancelNavigationEdit}
                                          className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-rose-300 bg-rose-50 text-rose-700 transition-colors hover:bg-rose-100"
                                          aria-label="Cancel nav and button rearrange"
                                          title="Cancel nav and button rearrange"
                                        >
                                          <X className="h-4 w-4" />
                                        </button>
                                      </div>
                                    ) : null}
                                    {!dashboardTilesEditMode && !customDashboardsCollapsedInView && shouldRenderNavButton("action:custom-create") ? (
                                      <button
                                        type="button"
                                        className={`sidebar-add-dashed w-full rounded-md border border-dashed border-slate-300 px-2.5 py-3 text-left text-sm font-normal text-slate-500 transition-colors hover:bg-slate-200 hover:text-slate-700 dark:border-border dark:text-slate-200 dark:hover:bg-accent dark:hover:text-foreground ${hiddenInEditClass(
                                          isNavButtonHidden("action:custom-create"),
                                        )}`}
                                      >
                                        + Create Custom Dashboard
                                      </button>
                                    ) : null}
                                  </div>
                                  ) : null}
                              </div>
                            </CardContent>
                          </div>
                </CardContent>
              </Card>
              <div
                className={`${isNavRearranging || dashboardTilesEditMode ? "pointer-events-none select-none" : ""} space-y-4`}
              >
              <div className="space-y-4">
              {activeAppShellSection !== "portfolio" && activeAppShellSection !== "addAccount" ? (
                <div className="grid grid-cols-1 gap-3">
                  <Card className="rounded-lg border border-background bg-background shadow-none dark:border-background dark:bg-background dark:text-foreground">
                      <CardContent className="h-[92px] px-4 py-2">
                        <div className="flex h-full items-center justify-between gap-3">
                          <h1 className="font-sans text-[2rem] font-semibold tracking-tight text-foreground dark:text-foreground">
                            {`${activeSidebarLabel} Dashboard`}
                          </h1>
                          {!isAssetsLiabilitiesDashboard ? (
                            <div className="flex items-center gap-2">
                              <div className="relative" data-dashboard-menu>
                                <button
                                  type="button"
                                  onClick={() => {
                                    setSettingsMenuOpen((previous) => !previous);
                                  }}
                                  className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-blue-100 bg-white text-muted-foreground transition-colors hover:bg-blue-50 hover:text-foreground dark:border-border dark:bg-secondary dark:text-foreground dark:hover:bg-accent dark:hover:text-foreground"
                                >
                                  <Settings className="h-5 w-5" />
                                </button>
                                {settingsMenuOpen ? (
                                  <div className="absolute right-0 z-50 mt-2 w-40 rounded-xl border border-border bg-white p-1 shadow-lg dark:border-border dark:bg-popover">
                                    {!isEditing ? (
                                      <button
                                        type="button"
                                        onClick={() => {
                                          setIsEditing(true);
                                          setSettingsMenuOpen(false);
                                        }}
                                        className="w-full rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-secondary/80 hover:text-foreground"
                                      >
                                        Edit Dashboard
                                      </button>
                                    ) : (
                                      <div className="rounded px-2 py-1.5 text-xs text-muted-foreground">
                                        Use the edit toolbar above the dashboard.
                                      </div>
                                    )}
                                  </div>
                                ) : null}
                              </div>
                            </div>
                          ) : null}
                        </div>
                      </CardContent>
                    </Card>
                 </div>
              ) : null}
              {!isEditing ? (
                <Card className="overflow-visible border border-background bg-background shadow-none dark:border-background dark:bg-background">
                  <CardContent className={activeAppShellSection === "portfolio" || activeAppShellSection === "addAccount" ? "min-h-[74vh] p-0" : "min-h-[74vh] px-5 pb-5 pt-2"}>
                    {activeAppShellSection === "portfolio" ? (
                      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
                      <div className="space-y-4 rounded-xl border border-background bg-background p-4">
                        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                          <div>
                            <p className="text-3xl font-bold tracking-tight text-foreground">$98,056</p>
                          </div>
                        </div>

                        <div className="px-1 pb-1 pt-2">
                          <div className="h-[240px] w-full">
                            <svg viewBox="0 0 1200 240" className="h-full w-full" preserveAspectRatio="none" aria-hidden="true">
                              <defs>
                                <linearGradient id="portfolio-placeholder-fill" x1="0" x2="0" y1="0" y2="1">
                                  <stop offset="0%" stopColor="rgb(34 197 94 / 0.16)" />
                                  <stop offset="100%" stopColor="rgb(34 197 94 / 0)" />
                                </linearGradient>
                              </defs>
                              <path
                                d="M0 210 L0 178 L55 178 L82 176 L108 168 L138 145 L162 142 L190 126 L214 129 L242 112 L270 118 L300 108 L334 110 L364 101 L398 105 L432 92 L470 95 L504 89 L538 73 L570 58 L605 54 L636 60 L670 50 L690 157 L728 155 L760 151 L796 141 L832 149 L866 144 L902 140 L934 132 L970 149 L1003 142 L1038 136 L1074 129 L1106 137 L1140 128 L1180 120 L1200 118 L1200 210 Z"
                                fill="url(#portfolio-placeholder-fill)"
                              />
                              <path
                                d="M0 178 L55 178 L82 176 L108 168 L138 145 L162 142 L190 126 L214 129 L242 112 L270 118 L300 108 L334 110 L364 101 L398 105 L432 92 L470 95 L504 89 L538 73 L570 58 L605 54 L636 60 L670 50 L690 157 L728 155 L760 151 L796 141 L832 149 L866 144 L902 140 L934 132 L970 149 L1003 142 L1038 136 L1074 129 L1106 137 L1140 128 L1180 120 L1200 118"
                                fill="none"
                                stroke="#16a34a"
                                strokeWidth="2.2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                              />
                              <line x1="0" y1="210" x2="1200" y2="210" stroke="rgb(148 163 184 / 0.35)" strokeWidth="1" />
                            </svg>
                          </div>
                          <div className="mt-3 flex items-center justify-between gap-4 border-t border-slate-200/80 pt-3">
                            <div className="flex flex-wrap items-center gap-2 text-sm font-semibold text-slate-500">
                              <span>1M</span>
                              <span>3M</span>
                              <span>6M</span>
                              <span>YTD</span>
                              <span>1Y</span>
                              <span className="rounded-md bg-slate-100 px-2 py-1 text-slate-700">ALL</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm font-semibold text-slate-500">
                              <span className="rounded-md bg-slate-100 px-2 py-1 text-slate-700">Value</span>
                              <span>Returns</span>
                            </div>
                          </div>
                          <div className="mt-4 flex justify-start">
                            <div className="inline-flex items-center rounded-full border border-slate-200 bg-white p-1 shadow-[0_4px_10px_rgba(15,23,42,0.04)]">
                              <button
                                type="button"
                                onClick={() => setPortfolioGroupingMode("account")}
                                className={`rounded-full px-4 py-1.5 text-sm font-semibold transition-colors ${
                                  portfolioGroupingMode === "account" ? "bg-foreground text-background" : "text-slate-600 hover:text-slate-900"
                                }`}
                              >
                                Accounts
                              </button>
                              <button
                                type="button"
                                onClick={() => setPortfolioGroupingMode("asset")}
                                className={`rounded-full px-4 py-1.5 text-sm font-semibold transition-colors ${
                                  portfolioGroupingMode === "asset" ? "bg-foreground text-background" : "text-slate-600 hover:text-slate-900"
                                }`}
                              >
                                Asset Types
                              </button>
                            </div>
                          </div>
                        </div>

                        {portfolioHoldingsNotice ? (
                          <div className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-muted-foreground">
                            {portfolioHoldingsNotice}
                          </div>
                        ) : null}

                        {isPortfolioHoldingsLoading ? (
                          <div className="grid gap-4 xl:grid-cols-2">
                            {Array.from({ length: 2 }, (_, index) => (
                              <div key={`portfolio-loading-${index}`} className="rounded-xl border border-slate-200 bg-white p-4">
                                <div className="h-5 w-32 animate-pulse rounded bg-slate-200" />
                                <div className="mt-4 space-y-2">
                                  {Array.from({ length: 5 }, (_, row) => (
                                    <div key={`portfolio-loading-row-${index}-${row}`} className="h-10 animate-pulse rounded-lg bg-slate-100" />
                                  ))}
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : portfolioGroupedSections.length === 0 ? (
                          <div className="flex min-h-[calc(100vh-12rem)] items-center justify-center rounded-xl border border-dashed border-slate-300 bg-white text-sm text-muted-foreground">
                            No assets or liabilities have been added yet. Use Add Assets to start building your portfolio.
                          </div>
                        ) : (
                          <div className="space-y-4">
                            {portfolioGroupedSections.map((group) => (
                              <div key={`portfolio-group-${group.key}`} className="overflow-hidden rounded-xl border border-slate-200 bg-white">
                                <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
                                  <div>
                                    <h3 className="text-base font-semibold text-foreground">{group.label}</h3>
                                    <p className="text-sm text-muted-foreground">{group.subtitle}</p>
                                  </div>
                                </div>
                                <div className="overflow-x-auto">
                                  <table className="min-w-full border-collapse">
                                    <thead>
                                      <tr className="border-b border-slate-200 bg-slate-50/80 text-left text-xs uppercase tracking-[0.12em] text-slate-500">
                                        <th className="px-4 py-3 font-medium">Asset</th>
                                        <th className="px-4 py-3 font-medium">Ticker</th>
                                        <th className="px-4 py-3 font-medium">{portfolioGroupingMode === "asset" ? "Account" : "Asset Type"}</th>
                                        <th className="px-4 py-3 font-medium">Quantity</th>
                                        <th className="px-4 py-3 font-medium">Avg. Cost</th>
                                        {portfolioDetailMode === "detailed" ? (
                                          <>
                                            <th className="px-4 py-3 font-medium">Sector</th>
                                            <th className="px-4 py-3 font-medium">Dividends</th>
                                            <th className="px-4 py-3 font-medium">Cash Flow</th>
                                          </>
                                        ) : null}
                                        <th className="px-4 py-3 font-medium">Updated</th>
                                      </tr>
                                    </thead>
                                    <tbody>
                                      {group.rows.map((holding) => (
                                        <tr key={`portfolio-holding-${holding.id}`} className="border-b border-slate-100 text-sm last:border-b-0">
                                          <td className="px-4 py-3 font-medium text-foreground">{holding.asset_display_name}</td>
                                          <td className="px-4 py-3 text-muted-foreground">{holding.original_ticker || "—"}</td>
                                          <td className="px-4 py-3 text-muted-foreground">
                                            {portfolioGroupingMode === "asset"
                                              ? holding.account_name
                                              : assetTypeNameBySlug.get(holding.asset_type) ?? formatSlugLabel(holding.asset_type)}
                                          </td>
                                          <td className="px-4 py-3 text-muted-foreground">{formatNumber(holding.quantity, { maximumFractionDigits: 4 })}</td>
                                          <td className="px-4 py-3 text-muted-foreground">{formatCurrency(holding.average_purchase_price)}</td>
                                          {portfolioDetailMode === "detailed" ? (
                                            <>
                                              <td className="px-4 py-3 text-muted-foreground">—</td>
                                              <td className="px-4 py-3 text-muted-foreground">—</td>
                                              <td className="px-4 py-3 text-muted-foreground">—</td>
                                            </>
                                          ) : null}
                                          <td className="px-4 py-3 text-muted-foreground">{formatDateLabel(holding.updated_at)}</td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="rounded-xl border border-slate-200 bg-white p-4">
                        <div className="flex min-h-[240px] flex-col">
                          <p className="text-sm font-medium text-slate-900">New Tile</p>
                        </div>
                      </div>
                      </div>
                    ) : activeAppShellSection === "holdings" ? (
                      <div className="flex min-h-[74vh] items-center justify-center rounded-xl border border-slate-200 bg-white text-sm text-muted-foreground">
                        Holdings view coming next.
                      </div>
                    ) : activeAppShellSection === "accounts" ? (
                      <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                          <p className="text-lg font-semibold text-foreground">Accounts</p>
                          <div className="flex items-center gap-2">
                            <label htmlFor="accounts-shell-sort" className="text-sm font-medium text-slate-500">
                              Sort
                            </label>
                            <select
                              id="accounts-shell-sort"
                              value={accountsShellSortMode}
                              onChange={(event) => setAccountsShellSortMode(event.target.value as ShellSortMode)}
                              className="rounded-full border border-slate-200 bg-white px-3 py-2 text-sm text-foreground"
                            >
                              <option value="value_desc">Value (High-Low)</option>
                              <option value="value_asc">Value (Low-High)</option>
                              <option value="name_asc">Alphabetical (A-Z)</option>
                              <option value="name_desc">Alphabetical (Z-A)</option>
                            </select>
                          </div>
                        </div>
                        <div className="space-y-3">
                          {accountsShellGroups.length === 0 ? (
                            <div className="rounded-xl border border-dashed border-slate-300 px-4 py-10 text-center text-sm text-muted-foreground">
                              No accounts yet.
                            </div>
                          ) : (
                            accountsShellGroups.map((group) => {
                              const collapsed = collapsedAccountTypeGroups.includes(group.key);
                              return (
                                <div key={group.key} className="overflow-hidden rounded-xl border border-slate-200 bg-slate-50/60">
                                  <button
                                    type="button"
                                    onClick={() =>
                                      setCollapsedAccountTypeGroups((previous) =>
                                        previous.includes(group.key) ? previous.filter((key) => key !== group.key) : [...previous, group.key],
                                      )
                                    }
                                    className="flex w-full items-center justify-between gap-4 px-4 py-4 text-left"
                                  >
                                    <div>
                                      <p className="text-base font-semibold text-foreground">{group.label}</p>
                                      <p className="text-sm text-muted-foreground">{group.items.length} accounts</p>
                                    </div>
                                    <div className="flex items-center gap-3">
                                      <p className="text-base font-semibold text-foreground">{formatCurrency(group.totalValue)}</p>
                                      <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${collapsed ? "" : "rotate-180"}`} />
                                    </div>
                                  </button>
                                  {!collapsed ? (
                                    <div className="border-t border-slate-200 bg-white">
                                      {group.items.map((item) => (
                                        <div key={item.key} className="flex items-center justify-between gap-4 px-4 py-3 text-sm">
                                          <div className="min-w-0">
                                            <p className="truncate font-medium text-foreground">{item.label}</p>
                                            {item.subtitle ? <p className="truncate text-xs text-muted-foreground">{item.subtitle}</p> : null}
                                          </div>
                                          <p className="shrink-0 font-medium text-foreground">{formatCurrency(item.value)}</p>
                                        </div>
                                      ))}
                                    </div>
                                  ) : null}
                                </div>
                              );
                            })
                          )}
                        </div>
                      </div>
                    ) : activeAppShellSection === "addAccount" ? (
                      <div className="space-y-6 rounded-xl border border-slate-200 bg-white p-6">
                        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
                          <div className="space-y-3">
                            <button
                              type="button"
                              onClick={() => setActiveAppShellSection("accounts")}
                              className="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 transition-colors hover:text-foreground"
                            >
                              <ChevronLeft className="h-4 w-4" />
                              <span>Back to Accounts</span>
                            </button>
                            <div className="space-y-2">
                              <h2 className="text-3xl font-semibold tracking-tight text-foreground">Which Account would you like to add?</h2>
                              <p className="max-w-2xl text-sm text-muted-foreground">
                                Choose a built-in account type to get started, or create a custom account type for something more specific.
                              </p>
                            </div>
                          </div>
                          <div className="rounded-3xl border border-slate-200 bg-slate-50 px-6 py-5">
                            <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-slate-800 shadow-sm">
                              <WalletSolidIcon className="h-7 w-7" />
                            </div>
                          </div>
                        </div>
                        {addAccountTypeTiles.length === 0 ? (
                          <div className="rounded-xl border border-dashed border-slate-300 px-4 py-10 text-center text-sm text-muted-foreground">
                            No account types available yet.
                          </div>
                        ) : (
                          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                            {addAccountTypeTiles.map((accountType) => (
                              <button
                                key={`add-account-type-${accountType.id}`}
                                type="button"
                                className="group rounded-2xl border border-slate-200 bg-white p-5 text-left shadow-[0_6px_18px_rgba(15,23,42,0.04)] transition-all hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-[0_10px_22px_rgba(15,23,42,0.08)]"
                              >
                                <div className="flex items-start justify-between gap-3">
                                  <div className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-100 text-slate-700 transition-colors group-hover:bg-slate-900 group-hover:text-white">
                                    <WalletOutlineIcon className="h-5 w-5" />
                                  </div>
                                  {!accountType.is_system ? (
                                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500">
                                      Custom
                                    </span>
                                  ) : null}
                                </div>
                                <div className="mt-5">
                                  <p className="text-base font-semibold text-foreground">{accountType.name}</p>
                                  {accountType.description ? (
                                    <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{accountType.description}</p>
                                  ) : (
                                    <p className="mt-1 text-sm text-muted-foreground">
                                      {accountType.allowed_asset_type_slugs.length > 0
                                        ? accountType.allowed_asset_type_slugs.map(formatSlugLabel).join(", ")
                                        : "General account type"}
                                    </p>
                                  )}
                                </div>
                              </button>
                            ))}
                            <button
                              type="button"
                              className="group rounded-2xl border border-slate-300 bg-slate-100/70 p-5 text-left shadow-[0_6px_18px_rgba(15,23,42,0.03)] transition-all hover:-translate-y-0.5 hover:border-slate-400 hover:bg-slate-200/70"
                            >
                              <div className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-slate-700 shadow-sm">
                                <Plus className="h-5 w-5" />
                              </div>
                              <div className="mt-5">
                                <p className="text-base font-semibold text-foreground">Create New Account Type</p>
                                <p className="mt-1 text-sm text-muted-foreground">Add a custom account type for a workflow that does not fit the built-in options.</p>
                              </div>
                            </button>
                          </div>
                        )}
                      </div>
                    ) : activeAppShellSection === "assetTypes" ? (
                      <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                          <p className="text-lg font-semibold text-foreground">Asset Types</p>
                          <div className="flex items-center gap-2">
                            <label htmlFor="asset-types-shell-sort" className="text-sm font-medium text-slate-500">
                              Sort
                            </label>
                            <select
                              id="asset-types-shell-sort"
                              value={assetTypesShellSortMode}
                              onChange={(event) => setAssetTypesShellSortMode(event.target.value as ShellSortMode)}
                              className="rounded-full border border-slate-200 bg-white px-3 py-2 text-sm text-foreground"
                            >
                              <option value="value_desc">Value (High-Low)</option>
                              <option value="value_asc">Value (Low-High)</option>
                              <option value="name_asc">Alphabetical (A-Z)</option>
                              <option value="name_desc">Alphabetical (Z-A)</option>
                            </select>
                          </div>
                        </div>
                        <div className="space-y-3">
                          {assetTypesShellGroups.length === 0 ? (
                            <div className="rounded-xl border border-dashed border-slate-300 px-4 py-10 text-center text-sm text-muted-foreground">
                              No asset types yet.
                            </div>
                          ) : (
                            assetTypesShellGroups.map((group) => {
                              const collapsed = collapsedAssetTypeGroups.includes(group.key);
                              return (
                                <div key={group.key} className="overflow-hidden rounded-xl border border-slate-200 bg-slate-50/60">
                                  <button
                                    type="button"
                                    onClick={() =>
                                      setCollapsedAssetTypeGroups((previous) =>
                                        previous.includes(group.key) ? previous.filter((key) => key !== group.key) : [...previous, group.key],
                                      )
                                    }
                                    className="flex w-full items-center justify-between gap-4 px-4 py-4 text-left"
                                  >
                                    <div>
                                      <p className="text-base font-semibold text-foreground">{group.label}</p>
                                      <p className="text-sm text-muted-foreground">{group.items.length} assets</p>
                                    </div>
                                    <div className="flex items-center gap-3">
                                      <p className="text-base font-semibold text-foreground">{formatCurrency(group.totalValue)}</p>
                                      <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${collapsed ? "" : "rotate-180"}`} />
                                    </div>
                                  </button>
                                  {!collapsed ? (
                                    <div className="border-t border-slate-200 bg-white">
                                      {group.items.map((item) => (
                                        <div key={item.key} className="flex items-center justify-between gap-4 px-4 py-3 text-sm">
                                          <div className="min-w-0">
                                            <p className="truncate font-medium text-foreground">{item.label}</p>
                                            {item.subtitle ? <p className="truncate text-xs text-muted-foreground">{item.subtitle}</p> : null}
                                          </div>
                                          <p className="shrink-0 font-medium text-foreground">{formatCurrency(item.value)}</p>
                                        </div>
                                      ))}
                                    </div>
                                  ) : null}
                                </div>
                              );
                            })
                          )}
                        </div>
                      </div>
                    ) : isAssetsLiabilitiesDashboard ? (
                      <div className="space-y-3">
                        <Card className="rounded-xl border border-slate-200 bg-white shadow-none dark:border-border dark:bg-card">
                          <CardContent className="px-4 py-4">
                            <div className="overflow-x-auto md:overflow-visible">
                              <div className="flex min-w-max flex-nowrap items-center gap-x-4 gap-y-2 md:min-w-0 md:flex-wrap">
                              {assetsLiabilitiesTypeOptions.map((option) => {
                                const selected = assetsLiabilitiesTypeSelection === option.key;
                                return (
                                  <button
                                    key={option.key}
                                    type="button"
                                    onClick={() => setAssetsLiabilitiesTypeSelection(option.key)}
                                    className={`relative inline-flex items-center text-sm leading-none transition-colors ${
                                      selected
                                        ? "font-semibold text-foreground dark:text-foreground"
                                        : "font-normal text-muted-foreground hover:text-foreground dark:text-muted-foreground dark:hover:text-foreground"
                                    }`}
                                  >
                                    {option.label}
                                    {selected ? <span className="absolute -bottom-1 left-0 right-0 h-0.5 bg-current" /> : null}
                                  </button>
                                );
                              })}
                              </div>
                            </div>
                            {totalAccountHoldings === 0 ? (
                              <div className="mt-4 rounded-lg border border-dashed border-slate-300 px-3 py-4 text-sm text-muted-foreground dark:border-border dark:text-muted-foreground">
                                No assets in portfolio yet. Click Add Assets to get started.
                              </div>
                            ) : null}
                          </CardContent>
                        </Card>
                      </div>
                    ) : activeSidebarCategory === "holdings" ? (
                      <div className="h-[520px] w-full rounded-xl border border-slate-300/80 bg-slate-100/70 dark:border-border dark:bg-card" />
                    ) : (
                      <div className="flex items-start gap-2">
                        <div className="relative flex-1 overflow-hidden">
                          <div
                            ref={gridRef}
                            className="grid auto-rows-[120px] gap-3 md:auto-rows-[132px]"
                            style={{ gridTemplateColumns: `repeat(${Math.max(1, columns)}, minmax(0, 1fr))` }}
                          >
                            {Array.from({ length: totalSlots }, (_, slot) => (
                              <div key={`slot-${slot}`} className="pointer-events-none rounded-xl border border-transparent bg-transparent" />
                            ))}
                          </div>
                          <div ref={overlayRef} className="absolute inset-0 z-10">
                            {tiles.map((tile) => {
                              const pos = getGridPosition(tile.slot, columns);
                              const left = pos.col * (gridMetrics?.cellWidth ?? 0) + pos.col * (gridMetrics?.colGap ?? 0);
                              const top = pos.row * (gridMetrics?.cellHeight ?? 0) + pos.row * (gridMetrics?.rowGap ?? 0);
                              const width = tile.colSpan * (gridMetrics?.cellWidth ?? 0) + (tile.colSpan - 1) * (gridMetrics?.colGap ?? 0);
                              const height = tile.rowSpan * (gridMetrics?.cellHeight ?? 0) + (tile.rowSpan - 1) * (gridMetrics?.rowGap ?? 0);
                              return (
                                <div
                                  key={`tile-${tile.id}`}
                                  style={{
                                    left: `${left}px`,
                                    top: `${top}px`,
                                    width: `${width}px`,
                                    height: `${height}px`,
                                  }}
                                  className="absolute rounded-xl border border-primary/20 bg-primary p-3 text-primary-foreground"
                                >
                                  <div className="flex h-full flex-col justify-between">
                                    <div className="text-xs font-medium uppercase tracking-wide opacity-80">Tile {tile.id}</div>
                                    <div className="text-[11px] opacity-85">
                                      {tile.colSpan}x{tile.rowSpan} tile
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ) : null}
              </div>
            </div>
            </div>
          </section>
        </div>
      </div>
      </div>
      </div>
      {isAddAssetModalOpen && !isEditing ? (
        <div className="fixed inset-0 z-[78] flex items-center justify-center bg-slate-900/35 px-4">
          <div className="w-full max-w-3xl rounded-[1.75rem] border border-slate-200 bg-[#f8f8fb] p-5 shadow-[0_24px_60px_rgba(15,23,42,0.24)]">
            <div className="mb-4 flex items-start justify-between gap-3">
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-slate-900">
                  {isAddAssetTypeViewOpen ? "New Asset Type" : "Add Asset"}
                </h2>
                {!isAddAssetTypeViewOpen ? (
                  <div className="mt-3 flex w-full flex-wrap items-center justify-center gap-3 text-center text-xs">
                    <span className={addAssetStep === "type" ? "font-medium text-slate-900" : "text-slate-500"}>1. Select Asset Type</span>
                    <span className="h-px w-8 bg-slate-300" aria-hidden="true" />
                    <span className={addAssetStep === "account" ? "font-medium text-slate-900" : "text-slate-500"}>2. Choose or Create Account</span>
                    <span className="h-px w-8 bg-slate-300" aria-hidden="true" />
                    <span className={addAssetStep === "asset" ? "font-medium text-slate-900" : "text-slate-500"}>3. Add or Sync Asset</span>
                  </div>
                ) : null}
              </div>
              <button
                type="button"
                onClick={closeAddAssetsModal}
                className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 transition-colors hover:bg-slate-200"
                aria-label="Close add flow"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="max-h-[62vh] overflow-y-auto pr-1">
              {isAddAssetTypeViewOpen ? (
                <div className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="space-y-2">
                    <label htmlFor="new-asset-type-name" className="text-sm font-medium text-slate-900">
                      Asset type name
                    </label>
                    <input
                      id="new-asset-type-name"
                      type="text"
                      value={newAssetTypeName}
                      onChange={(event) => {
                        setNewAssetTypeName(event.target.value);
                        if (newAssetTypeError) setNewAssetTypeError(null);
                      }}
                      placeholder="Example: Private Credit"
                      className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition-colors focus:border-slate-400"
                    />
                    {newAssetTypeError ? <p className="text-sm text-rose-600">{newAssetTypeError}</p> : null}
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <button
                      type="button"
                      onClick={() => {
                        setIsAddAssetTypeViewOpen(false);
                        setNewAssetTypeName("");
                        setNewAssetTypeError(null);
                      }}
                      className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-100"
                    >
                      Back
                    </button>
                    <button
                      type="button"
                      onClick={() => void handleCreateAssetType()}
                      disabled={isCreatingAssetType}
                      className="rounded-xl border border-slate-900 bg-slate-900 px-4 py-2 text-sm text-white transition-colors hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {isCreatingAssetType ? "Creating..." : "Create Asset Type"}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {addAssetFlowError ? (
                    <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
                      {addAssetFlowError}
                    </div>
                  ) : null}
                  {addAssetStep === "type" ? (
                    <>
                      <div className="grid auto-rows-[124px] grid-cols-2 gap-3 md:grid-cols-3">
                        {addAssetModalAssetTypes.map((assetType) => {
                          const assetTypeKey = `add-asset-type-${assetType.slug ?? assetType.id}`;
                          const Icon = getAddAssetTileIcon(assetType.slug);
                          const toneClass = getAddAssetTileTone(assetType.slug);
                          return (
                            <button
                              key={assetTypeKey}
                              type="button"
                              onClick={() => {
                                if (assetType.slug === "equity") {
                                  beginAddAssetFlow(assetType);
                                  return;
                                }
                                setActiveSidebarCategory(`asset-type:${assetType.slug ?? assetType.id}`);
                                setActiveSidebarLabel(assetType.name);
                                closeAddAssetsModal();
                              }}
                              className={`group rounded-[1.25rem] border p-4 text-left shadow-[0_8px_24px_rgba(15,23,42,0.04)] transition-all duration-150 hover:-translate-y-0.5 ${toneClass}`}
                            >
                              <div className="flex h-full flex-col justify-between gap-4">
                                <div className="flex items-start justify-between gap-3">
                                  <span className="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 ring-1 ring-slate-200 transition-colors group-hover:bg-white">
                                    <Icon className="h-5 w-5 text-slate-700" />
                                  </span>
                                </div>
                                <div className="pr-2">
                                  <p className="text-base font-semibold text-slate-900">{assetType.name}</p>
                                </div>
                              </div>
                            </button>
                          );
                        })}
                        <button
                          type="button"
                          onClick={() => {
                            setIsAddAssetTypeViewOpen(true);
                            setNewAssetTypeError(null);
                          }}
                          className="group rounded-[1.25rem] border border-slate-900 bg-slate-900 p-4 text-left shadow-[0_8px_24px_rgba(15,23,42,0.12)] transition-all duration-150 hover:-translate-y-0.5 hover:bg-slate-800"
                        >
                          <div className="flex h-full flex-col justify-between gap-4">
                            <div className="flex items-start justify-between gap-3">
                              <span className="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-white/10 ring-1 ring-white/10">
                                <Plus className="h-5 w-5 text-white" />
                              </span>
                            </div>
                            <div className="pr-2">
                              <p className="text-base font-semibold text-white">Add Custom Asset Type</p>
                            </div>
                          </div>
                        </button>
                      </div>
                      {addAssetModalAssetTypes.length === 0 ? (
                        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                          No asset types yet.
                        </div>
                      ) : null}
                    </>
                  ) : null}
                  {addAssetStep === "account" && selectedAddAssetType ? (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="text-base font-semibold text-slate-900">{selectedAddAssetType.name}</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => setAddAssetStep("type")}
                          className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-100"
                        >
                          Back
                        </button>
                      </div>
                      <div className={`grid gap-4 ${isAddAccountInlineOpen ? "lg:grid-cols-[1.1fr_0.9fr]" : "lg:grid-cols-[1fr_auto]"}`}>
                        <div className="rounded-2xl border border-slate-200 bg-white p-4">
                          <div className="space-y-3">
                            {eligibleAccountsForSelectedAsset.length > 0 ? (
                              eligibleAccountsForSelectedAsset.map((account) => (
                                <button
                                  key={`eligible-account-${account.id}`}
                                  type="button"
                                  onClick={() => {
                                    setSelectedAddAssetAccountId(account.id);
                                    setAddAssetStep("asset");
                                  }}
                                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 p-4 text-left transition-colors hover:border-slate-300 hover:bg-white"
                                >
                                  <p className="text-base font-semibold text-slate-900">{account.name}</p>
                                  <p className="mt-1 text-sm text-slate-500">{accountTypeNameById.get(account.account_type) ?? "Account"}</p>
                                </button>
                              ))
                            ) : (
                              <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-500">
                                No existing accounts.
                              </div>
                            )}
                          </div>
                        </div>
                        {!isAddAccountInlineOpen ? (
                          <button
                            type="button"
                            onClick={() => setIsAddAccountInlineOpen(true)}
                            className="h-fit rounded-2xl border border-slate-900 bg-slate-900 px-5 py-3 text-sm font-medium text-white transition-colors hover:bg-slate-800"
                          >
                            Add New Account
                          </button>
                        ) : (
                          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                            <div className="grid gap-3">
                              <select
                                value={newAccountTypeId ?? ""}
                                onChange={(event) => setNewAccountTypeId(Number(event.target.value))}
                                className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none focus:border-slate-400"
                              >
                                {eligibleAccountTypesForSelectedAsset.map((accountType) => (
                                  <option key={`account-type-option-${accountType.id}`} value={accountType.id}>
                                    {accountType.name}
                                  </option>
                                ))}
                              </select>
                              <input
                                type="text"
                                value={newAccountName}
                                onChange={(event) => setNewAccountName(event.target.value)}
                                placeholder={brokerageAccountType ? "Brokerage Account" : "Account Name"}
                                className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none focus:border-slate-400"
                              />
                              <input
                                type="text"
                                value={newAccountBroker}
                                onChange={(event) => setNewAccountBroker(event.target.value)}
                                placeholder="Broker"
                                className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none focus:border-slate-400"
                              />
                              <select
                                value={newAccountPortfolioId ?? ""}
                                onChange={(event) => setNewAccountPortfolioId(Number(event.target.value))}
                                className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none focus:border-slate-400"
                              >
                                {(accountCreateOptions?.portfolios ?? []).map((portfolio) => (
                                  <option key={`portfolio-option-${portfolio.id}`} value={portfolio.id}>
                                    {portfolio.name}
                                  </option>
                                ))}
                              </select>
                              <select
                                value={newAccountClassificationId ?? ""}
                                onChange={(event) => setNewAccountClassificationId(Number(event.target.value))}
                                className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none focus:border-slate-400"
                              >
                                {(accountCreateOptions?.classification_definitions ?? []).map((classification) => (
                                  <option key={`classification-option-${classification.id}`} value={classification.id}>
                                    {classification.name}
                                  </option>
                                ))}
                              </select>
                            </div>
                            <div className="mt-4 flex items-center gap-2">
                              <button
                                type="button"
                                onClick={() => void handleCreateEligibleAccount()}
                                disabled={isCreatingAccount}
                                className="rounded-xl border border-slate-900 bg-slate-900 px-4 py-2 text-sm text-white transition-colors hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                              >
                                {isCreatingAccount ? "Creating..." : "Add Account"}
                              </button>
                              <button
                                type="button"
                                onClick={() => setIsAddAccountInlineOpen(false)}
                                className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-100"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : null}
                  {addAssetStep === "asset" && selectedAddAssetType?.slug === "equity" ? (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="text-sm text-slate-500">Account selected</p>
                          <p className="text-base font-semibold text-slate-900">
                            {eligibleAccountsForSelectedAsset.find((account) => account.id === selectedAddAssetAccountId)?.name ?? "Account"}
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => setAddAssetStep("account")}
                          className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-100"
                        >
                          Back
                        </button>
                      </div>
                      <div className="rounded-2xl border border-slate-200 bg-white p-4">
                        <p className="text-sm font-medium text-slate-900">Find equity</p>
                        <input
                          type="text"
                          value={equitySearchQuery}
                          onChange={(event) => {
                            setEquitySearchQuery(event.target.value);
                            setSelectedEquityResult(null);
                          }}
                          placeholder="Type company name or ticker"
                          className="mt-3 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 outline-none focus:border-slate-400"
                        />
                        <div className="mt-3 max-h-[240px] overflow-y-auto space-y-2">
                          {isEquitySearchLoading ? (
                            <div className="text-sm text-slate-500">Searching…</div>
                          ) : null}
                          {!isEquitySearchLoading && equitySearchQuery.trim().length > 0 && equitySearchResults.length === 0 ? (
                            <div className="text-sm text-slate-500">No matches found.</div>
                          ) : null}
                          {equitySearchResults.map((result) => (
                            <button
                              key={`equity-result-${result.asset_id}`}
                              type="button"
                              onClick={() => setSelectedEquityResult(result)}
                              className={`w-full rounded-xl border px-3 py-3 text-left transition-colors ${
                                selectedEquityResult?.asset_id === result.asset_id
                                  ? "border-slate-900 bg-slate-900 text-white"
                                  : "border-slate-200 bg-slate-50 text-slate-900 hover:bg-white"
                              }`}
                            >
                              <div className="flex items-center justify-between gap-3">
                                <div>
                                  <p className="text-sm font-semibold">{result.ticker}</p>
                                  <p className={`text-sm ${selectedEquityResult?.asset_id === result.asset_id ? "text-white/80" : "text-slate-500"}`}>{result.name}</p>
                                </div>
                                <div className={`text-xs ${selectedEquityResult?.asset_id === result.asset_id ? "text-white/70" : "text-slate-400"}`}>
                                  {result.sector ?? "Equity"}
                                </div>
                              </div>
                            </button>
                          ))}
                        </div>
                      </div>
                      <div className="grid gap-3 md:grid-cols-2">
                        <input
                          type="text"
                          inputMode="decimal"
                          value={newHoldingQuantity}
                          onChange={(event) => setNewHoldingQuantity(event.target.value)}
                          placeholder="Quantity"
                          className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none focus:border-slate-400"
                        />
                        <input
                          type="text"
                          inputMode="decimal"
                          value={newHoldingAverageCost}
                          onChange={(event) => setNewHoldingAverageCost(event.target.value)}
                          placeholder="Average cost (optional)"
                          className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none focus:border-slate-400"
                        />
                      </div>
                      <button
                        type="button"
                        onClick={() => void handleSubmitEquityHolding()}
                        disabled={isSubmittingHolding}
                        className="rounded-xl border border-slate-900 bg-slate-900 px-4 py-2 text-sm text-white transition-colors hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {isSubmittingHolding ? "Adding..." : "Add Equity"}
                      </button>
                    </div>
                  ) : null}
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}
      {isEditing ? (
        <div className="edit-dashboard-screen fixed inset-x-0 bottom-0 top-20 z-50 bg-slate-900/25 backdrop-blur-[4px]">
          <div className="mx-auto h-full w-full max-w-[1680px] overflow-y-auto px-4 py-4 sm:px-6 lg:px-8">
            <div className="space-y-3">
              <div className="flex justify-center">
                <div className={`h-[calc(100vh-7rem)] w-full ${editPreviewWidthClass}`}>
                <Card className="edit-dashboard-sheet-bg h-full overflow-hidden border-border">
                  <CardContent className="flex h-full flex-col gap-4 overflow-hidden p-5">
                    <div ref={gridScrollRef} className="min-h-0 flex-1 overflow-auto px-1">
                    <div className={isManageGridMode ? "edit-dashboard-sheet-bg sticky top-0 z-[110] pb-2" : ""}>
                    {useCompactEditToolbar ? (
                    <div className="space-y-3">
                      {!isManageGridMode ? (
                        <div className={`flex justify-center ${editingViewport === "tablet" ? "mb-4" : ""}`}>
                          <div className="relative grid w-full max-w-[260px] grid-cols-3 rounded-lg border border-blue-100 bg-white p-1">
                            <div
                              className="absolute bottom-1 left-1 top-1 z-0 w-[calc((100%-0.5rem)/3)] rounded-md bg-blue-600 transition-transform duration-200"
                              style={{ transform: `translateX(${editViewportIndex * 100}%)` }}
                            />
                            {[
                              { key: "mobile", label: "Mobile", icon: Smartphone },
                              { key: "tablet", label: "Tablet", icon: Tablet },
                              { key: "desktop", label: "Desktop", icon: Monitor },
                            ].map((option) => {
                              const active = editingViewport === option.key;
                              const Icon = option.icon;
                              return (
                                <button
                                  key={`edit-viewport-mobile-${option.key}`}
                                  type="button"
                                  onClick={() => setEditingViewport(option.key as EditViewport)}
                                  title={option.label}
                                  aria-label={option.label}
                                  className={`relative z-10 inline-flex h-9 items-center justify-center rounded-md transition-colors ${
                                    active ? "text-white" : "text-slate-400 hover:text-slate-600"
                                  }`}
                                >
                                  <Icon className="h-4 w-4" />
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      ) : null}
                      <div className="space-y-4">
                        {!isManageGridMode ? (
                          <div className={`${editingViewport === "tablet" ? "mt-10" : "mt-6"} flex items-center justify-end gap-2`}>
                            <span
                              className={`rounded-md border px-2.5 py-1 text-xs font-semibold ${
                                hasUnsavedChanges
                                  ? "border-amber-200 bg-amber-50 text-amber-900"
                                  : "border-blue-200 bg-blue-50 text-blue-800"
                              }`}
                            >
                              {hasUnsavedChanges ? "Unsaved Changes" : "No Changes"}
                            </span>
                            <div className="relative flex items-center gap-1" data-exit-actions-menu>
                              <button
                                type="button"
                                onClick={requestExitEditing}
                                className="edit-save-check-btn inline-flex h-7 w-7 items-center justify-center rounded-full border border-border bg-white text-foreground transition-colors hover:bg-secondary/80"
                                title="Save and close"
                                aria-label="Save and close"
                              >
                                <Check className="h-4 w-4" />
                              </button>
                              {isExitActionsMenuOpen ? (
                                <div className="absolute right-0 top-full z-[140] mt-2 w-44 rounded-xl border border-border bg-white p-1 shadow-lg">
                                  <button
                                    type="button"
                                    onClick={confirmExitEditSave}
                                    className="w-full rounded px-2 py-1.5 text-left text-xs transition-colors hover:bg-secondary/80 hover:text-foreground"
                                  >
                                    Save & Exit
                                  </button>
                                  <button
                                    type="button"
                                    onClick={confirmExitEditDiscard}
                                    className="w-full rounded px-2 py-1.5 text-left text-xs transition-colors hover:bg-secondary/80 hover:text-foreground"
                                  >
                                    Discard & Exit
                                  </button>
                                </div>
                              ) : null}
                            </div>
                          </div>
                        ) : null}
                        <div className="flex flex-wrap items-center gap-2">
                          <select
                            value={activeLayoutId}
                            onChange={(event) => requestLayoutSwitch(event.target.value)}
                            disabled={isManageGridMode}
                            className={`edit-layout-select min-w-0 flex-1 rounded-xl border border-blue-100 bg-white px-2 py-1.5 text-sm text-foreground ${
                              isManageGridMode ? "opacity-55" : ""
                            }`}
                          >
                            {savedLayouts.map((layout) => (
                              <option key={`dashboard-layout-select-mobile-${layout.id}`} value={layout.id}>
                                {getDisplayLayoutName(layout.name)}{layout.isPrimary ? " (Active)" : ""}
                              </option>
                            ))}
                          </select>
                          {!isManageGridMode ? (
                            <div className="relative" data-dashboard-menu>
                              <button
                                type="button"
                                onClick={() => setLayoutActionsMenuOpen((previous) => !previous)}
                                className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-border bg-white text-foreground transition-colors hover:bg-secondary/80"
                                title="Layout actions"
                                aria-label="Layout actions"
                              >
                                <Ellipsis className="h-4 w-4" />
                              </button>
                              {layoutActionsMenuOpen ? (
                                <div className="absolute right-0 z-[140] mt-2 w-52 rounded-xl border border-border bg-white p-1 shadow-lg">
                                  <button
                                    type="button"
                                    onClick={() => {
                                      setLayoutNameDialogMode("rename");
                                      setPendingLayoutName(activeLayout?.name ?? defaultLayoutName);
                                      setLayoutNameError(null);
                                      setIsNewLayoutDialogOpen(true);
                                      setLayoutActionsMenuOpen(false);
                                    }}
                                    className="w-full rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-secondary/80 hover:text-foreground"
                                  >
                                    Rename Current Layout
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      if (hasUnsavedChanges) {
                                        setPendingSwitchLayoutId(null);
                                        setPendingCreateLayout(true);
                                        setIsSwitchLayoutDialogOpen(true);
                                      } else {
                                        setLayoutNameDialogMode("create");
                                        setPendingLayoutName(`${sectionLabel} Layout ${savedLayouts.length + 1}`);
                                        setLayoutNameError(null);
                                        setIsNewLayoutDialogOpen(true);
                                      }
                                      setLayoutActionsMenuOpen(false);
                                    }}
                                    className="w-full rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-secondary/80 hover:text-foreground"
                                  >
                                    Add Layout
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      if (!activeLayout || activeLayout.isPrimary) return;
                                      setPrimaryLayout(activeLayout.id);
                                      setLayoutActionsMenuOpen(false);
                                    }}
                                    disabled={!activeLayout || activeLayout.isPrimary}
                                    className="w-full rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-secondary/80 hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50"
                                  >
                                    Make Active
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      if (activeLayout?.isPrimary || savedLayouts.length <= 1) return;
                                      const shouldDelete = window.confirm(`Are you sure you want to delete "${activeLayout?.name ?? "this layout"}"?`);
                                      if (!shouldDelete) return;
                                      deleteActiveLayout();
                                      setLayoutActionsMenuOpen(false);
                                    }}
                                    disabled={Boolean(activeLayout?.isPrimary) || savedLayouts.length <= 1}
                                    className="w-full rounded px-2 py-1.5 text-left text-sm text-red-700 transition-colors hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
                                  >
                                    Delete
                                  </button>
                                </div>
                              ) : null}
                            </div>
                          ) : null}
                          {isManageGridMode ? (
                            <div className="ml-auto flex flex-wrap items-center justify-end gap-2">
                              <button
                                type="button"
                                onClick={() => {
                                  if (columns >= VIEWPORT_MAX_COLUMNS[activeViewport]) {
                                    
                                  } else {
                                    addColumn();
                                    
                                  }
                                }}
                                className="inline-flex items-center gap-1 rounded-xl border border-border bg-white px-2.5 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-secondary/80"
                                title="Add Column"
                                aria-label="Add Column"
                              >
                                <Plus className="h-3.5 w-3.5" />
                                <span>Add Column</span>
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  if (canAddRow) {
                                    setTargetRows((previous) => Math.min(MAX_ROWS, previous + 1));
                                  }
                                  
                                }}
                                disabled={!canAddRow}
                                className="inline-flex items-center gap-1 rounded-xl border border-border bg-white px-2.5 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-secondary/80 disabled:cursor-not-allowed disabled:opacity-50"
                                title="Add Row"
                                aria-label="Add Row"
                              >
                                <Plus className="h-3.5 w-3.5" />
                                <span>Add Row</span>
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  setSelectedDeleteRows([]);
                                  setSelectedDeleteCols([]);
                                  setHoveredDeleteRow(null);
                                  setHoveredDeleteCol(null);
                                }}
                                disabled={selectedDeleteRows.length === 0 && selectedDeleteCols.length === 0}
                                className="inline-flex items-center gap-1 rounded-xl border border-border bg-white px-2.5 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-secondary/80 disabled:cursor-not-allowed disabled:opacity-50"
                                title="Cancel selected delete targets"
                                aria-label="Cancel selected delete targets"
                              >
                                <X className="h-3.5 w-3.5" />
                                <span>Cancel Selection</span>
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  setIsManageGridMode(false);
                                  setIsDeleteStructureMode(false);
                                  setSelectedDeleteRows([]);
                                  setSelectedDeleteCols([]);
                                  setHoveredDeleteRow(null);
                                  setHoveredDeleteCol(null);
                                  
                                }}
                                className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-border bg-white text-foreground transition-colors hover:bg-foreground hover:text-background"
                                title="Exit grid manage mode"
                                aria-label="Exit grid manage mode"
                              >
                                <Check className="h-4 w-4" />
                              </button>
                            </div>
                          ) : null}
                        </div>
                      </div>
                    </div>
                    ) : useTabletEditToolbar ? (
                    <div className="space-y-3">
                      {!isManageGridMode ? (
                        <div className="mb-5 flex justify-center">
                          <div className="relative grid w-[260px] grid-cols-3 rounded-lg border border-blue-100 bg-white p-1">
                            <div
                              className="absolute bottom-1 left-1 top-1 z-0 w-[calc((100%-0.5rem)/3)] rounded-md bg-blue-600 transition-transform duration-200"
                              style={{ transform: `translateX(${editViewportIndex * 100}%)` }}
                            />
                            {[
                              { key: "mobile", label: "Mobile", icon: Smartphone },
                              { key: "tablet", label: "Tablet", icon: Tablet },
                              { key: "desktop", label: "Desktop", icon: Monitor },
                            ].map((option) => {
                              const active = editingViewport === option.key;
                              const Icon = option.icon;
                              return (
                                <button
                                  key={`edit-viewport-tablet-${option.key}`}
                                  type="button"
                                  onClick={() => setEditingViewport(option.key as EditViewport)}
                                  title={option.label}
                                  aria-label={option.label}
                                  className={`relative z-10 inline-flex h-9 items-center justify-center rounded-md transition-colors ${
                                    active ? "text-white" : "text-slate-400 hover:text-slate-600"
                                  }`}
                                >
                                  <Icon className="h-4 w-4" />
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      ) : null}
                      <div className="mt-12 flex items-start justify-between gap-3">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <select
                              value={activeLayoutId}
                              onChange={(event) => requestLayoutSwitch(event.target.value)}
                              disabled={isManageGridMode}
                              className={`edit-layout-select min-w-0 max-w-[360px] flex-1 rounded-xl border border-blue-100 bg-white px-2 py-1.5 text-sm text-foreground ${
                                isManageGridMode ? "opacity-55" : ""
                              }`}
                            >
                              {savedLayouts.map((layout) => (
                                <option key={`dashboard-layout-select-tablet-${layout.id}`} value={layout.id}>
                                  {getDisplayLayoutName(layout.name)}{layout.isPrimary ? " (Active)" : ""}
                                </option>
                              ))}
                            </select>
                            {!isManageGridMode ? (
                              <div className="relative" data-dashboard-menu>
                                <button
                                  type="button"
                                  onClick={() => setLayoutActionsMenuOpen((previous) => !previous)}
                                  className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-border bg-white text-foreground transition-colors hover:bg-secondary/80"
                                  title="Layout actions"
                                  aria-label="Layout actions"
                                >
                                  <Ellipsis className="h-4 w-4" />
                                </button>
                                {layoutActionsMenuOpen ? (
                                  <div className="absolute left-0 z-[140] mt-2 w-52 rounded-xl border border-border bg-white p-1 shadow-lg">
                                  <button
                                    type="button"
                                    onClick={() => {
                                      setLayoutNameDialogMode("rename");
                                      setPendingLayoutName(activeLayout?.name ?? defaultLayoutName);
                                      setLayoutNameError(null);
                                      setIsNewLayoutDialogOpen(true);
                                      setLayoutActionsMenuOpen(false);
                                    }}
                                    className="w-full rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-secondary/80 hover:text-foreground"
                                  >
                                    Rename Current Layout
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      if (hasUnsavedChanges) {
                                        setPendingSwitchLayoutId(null);
                                        setPendingCreateLayout(true);
                                        setIsSwitchLayoutDialogOpen(true);
                                      } else {
                                        setLayoutNameDialogMode("create");
                                        setPendingLayoutName(`${sectionLabel} Layout ${savedLayouts.length + 1}`);
                                        setLayoutNameError(null);
                                        setIsNewLayoutDialogOpen(true);
                                      }
                                      setLayoutActionsMenuOpen(false);
                                    }}
                                    className="w-full rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-secondary/80 hover:text-foreground"
                                  >
                                    Add Layout
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      if (!activeLayout || activeLayout.isPrimary) return;
                                      setPrimaryLayout(activeLayout.id);
                                      setLayoutActionsMenuOpen(false);
                                    }}
                                    disabled={!activeLayout || activeLayout.isPrimary}
                                    className="w-full rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-secondary/80 hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50"
                                  >
                                    Make Active
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      if (activeLayout?.isPrimary || savedLayouts.length <= 1) return;
                                      const shouldDelete = window.confirm(`Are you sure you want to delete "${activeLayout?.name ?? "this layout"}"?`);
                                      if (!shouldDelete) return;
                                      deleteActiveLayout();
                                      setLayoutActionsMenuOpen(false);
                                    }}
                                    disabled={Boolean(activeLayout?.isPrimary) || savedLayouts.length <= 1}
                                    className="w-full rounded px-2 py-1.5 text-left text-sm text-red-700 transition-colors hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
                                  >
                                    Delete
                                  </button>
                                  </div>
                                ) : null}
                              </div>
                            ) : null}
                            {isManageGridMode ? (
                              <div className="ml-auto flex flex-wrap items-center justify-end gap-2">
                                <button
                                  type="button"
                                  onClick={() => {
                                    if (columns >= VIEWPORT_MAX_COLUMNS[activeViewport]) {
                                      
                                    } else {
                                      addColumn();
                                      
                                    }
                                  }}
                                  className="inline-flex items-center gap-1 rounded-xl border border-border bg-white px-2.5 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-secondary/80"
                                  title="Add Column"
                                  aria-label="Add Column"
                                >
                                  <Plus className="h-3.5 w-3.5" />
                                  <span>Add Column</span>
                                </button>
                                <button
                                  type="button"
                                  onClick={() => {
                                    if (canAddRow) {
                                      setTargetRows((previous) => Math.min(MAX_ROWS, previous + 1));
                                    }
                                    
                                  }}
                                  disabled={!canAddRow}
                                  className="inline-flex items-center gap-1 rounded-xl border border-border bg-white px-2.5 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-secondary/80 disabled:cursor-not-allowed disabled:opacity-50"
                                  title="Add Row"
                                  aria-label="Add Row"
                                >
                                  <Plus className="h-3.5 w-3.5" />
                                  <span>Add Row</span>
                                </button>
                                <button
                                  type="button"
                                  onClick={() => {
                                    setSelectedDeleteRows([]);
                                    setSelectedDeleteCols([]);
                                    setHoveredDeleteRow(null);
                                    setHoveredDeleteCol(null);
                                  }}
                                  disabled={selectedDeleteRows.length === 0 && selectedDeleteCols.length === 0}
                                  className="inline-flex items-center gap-1 rounded-xl border border-border bg-white px-2.5 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-secondary/80 disabled:cursor-not-allowed disabled:opacity-50"
                                  title="Cancel selected delete targets"
                                  aria-label="Cancel selected delete targets"
                                >
                                  <X className="h-3.5 w-3.5" />
                                  <span>Cancel Selection</span>
                                </button>
                                <button
                                  type="button"
                                  onClick={() => {
                                    setIsManageGridMode(false);
                                    setIsDeleteStructureMode(false);
                                    setSelectedDeleteRows([]);
                                    setSelectedDeleteCols([]);
                                    setHoveredDeleteRow(null);
                                    setHoveredDeleteCol(null);
                                    
                                  }}
                                  className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-border bg-white text-foreground transition-colors hover:bg-foreground hover:text-background"
                                  title="Exit grid manage mode"
                                  aria-label="Exit grid manage mode"
                                >
                                  <Check className="h-4 w-4" />
                                </button>
                              </div>
                            ) : null}
                          </div>
                        </div>
                        {!isManageGridMode ? (
                          <div className="flex items-center gap-2">
                            <span
                              className={`rounded-md border px-2.5 py-1 text-xs font-semibold ${
                                hasUnsavedChanges
                                  ? "border-amber-200 bg-amber-50 text-amber-900"
                                  : "border-blue-200 bg-blue-50 text-blue-800"
                              }`}
                            >
                              {hasUnsavedChanges ? "Unsaved Changes" : "No Changes"}
                            </span>
                            <div className="relative flex items-center gap-1" data-exit-actions-menu>
                              <button
                                type="button"
                                onClick={requestExitEditing}
                                className="edit-save-check-btn inline-flex h-8 w-8 items-center justify-center rounded-full border border-border bg-white text-foreground transition-colors hover:bg-secondary/80"
                                title="Save and close"
                                aria-label="Save and close"
                              >
                                <Check className="h-4 w-4" />
                              </button>
                              {isExitActionsMenuOpen ? (
                                <div className="absolute right-0 top-full z-[140] mt-2 w-44 rounded-xl border border-border bg-white p-1 shadow-lg">
                                  <button
                                    type="button"
                                    onClick={confirmExitEditSave}
                                    className="w-full rounded px-2 py-1.5 text-left text-xs transition-colors hover:bg-secondary/80 hover:text-foreground"
                                  >
                                    Save & Exit
                                  </button>
                                  <button
                                    type="button"
                                    onClick={confirmExitEditDiscard}
                                    className="w-full rounded px-2 py-1.5 text-left text-xs transition-colors hover:bg-secondary/80 hover:text-foreground"
                                  >
                                    Discard & Exit
                                  </button>
                                </div>
                              ) : null}
                            </div>
                          </div>
                        ) : null}
                      </div>
                    </div>
                    ) : (
                    <div className="grid items-center gap-4 px-2 lg:grid-cols-6">
                      <div className="flex flex-col gap-1 lg:col-span-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <select
                            value={activeLayoutId}
                            onChange={(event) => requestLayoutSwitch(event.target.value)}
                            disabled={isManageGridMode}
                            className={`edit-layout-select w-full min-w-0 rounded-xl border border-blue-100 bg-white px-2 py-1.5 text-sm text-foreground sm:w-auto sm:min-w-[220px] ${
                              isManageGridMode ? "opacity-55" : ""
                            }`}
                          >
                            {savedLayouts.map((layout) => (
                              <option key={`dashboard-layout-select-${layout.id}`} value={layout.id}>
                                {getDisplayLayoutName(layout.name)}{layout.isPrimary ? " (Active)" : ""}
                              </option>
                            ))}
                          </select>
                          {!isManageGridMode ? (
                            <div className="relative" data-dashboard-menu>
                              <button
                                type="button"
                                onClick={() => setLayoutActionsMenuOpen((previous) => !previous)}
                                className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-border bg-white text-foreground transition-colors hover:bg-secondary/80"
                                title="Layout actions"
                                aria-label="Layout actions"
                              >
                                <Ellipsis className="h-4 w-4" />
                              </button>
                              {layoutActionsMenuOpen ? (
                                <div className="absolute left-0 z-[140] mt-2 w-52 rounded-xl border border-border bg-white p-1 shadow-lg">
                                <button
                                  type="button"
                                  onClick={() => {
                                    setLayoutNameDialogMode("rename");
                                    setPendingLayoutName(activeLayout?.name ?? defaultLayoutName);
                                    setLayoutNameError(null);
                                    setIsNewLayoutDialogOpen(true);
                                    setLayoutActionsMenuOpen(false);
                                  }}
                                  className="w-full rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-secondary/80 hover:text-foreground"
                                >
                                  Rename Current Layout
                                </button>
                                <button
                                  type="button"
                                  onClick={() => {
                                    if (hasUnsavedChanges) {
                                      setPendingSwitchLayoutId(null);
                                      setPendingCreateLayout(true);
                                      setIsSwitchLayoutDialogOpen(true);
                                    } else {
                                      setLayoutNameDialogMode("create");
                                      setPendingLayoutName(`${sectionLabel} Layout ${savedLayouts.length + 1}`);
                                      setLayoutNameError(null);
                                      setIsNewLayoutDialogOpen(true);
                                    }
                                    setLayoutActionsMenuOpen(false);
                                  }}
                                  className="w-full rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-secondary/80 hover:text-foreground"
                                >
                                  Add Layout
                                </button>
                                <button
                                  type="button"
                                  onClick={() => {
                                    if (!activeLayout || activeLayout.isPrimary) return;
                                    setPrimaryLayout(activeLayout.id);
                                    setLayoutActionsMenuOpen(false);
                                  }}
                                  disabled={!activeLayout || activeLayout.isPrimary}
                                  className="w-full rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-secondary/80 hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                  Make Active
                                </button>
                                <button
                                  type="button"
                                  onClick={() => {
                                    if (activeLayout?.isPrimary || savedLayouts.length <= 1) return;
                                    const shouldDelete = window.confirm(`Are you sure you want to delete "${activeLayout?.name ?? "this layout"}"?`);
                                    if (!shouldDelete) return;
                                    deleteActiveLayout();
                                    setLayoutActionsMenuOpen(false);
                                  }}
                                  disabled={Boolean(activeLayout?.isPrimary) || savedLayouts.length <= 1}
                                  className="w-full rounded px-2 py-1.5 text-left text-sm text-red-700 transition-colors hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                  Delete
                                </button>
                                </div>
                              ) : null}
                            </div>
                          ) : null}
                          {isManageGridMode ? (
                            <div className="ml-auto flex flex-wrap items-center justify-end gap-2">
                              <button
                                type="button"
                                onClick={() => {
                                  if (columns >= VIEWPORT_MAX_COLUMNS[activeViewport]) {
                                    
                                  } else {
                                    addColumn();
                                    
                                  }
                                }}
                                className="inline-flex items-center gap-1 rounded-xl border border-border bg-white px-2.5 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-secondary/80"
                                title="Add Column"
                                aria-label="Add Column"
                              >
                                <Plus className="h-3.5 w-3.5" />
                                <span>Add Column</span>
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  if (canAddRow) {
                                    setTargetRows((previous) => Math.min(MAX_ROWS, previous + 1));
                                  }
                                  
                                }}
                                disabled={!canAddRow}
                                className="inline-flex items-center gap-1 rounded-xl border border-border bg-white px-2.5 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-secondary/80 disabled:cursor-not-allowed disabled:opacity-50"
                                title="Add Row"
                                aria-label="Add Row"
                              >
                                <Plus className="h-3.5 w-3.5" />
                                <span>Add Row</span>
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  setSelectedDeleteRows([]);
                                  setSelectedDeleteCols([]);
                                  setHoveredDeleteRow(null);
                                  setHoveredDeleteCol(null);
                                }}
                                disabled={selectedDeleteRows.length === 0 && selectedDeleteCols.length === 0}
                                className="inline-flex items-center gap-1 rounded-xl border border-border bg-white px-2.5 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-secondary/80 disabled:cursor-not-allowed disabled:opacity-50"
                                title="Cancel selected delete targets"
                                aria-label="Cancel selected delete targets"
                              >
                                <X className="h-3.5 w-3.5" />
                                <span>Cancel Selection</span>
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  setIsManageGridMode(false);
                                  setIsDeleteStructureMode(false);
                                  setSelectedDeleteRows([]);
                                  setSelectedDeleteCols([]);
                                  setHoveredDeleteRow(null);
                                  setHoveredDeleteCol(null);
                                  
                                }}
                                className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-border bg-white text-foreground transition-colors hover:bg-foreground hover:text-background"
                                title="Exit grid manage mode"
                                aria-label="Exit grid manage mode"
                              >
                                <Check className="h-4 w-4" />
                              </button>
                            </div>
                          ) : null}
                        </div>
                      </div>
                      {!isManageGridMode ? (
                        <div className="justify-self-center w-full md:w-auto lg:col-span-3">
                          <div className="relative mx-auto grid w-full max-w-[260px] grid-cols-3 rounded-lg border border-blue-100 bg-white p-1 md:w-[220px] md:max-w-none">
                            <div
                              className="absolute bottom-1 left-1 top-1 z-0 w-[calc((100%-0.5rem)/3)] rounded-md bg-blue-600 transition-transform duration-200"
                              style={{ transform: `translateX(${editViewportIndex * 100}%)` }}
                            />
                            {[
                              { key: "mobile", label: "Mobile", icon: Smartphone },
                              { key: "tablet", label: "Tablet", icon: Tablet },
                              { key: "desktop", label: "Desktop", icon: Monitor },
                            ].map((option) => {
                              const active = editingViewport === option.key;
                              const Icon = option.icon;
                              return (
                                <button
                                  key={`edit-viewport-${option.key}`}
                                  type="button"
                                  onClick={() => setEditingViewport(option.key as EditViewport)}
                                  title={option.label}
                                  aria-label={option.label}
                                  className={`relative z-10 inline-flex h-9 items-center justify-center rounded-md transition-colors ${
                                    active ? "text-white" : "text-slate-400 hover:text-slate-600"
                                  }`}
                                >
                                  <Icon className="h-4 w-4" />
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      ) : null}
                      {!isManageGridMode ? (
                        <div className="flex items-center justify-end gap-3 lg:col-span-1">
                          <span
                            className={`rounded-md border px-2.5 py-1 text-xs font-semibold ${
                              hasUnsavedChanges
                                ? "border-amber-200 bg-amber-50 text-amber-900"
                                : "border-blue-200 bg-blue-50 text-blue-800"
                            }`}
                          >
                            {hasUnsavedChanges ? "Unsaved Changes" : "No Changes"}
                          </span>
                          <div className="relative flex items-center gap-1" data-exit-actions-menu>
                            <button
                              type="button"
                              onClick={requestExitEditing}
                              className="edit-save-check-btn inline-flex h-8 w-8 items-center justify-center rounded-full border border-border bg-white text-foreground transition-colors hover:bg-secondary/80"
                              title="Save and close"
                              aria-label="Save and close"
                            >
                              <Check className="h-4 w-4" />
                            </button>
                            {isExitActionsMenuOpen ? (
                              <div className="absolute right-0 top-full z-[140] mt-2 w-44 rounded-xl border border-border bg-white p-1 shadow-lg">
                                <button
                                  type="button"
                                  onClick={confirmExitEditSave}
                                  className="w-full rounded px-2 py-1.5 text-left text-xs transition-colors hover:bg-secondary/80 hover:text-foreground"
                                >
                                  Save & Exit
                                </button>
                                <button
                                  type="button"
                                  onClick={confirmExitEditDiscard}
                                  className="w-full rounded px-2 py-1.5 text-left text-xs transition-colors hover:bg-secondary/80 hover:text-foreground"
                                >
                                  Discard & Exit
                                </button>
                              </div>
                            ) : null}
                          </div>
                        </div>
                      ) : null}
                    </div>
                    )}
                    </div>
                      <div className="edit-dashboard-sheet-bg sticky top-0 z-[90] isolate mb-2 mt-3 space-y-2 px-2 pb-2">
                      {!isManageGridMode ? (
                      <div className="py-4 space-y-2 lg:flex lg:items-stretch lg:gap-3 lg:space-y-0">
                      <div className="mb-5 lg:mb-0 lg:flex-1">
                        <div
                          ref={holderDropRef}
                          className={`relative flex min-h-24 w-full rounded-2xl border px-2 py-2 transition-colors lg:h-24 ${
                            isOverHolderDrop && dragSession?.source === "grid"
                              ? "border-primary/60 bg-primary/10 text-primary"
                              : "edit-drop-slot-surface-solid"
                          }`}
                        >
                          {heldTileIds.length > 0 ? (
                            <div className="flex w-full flex-wrap content-start gap-2">
                              {heldTileIds.map((holderTile) => (
                                <div
                                  key={`holder-tile-${activeViewport}-${holderTile.id}`}
                                  className="relative z-30 rounded-xl border border-blue-100 bg-[#f4f6fa] px-2 py-1.5 text-xs text-slate-700 shadow-sm"
                                  data-holder-menu
                                >
                                  <button
                                    type="button"
                                    onMouseDown={(event) => {
                                      if (event.button !== 0) return;
                                      event.preventDefault();
                                      const viewportColumns = viewportLayouts[activeViewport].targetColumns;
                                      const cellWidth = gridMetrics?.cellWidth ?? 120;
                                      const cellHeight = gridMetrics?.cellHeight ?? 132;
                                      const colGap = gridMetrics?.colGap ?? 12;
                                      const rowGap = gridMetrics?.rowGap ?? 12;
                                    const ghostColSpan = clamp(holderTile.returnColSpan ?? holderTile.colSpan, 1, viewportColumns);
                                    const ghostRowSpan = clamp(holderTile.returnRowSpan ?? holderTile.rowSpan, 1, MAX_ROW_SPAN);
                                      const ghostWidth = ghostColSpan * cellWidth + (ghostColSpan - 1) * colGap;
                                      const ghostHeight = ghostRowSpan * cellHeight + (ghostRowSpan - 1) * rowGap;

                                      setDraggingTileId(holderTile.id);
                                      setActiveDropSlot(null);
                                      setDragSession({
                                        source: "holder",
                                        tileId: holderTile.id,
                                        startX: event.clientX,
                                        startY: event.clientY,
                                        pointerOffsetX: Math.min(80, ghostWidth / 2),
                                        pointerOffsetY: 18,
                                        ghostWidth,
                                        ghostHeight,
                                        ghostColSpan,
                                        ghostRowSpan,
                                        anchorCol: 0,
                                        anchorRow: 0,
                                      });
                                      setDragPreview({
                                        tileId: holderTile.id,
                                        x: event.clientX - Math.min(80, ghostWidth / 2),
                                        y: event.clientY - 18,
                                        width: ghostWidth,
                                        height: ghostHeight,
                                      });
                                    }}
                                    className="pr-7 text-left"
                                    title="Drag back into the grid"
                                  >
                                    <span className="font-medium">Tile {holderTile.id}</span>
                                    <span className="ml-1 text-[11px] text-muted-foreground">{holderTile.colSpan}x{holderTile.rowSpan}</span>
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => setHolderMenuOpenId((previous) => (previous === holderTile.id ? null : holderTile.id))}
                                    className="absolute right-1 top-1 inline-flex h-5 w-5 items-center justify-center rounded-full border border-blue-100 bg-white text-slate-600 transition-colors hover:bg-blue-50"
                                    title="Storage options"
                                    aria-label="Storage options"
                                  >
                                    <Ellipsis className="h-3 w-3" />
                                  </button>
                                  {holderMenuOpenId === holderTile.id ? (
                                    <div className="absolute left-0 top-full z-[80] mt-1 w-44 rounded-xl border border-border bg-white p-1 shadow-lg">
                                      <div className="px-2 py-1 text-[11px] font-medium text-slate-500">
                                        Current: {holderTile.returnColSpan ?? holderTile.colSpan}x{holderTile.returnRowSpan ?? holderTile.rowSpan}
                                      </div>
                                      <div className="my-1 border-t border-border/80" />
                                      <button
                                        type="button"
                                        onClick={() => {
                                          setViewportHolders((previous) => ({
                                            ...previous,
                                            [activeViewport]: previous[activeViewport].map((item) =>
                                              item.id === holderTile.id
                                                ? {
                                                    ...item,
                                                    returnColSpan: holderTile.colSpan,
                                                    returnRowSpan: holderTile.rowSpan,
                                                  }
                                                : item,
                                            ),
                                          }));
                                          setHolderMenuOpenId(null);
                                        }}
                                        className="w-full rounded px-2 py-1.5 text-left text-xs transition-colors hover:bg-secondary/80 hover:text-foreground"
                                      >
                                        Return as original ({holderTile.colSpan}x{holderTile.rowSpan})
                                      </button>
                                      <button
                                        type="button"
                                        onClick={() => {
                                          setViewportHolders((previous) => ({
                                            ...previous,
                                            [activeViewport]: previous[activeViewport].map((item) =>
                                              item.id === holderTile.id
                                                ? {
                                                    ...item,
                                                    returnColSpan: 1,
                                                    returnRowSpan: 1,
                                                  }
                                                : item,
                                            ),
                                          }));
                                          setHolderMenuOpenId(null);
                                        }}
                                        className="w-full rounded px-2 py-1.5 text-left text-xs transition-colors hover:bg-secondary/80 hover:text-foreground"
                                      >
                                        Return as 1x1
                                      </button>
                                      <div className="my-1 border-t border-border/80" />
                                      <button
                                        type="button"
                                        onClick={() => {
                                          deleteTile(holderTile.id);
                                          setHolderMenuOpenId(null);
                                        }}
                                        className="w-full rounded px-2 py-1.5 text-left text-xs text-destructive transition-colors hover:bg-destructive/10"
                                      >
                                        Delete tile
                                      </button>
                                    </div>
                                  ) : null}
                                </div>
                              ))}
                            </div>
                          ) : (
                            <div className="edit-drop-slot-label m-auto px-2 text-center text-xs italic font-medium">
                              Drag tiles here to park while reorganizing in this view.
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="mt-3 flex flex-wrap items-center justify-center gap-2 lg:mt-0 lg:grid lg:w-[280px] lg:grid-cols-2 lg:gap-3 lg:items-stretch">
                        <button
                          type="button"
                          onClick={() => setIsAddTileDialogOpen(true)}
                          className="edit-add-tile-trigger inline-flex h-16 items-center justify-center gap-1 rounded-xl border px-2 py-2 text-xs font-semibold transition-colors lg:h-24 lg:w-full"
                          title="Add Tile"
                          aria-label="Add Tile"
                        >
                          <Plus className="h-3.5 w-3.5" />
                          <span>Add Tile</span>
                        </button>
                        <div className="relative lg:h-full lg:w-full" data-grid-add-menu>
                          <button
                            type="button"
                            onClick={() => setIsGridOptionsMenuOpen((previous) => !previous)}
                            className="inline-flex h-16 w-full items-center justify-center gap-1 rounded-xl border border-border bg-white px-2 py-2 text-xs font-semibold text-foreground transition-colors hover:bg-secondary/80 lg:h-24"
                            title="Grid options"
                            aria-label="Grid options"
                          >
                            <Grid2x2 className="h-3.5 w-3.5" />
                            <span>Grid Options</span>
                          </button>
                          {isGridOptionsMenuOpen ? (
                            <div className="absolute right-0 z-30 mt-1 w-44 rounded-xl border border-border bg-white p-1 shadow-lg dark:bg-popover">
                              <button
                                type="button"
                                onClick={() => {
                                  if (!canAddColumn) return;
                                  addColumnAtSide("left");
                                  setIsGridOptionsMenuOpen(false);
                                }}
                                disabled={!canAddColumn}
                                className="w-full rounded px-2 py-1.5 text-left text-xs transition-colors hover:bg-secondary/80 hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50"
                              >
                                Add Column (Left)
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  if (!canAddColumn) return;
                                  addColumnAtSide("right");
                                  setIsGridOptionsMenuOpen(false);
                                }}
                                disabled={!canAddColumn}
                                className="w-full rounded px-2 py-1.5 text-left text-xs transition-colors hover:bg-secondary/80 hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50"
                              >
                                Add Column (Right)
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  if (!canAddRow) return;
                                  addRowAtSide("top");
                                  setIsGridOptionsMenuOpen(false);
                                }}
                                disabled={!canAddRow}
                                className="w-full rounded px-2 py-1.5 text-left text-xs transition-colors hover:bg-secondary/80 hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50"
                              >
                                Add Row (Top)
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  if (!canAddRow) return;
                                  addRowAtSide("bottom");
                                  setIsGridOptionsMenuOpen(false);
                                }}
                                disabled={!canAddRow}
                                className="w-full rounded px-2 py-1.5 text-left text-xs transition-colors hover:bg-secondary/80 hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50"
                              >
                                Add Row (Bottom)
                              </button>
                            </div>
                          ) : null}
                        </div>
                      </div>
                      </div>
                      ) : null}
                      </div>
                      <div className={`mx-auto w-full ${editGridViewportWidthClass}`}>
                      <div className={`flex items-start px-2 pb-2 pt-0 ${isDeleteStructureMode ? "gap-2" : "gap-0"}`}>
                      <div className={`relative ${isDeleteStructureMode ? `hidden lg:block ${gridControlLeftSpacerDesktopClass}` : "w-0"}`} aria-hidden />
                      <div className="flex-1">
                        {isDeleteStructureMode ? (
                          <div className="relative mb-2 h-7">
                            {Array.from({ length: columns }, (_, colIndex) => {
                              const colCenter =
                                colIndex * ((gridMetrics?.cellWidth ?? 0) + (gridMetrics?.colGap ?? 0)) + (gridMetrics?.cellWidth ?? 0) / 2;
                              const deletable = columns > VIEWPORT_MIN_COLUMNS && deletableColumns.includes(colIndex);
                              const selected = selectedDeleteCols.includes(colIndex);
                              return (
                                <div
                                  key={`edit-col-del-${colIndex}`}
                                  className="absolute -translate-x-1/2"
                                  style={{ left: `${colCenter}px` }}
                                  onMouseEnter={() => {
                                    if (!deletable) return;
                                    setHoveredDeleteCol(colIndex);
                                  }}
                                  onMouseLeave={() => setHoveredDeleteCol((previous) => (previous === colIndex ? null : previous))}
                                >
                                  <div className="flex items-center justify-center gap-2">
                                    <button
                                      type="button"
                                      disabled={!deletable}
                                      onClick={() => {
                                        if (!deletable) return;
                                        if (selected) {
                                          setSelectedDeleteCols([]);
                                          return;
                                        }
                                        setSelectedDeleteCols([colIndex]);
                                      }}
                                      className={`inline-flex h-7 w-7 items-center justify-center rounded-full border font-semibold transition-colors ${
                                        selected
                                          ? "border-border bg-white text-foreground hover:border-foreground/50"
                                          : ""
                                      } ${
                                        !selected && deletable
                                          ? "border-border bg-white text-foreground hover:border-foreground/50 hover:text-foreground"
                                          : !selected
                                            ? "border-transparent bg-transparent text-muted-foreground/40"
                                            : ""
                                      }`}
                                      title={deletable ? (selected ? "Cancel column delete selection" : "Mark column for delete") : "Column currently occupied"}
                                    >
                                      {selected ? <X className="h-3.5 w-3.5" /> : <Trash2 className="h-3.5 w-3.5" />}
                                    </button>
                                    {selected ? (
                                      <button
                                        type="button"
                                        onClick={() => confirmDeleteStructure([], [colIndex])}
                                        className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-foreground bg-foreground text-background transition-colors hover:opacity-90"
                                        title="Delete column"
                                        aria-label="Delete column"
                                      >
                                        <Trash2 className="h-3.5 w-3.5" />
                                      </button>
                                    ) : null}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        ) : null}
                      <div className="relative overflow-visible pt-2">
                        <div
                          ref={gridRef}
                          className="grid auto-rows-[120px] gap-3 md:auto-rows-[132px]"
                          style={{ gridTemplateColumns: `repeat(${Math.max(1, columns)}, minmax(0, 1fr))` }}
                        >
                          {Array.from({ length: totalSlots }, (_, slot) => {
                            const slotPos = getGridPosition(slot, columns);
                            const selectedForDelete =
                              isDeleteStructureMode
                              && (
                                selectedDeleteRows.includes(slotPos.row)
                                || selectedDeleteCols.includes(slotPos.col)
                              );
                            const previewForDelete =
                              isDeleteStructureMode
                              && !selectedForDelete
                              && (
                                hoveredDeleteRow === slotPos.row
                                || hoveredDeleteCol === slotPos.col
                              );
                            return (
                            <div
                              key={`edit-slot-${slot}`}
                              className={
                                isEditing
                                  ? `rounded-xl border ${
                                      selectedForDelete
                                        ? "border-foreground/70 bg-transparent"
                                        : previewForDelete
                                          ? "border-foreground/40 bg-foreground/[0.04]"
                                        : activeDropSlot === slot
                                          ? "border-primary/60 bg-primary/10"
                                          : "edit-drop-slot"
                                    }`
                                  : "pointer-events-none rounded-xl border border-transparent bg-transparent"
                              }
                            >
                              <div className="edit-drop-slot-label flex h-full items-center justify-center rounded-lg text-xs">
                                {occupiedSlots.has(slot) ? "" : "Drop tile here"}
                              </div>
                            </div>
                            );
                          })}
                        </div>

                        <div
                          ref={overlayRef}
                          className="absolute inset-x-0 bottom-0 top-2 z-10"
                        >
                        {tiles.map((tile) => {
                          const resizeSnapPreview = resizePreview?.tileId === tile.id ? resizePreview : null;
                          const liveSlot = resizeSnapPreview ? resizeSnapPreview.slot : tile.slot;
                          const liveColSpan = resizeSnapPreview ? resizeSnapPreview.colSpan : tile.colSpan;
                          const liveRowSpan = resizeSnapPreview ? resizeSnapPreview.rowSpan : tile.rowSpan;
                          const pos = getGridPosition(liveSlot, columns);
                          const selectedDeleteHighlight =
                            isDeleteStructureMode
                            && (
                              selectedDeleteRows.some((row) => row >= pos.row && row < pos.row + liveRowSpan)
                              || selectedDeleteCols.some((col) => col >= pos.col && col < pos.col + liveColSpan)
                            );
                          const hoverDeleteHighlight =
                            isDeleteStructureMode
                            && (
                              (hoveredDeleteRow !== null && hoveredDeleteRow >= pos.row && hoveredDeleteRow < pos.row + liveRowSpan)
                              || (hoveredDeleteCol !== null && hoveredDeleteCol >= pos.col && hoveredDeleteCol < pos.col + liveColSpan)
                            );
                            const left = pos.col * (gridMetrics?.cellWidth ?? 0) + pos.col * (gridMetrics?.colGap ?? 0);
                            const top = pos.row * (gridMetrics?.cellHeight ?? 0) + pos.row * (gridMetrics?.rowGap ?? 0);
                            const snappedWidth =
                              liveColSpan * (gridMetrics?.cellWidth ?? 0) + (liveColSpan - 1) * (gridMetrics?.colGap ?? 0);
                            const snappedHeight =
                              liveRowSpan * (gridMetrics?.cellHeight ?? 0) + (liveRowSpan - 1) * (gridMetrics?.rowGap ?? 0);
                        const resizeLivePreview = resizeVisual?.tileId === tile.id ? resizeVisual : null;

                            return (
                              <div
                                key={`edit-tile-${tile.id}`}
                                ref={(element) => {
                                  tileRefs.current[tile.id] = element;
                                }}
                                onMouseDown={(event) => {
                                  if (!isEditing) return;
                                  if (event.button !== 0) return;
                                  if (resizeSession?.tileId === tile.id) return;
                                  if (!gridMetrics) return;
                                  event.preventDefault();
                                  setDraggingTileId(tile.id);
                                  setActiveDropSlot(null);
                                  const tileRect = event.currentTarget.getBoundingClientRect();
                                  const relativeX = event.clientX - tileRect.left;
                                  const relativeY = event.clientY - tileRect.top;
                                  const colStep = Math.max(1, snappedWidth / Math.max(1, tile.colSpan));
                                  const rowStep = Math.max(1, snappedHeight / Math.max(1, tile.rowSpan));
                                  const anchorCol = clamp(Math.floor(relativeX / colStep), 0, tile.colSpan - 1);
                                  const anchorRow = clamp(Math.floor(relativeY / rowStep), 0, tile.rowSpan - 1);

                                  setDragSession({
                                    source: "grid",
                                    tileId: tile.id,
                                    startX: event.clientX,
                                    startY: event.clientY,
                                    pointerOffsetX: relativeX,
                                    pointerOffsetY: relativeY,
                                    ghostWidth: snappedWidth,
                                    ghostHeight: snappedHeight,
                                    ghostColSpan: tile.colSpan,
                                    ghostRowSpan: tile.rowSpan,
                                    anchorCol,
                                    anchorRow,
                                  });
                                  setDragPreview({
                                    tileId: tile.id,
                                    x: event.clientX - relativeX,
                                    y: event.clientY - relativeY,
                                    width: snappedWidth,
                                    height: snappedHeight,
                                  });
                                }}
                                style={{
                                  left: `${resizeLivePreview ? resizeLivePreview.left : left}px`,
                                  top: `${resizeLivePreview ? resizeLivePreview.top : top}px`,
                                  width: `${resizeLivePreview ? resizeLivePreview.width : snappedWidth}px`,
                                  height: `${resizeLivePreview ? resizeLivePreview.height : snappedHeight}px`,
                                }}
                                className={`absolute rounded-xl border p-3 text-primary-foreground ${
                                  selectedDeleteHighlight
                                    ? "border-foreground/70 ring-2 ring-foreground/30 bg-primary"
                                    : hoverDeleteHighlight
                                      ? "border-foreground/45 bg-primary/95"
                                      : "border-primary/20 bg-primary"
                                } ${
                                  isEditing ? "cursor-grab active:cursor-grabbing" : "cursor-default"
                                } ${
                                  draggingTileId === tile.id ? "z-40 opacity-30" : "z-10"
                                }`}
                              >
                                <div className="flex h-full flex-col justify-between">
                                  <div className="text-xs font-medium uppercase tracking-wide opacity-80">Tile {tile.id}</div>
                                  <div className="text-[11px] opacity-85">
                                    {liveColSpan}x{liveRowSpan} tile
                                  </div>
                                </div>
                                {[
                                  { key: "tl", style: { left: "-8px", top: "-8px" }, cursor: "cursor-nwse-resize", icon: "rotate-180" },
                                  { key: "tr", style: { right: "-8px", top: "-8px" }, cursor: "cursor-nesw-resize", icon: "rotate-90" },
                                  { key: "bl", style: { left: "-8px", bottom: "-8px" }, cursor: "cursor-nesw-resize", icon: "-rotate-90" },
                                  { key: "br", style: { right: "-8px", bottom: "-8px" }, cursor: "cursor-se-resize", icon: "" },
                                ].map((handle) => (
                                  <button
                                    key={`edit-${tile.id}-${handle.key}`}
                                    type="button"
                                    onMouseDown={(event) => {
                                      event.preventDefault();
                                      event.stopPropagation();
                                      setResizeSession({
                                        tileId: tile.id,
                                        startX: event.clientX,
                                        startY: event.clientY,
                                        startSlot: tile.slot,
                                        startColSpan: tile.colSpan,
                                        startRowSpan: tile.rowSpan,
                                        startLeft: left,
                                        startTop: top,
                                        startWidth:
                                          tile.colSpan * (gridMetrics?.cellWidth ?? 0) + (tile.colSpan - 1) * (gridMetrics?.colGap ?? 0),
                                        startHeight:
                                          tile.rowSpan * (gridMetrics?.cellHeight ?? 0) + (tile.rowSpan - 1) * (gridMetrics?.rowGap ?? 0),
                                        handle: handle.key as "tl" | "tr" | "bl" | "br",
                                      });
                                      setResizePreview({
                                        tileId: tile.id,
                                        slot: tile.slot,
                                        colSpan: tile.colSpan,
                                        rowSpan: tile.rowSpan,
                                      });
                                    }}
                                    style={handle.style}
                                    className={`absolute z-20 inline-flex h-5 w-5 items-center justify-center rounded-md border-2 border-slate-300 bg-white text-slate-700 shadow-md ${handle.cursor}`}
                                    aria-label={`Resize tile ${tile.id}`}
                                    title="Resize"
                                  >
                                    <MoveDiagonal2 className={`pointer-events-none h-3 w-3 ${handle.icon}`} />
                                  </button>
                                ))}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                      </div>

                      <div className={`relative ${isDeleteStructureMode ? gridControlRailWidthClass : "w-0"}`}>
                        {Array.from({ length: totalRows }, (_, rowIndex) => {
                          if (!isDeleteStructureMode) return null;
                          const deletable = deletableRows.includes(rowIndex);
                          const top = rowIndex * ((gridMetrics?.cellHeight ?? 132) + (gridMetrics?.rowGap ?? 12));
                          const rowDeleteVerticalOffset = isDeleteStructureMode ? 44 : 0;
                          const selected = selectedDeleteRows.includes(rowIndex);
                          return (
                            <div
                              key={`edit-del-row-${rowIndex}`}
                              className="absolute left-0"
                              style={{ top: `${rowDeleteVerticalOffset + top + ((gridMetrics?.cellHeight ?? 132) / 2) - 12}px` }}
                              onMouseEnter={() => {
                                if (!deletable) return;
                                setHoveredDeleteRow(rowIndex);
                              }}
                              onMouseLeave={() => setHoveredDeleteRow((previous) => (previous === rowIndex ? null : previous))}
                            >
                              <div className={`flex items-center justify-center ${selected ? "flex-col gap-2 -translate-y-[14px]" : ""}`}>
                                <button
                                  type="button"
                                  disabled={!deletable}
                                  onClick={() => {
                                    if (!deletable) return;
                                    if (selected) {
                                      setSelectedDeleteRows([]);
                                      return;
                                    }
                                    setSelectedDeleteRows([rowIndex]);
                                  }}
                                  className={`inline-flex h-7 w-7 items-center justify-center rounded-full border font-semibold transition-colors ${
                                    selected
                                      ? "border-border bg-white text-foreground hover:border-foreground/50"
                                      : ""
                                  } ${
                                    !selected && deletable
                                      ? "border-border bg-white text-foreground hover:border-foreground/50 hover:text-foreground"
                                      : !selected
                                        ? "border-transparent bg-transparent text-muted-foreground/40"
                                        : ""
                                  }`}
                                  title={deletable ? (selected ? "Cancel row delete selection" : "Mark row for delete") : "Row currently occupied"}
                                >
                                  {selected ? <X className="h-3.5 w-3.5" /> : <Trash2 className="h-3.5 w-3.5" />}
                                </button>
                                {selected ? (
                                  <button
                                    type="button"
                                    onClick={() => confirmDeleteStructure([rowIndex], [])}
                                    className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-foreground bg-foreground text-background transition-colors hover:opacity-90"
                                    title="Delete row"
                                    aria-label="Delete row"
                                  >
                                    <Trash2 className="h-3.5 w-3.5" />
                                  </button>
                                ) : null}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                      </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
              </div>
            </div>
          </div>
        </div>
      ) : null}
      {isEditing && dragSession && dragPreview ? (
        <div
          className="pointer-events-none fixed z-[70] rounded-xl border border-primary/20 bg-primary/95 p-3 text-primary-foreground shadow-lg"
          style={{
            left: `${dragPreview.x}px`,
            top: `${dragPreview.y}px`,
            width: `${dragPreview.width}px`,
            height: `${dragPreview.height}px`,
          }}
        >
          <div className="flex h-full flex-col justify-between">
            <div className="text-xs font-medium uppercase tracking-wide opacity-80">Tile {dragPreview.tileId}</div>
            <div className="text-[11px] opacity-85">
              {dragSession.ghostColSpan}x{dragSession.ghostRowSpan} tile
            </div>
          </div>
        </div>
      ) : null}
      {isEditing && isNewLayoutDialogOpen ? (
        <div className="fixed inset-0 z-[80] flex items-center justify-center bg-slate-900/25 px-4">
          <Card className="w-full max-w-md border-border bg-white">
            <CardContent className="space-y-3 p-4">
              <p className="text-sm font-semibold text-slate-900">
                {layoutNameDialogMode === "rename" ? "Rename Layout" : "New Layout Name"}
              </p>
              <input
                type="text"
                value={pendingLayoutName}
                onChange={(event) => {
                  setPendingLayoutName(event.target.value);
                  if (layoutNameError) setLayoutNameError(null);
                }}
                className="w-full rounded-md border border-blue-100 bg-white px-3 py-2 text-sm text-foreground"
                placeholder={`${sectionLabel} Layout ${savedLayouts.length + 1}`}
                autoFocus
              />
              {layoutNameError ? <p className="text-xs text-red-700">{layoutNameError}</p> : null}
              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setIsNewLayoutDialogOpen(false);
                    setPendingLayoutName("");
                    setLayoutNameError(null);
                  }}
                  className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-border bg-white text-foreground transition-colors hover:bg-secondary/80"
                  title="Cancel"
                  aria-label="Cancel"
                >
                  <X className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const name = normalizeLayoutName(pendingLayoutName);
                    if (!name) {
                      setLayoutNameError("Layout name is required.");
                      return;
                    }
                    const isDuplicateName = savedLayouts.some((layout) =>
                      layoutNameDialogMode === "rename" && activeLayout
                        ? layout.id !== activeLayout.id && normalizeLayoutName(layout.name).toLowerCase() === name.toLowerCase()
                        : normalizeLayoutName(layout.name).toLowerCase() === name.toLowerCase(),
                    );
                    if (isDuplicateName) {
                      setLayoutNameError("A layout with this name already exists.");
                      return;
                    }
                    if (layoutNameDialogMode === "rename") {
                      renameActiveLayout(name);
                    } else {
                      createNewLayout(name);
                    }
                    setIsNewLayoutDialogOpen(false);
                    setPendingLayoutName("");
                    setLayoutNameError(null);
                  }}
                  className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-border bg-white text-foreground transition-colors hover:bg-secondary/80"
                  title="Save layout"
                  aria-label="Save layout"
                >
                  <Check className="h-4 w-4" />
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : null}
      {isEditing && isAddTileDialogOpen ? (
        <div className="fixed inset-0 z-[81] flex items-center justify-center bg-slate-900/25 px-4">
          <Card className="w-full max-w-lg border-border bg-white">
            <CardContent className="space-y-3 p-4">
              <p className="text-sm font-semibold text-slate-900">Add Tile Preset</p>
              <div className="space-y-2">
                {TILE_PRESETS.map((preset) => (
                  <button
                    key={`tile-preset-${preset.id}`}
                    type="button"
                    onClick={() => {
                      addTile(preset);
                      setIsAddTileDialogOpen(false);
                    }}
                    className="w-full rounded-lg border border-blue-100 bg-white px-3 py-2 text-left text-sm transition-colors hover:bg-blue-50"
                  >
                    <div className="font-medium text-slate-900">{preset.label}</div>
                    <div className="mt-0.5 text-xs text-slate-600">
                      Desktop {preset.spans.desktop.colSpan}x{preset.spans.desktop.rowSpan}
                      {" | "}
                      Tablet {preset.spans.tablet.colSpan}x{preset.spans.tablet.rowSpan}
                      {" | "}
                      Mobile {preset.spans.mobile.colSpan}x{preset.spans.mobile.rowSpan}
                    </div>
                  </button>
                ))}
              </div>
              <div className="flex items-center justify-end">
                <button
                  type="button"
                  onClick={() => setIsAddTileDialogOpen(false)}
                  className="rounded-md border border-border bg-white px-3 py-2 text-xs font-semibold text-foreground transition-colors hover:bg-secondary/80"
                >
                  Cancel
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : null}
      {isEditing && isSwitchLayoutDialogOpen ? (
        <div className="edit-dashboard-popup fixed inset-0 z-[82] flex items-center justify-center bg-slate-900/30 px-4">
          <Card className="w-full max-w-lg border-border bg-white">
            <CardContent className="space-y-3 p-4">
              <p className="text-sm font-semibold text-slate-900">
                Unsaved changes in the current layout. What do you want to do?
              </p>
              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={cancelLayoutSwitchDialog}
                  className="rounded-md border border-border bg-white px-3 py-2 text-xs font-semibold text-foreground transition-colors hover:bg-secondary/80"
                >
                  Keep Editing
                </button>
                <button
                  type="button"
                  onClick={confirmLayoutSwitchLose}
                  className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-900 transition-colors hover:bg-amber-100"
                >
                  Discard & Continue
                </button>
                <button
                  type="button"
                  onClick={confirmLayoutSwitchSave}
                  className="rounded-md border border-border bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground transition-colors hover:opacity-90"
                >
                  Save & Continue
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : null}
      {isSetActiveDialogOpen ? (
        <div className="edit-dashboard-popup fixed inset-0 z-[84] flex items-center justify-center bg-slate-900/30 px-4">
          <Card className="w-full max-w-lg border-border bg-white">
            <CardContent className="space-y-3 p-4">
              <p className="text-sm font-semibold text-slate-900">
                Make "{savedLayouts.find((layout) => layout.id === pendingSetActiveLayoutId)?.name ?? "this layout"}" active or keep the current active layout?
              </p>
              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={confirmKeepCurrentActive}
                  className="rounded-md border border-border bg-white px-3 py-2 text-xs font-semibold text-foreground transition-colors hover:bg-secondary/80"
                >
                  Keep Current Active
                </button>
                <button
                  type="button"
                  onClick={confirmMakeLayoutActive}
                  className="rounded-md border border-border bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground transition-colors hover:opacity-90"
                >
                  Make Layout Active
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : null}
      {isEditing && isExitBlockedDialogOpen ? (
        <div className="edit-dashboard-popup fixed inset-0 z-[84] flex items-center justify-center bg-slate-900/30 px-4">
          <Card className="w-full max-w-md border-border bg-white">
            <CardContent className="space-y-3 p-4">
              <p className="text-sm font-semibold text-slate-900">
                You cannot exit until the drag here area is empty.
              </p>
              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsExitBlockedDialogOpen(false)}
                  className="rounded-md border border-border bg-white px-3 py-2 text-xs font-semibold text-foreground transition-colors hover:bg-secondary/80"
                >
                  OK
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : null}
    </main>
  );
}

function createDefaultViewportLayouts(): ViewportLayouts {
  return {
    mobile: {
      tiles: DEFAULT_TILES.map((tile) => ({ ...tile })),
      targetRows: VIEWPORT_BASE_ROWS.mobile,
      targetColumns: VIEWPORT_DEFAULT_COLUMNS.mobile,
    },
    tablet: {
      tiles: DEFAULT_TILES.map((tile) => ({ ...tile })),
      targetRows: VIEWPORT_BASE_ROWS.tablet,
      targetColumns: VIEWPORT_DEFAULT_COLUMNS.tablet,
    },
    desktop: {
      tiles: DEFAULT_TILES.map((tile) => ({ ...tile })),
      targetRows: VIEWPORT_BASE_ROWS.desktop,
      targetColumns: VIEWPORT_DEFAULT_COLUMNS.desktop,
    },
  };
}

function createDefaultViewportHolders(): ViewportHolders {
  return {
    mobile: [],
    tablet: [],
    desktop: [],
  };
}

function normalizeViewportHolders(holders: Partial<ViewportHolders> | undefined): ViewportHolders {
  const normalizeOne = (items: Array<HolderTile | number> | undefined) => {
    const mapped = (items ?? []).map((item) => {
      if (typeof item === "number") {
        return { id: item, colSpan: 1, rowSpan: 1, returnColSpan: 1, returnRowSpan: 1 };
      }
      const colSpan = clamp(item.colSpan ?? 1, 1, VIEWPORT_MAX_COLUMNS.desktop);
      const rowSpan = clamp(item.rowSpan ?? 1, 1, MAX_ROW_SPAN);
      return {
        id: item.id,
        colSpan,
        rowSpan,
        returnColSpan: clamp(item.returnColSpan ?? colSpan, 1, VIEWPORT_MAX_COLUMNS.desktop),
        returnRowSpan: clamp(item.returnRowSpan ?? rowSpan, 1, MAX_ROW_SPAN),
      };
    });
    const unique = new Map<number, HolderTile>();
    mapped.forEach((item) => {
      unique.set(item.id, item);
    });
    return Array.from(unique.values());
  };

  return {
    mobile: normalizeOne(holders?.mobile as Array<HolderTile | number> | undefined),
    tablet: normalizeOne(holders?.tablet as Array<HolderTile | number> | undefined),
    desktop: normalizeOne(holders?.desktop as Array<HolderTile | number> | undefined),
  };
}

function createViewportLayoutsFromLegacy(tiles: DashboardTile[], targetRows: number): ViewportLayouts {
  const desktopColumns = VIEWPORT_DEFAULT_COLUMNS.desktop;
  const tabletColumns = VIEWPORT_DEFAULT_COLUMNS.tablet;
  const mobileColumns = VIEWPORT_DEFAULT_COLUMNS.mobile;
  const desktopNormalized = normalizeViewportLayoutForColumns(
    { tiles: tiles.map((tile) => ({ ...tile })), targetRows, targetColumns: desktopColumns },
    desktopColumns,
    desktopColumns,
    VIEWPORT_BASE_ROWS.desktop,
  );
  const desktopTiles = desktopNormalized.tiles;
  return normalizeAllViewportLayouts({
    desktop: desktopNormalized,
    tablet: {
      tiles: fitTilesToColumns(desktopTiles, desktopColumns, tabletColumns),
      targetRows: targetRows,
      targetColumns: tabletColumns,
    },
    mobile: {
      tiles: fitTilesToColumns(desktopTiles, desktopColumns, mobileColumns),
      targetRows: targetRows,
      targetColumns: mobileColumns,
    },
  });
}

function normalizeAllViewportLayouts(layouts: Partial<ViewportLayouts>): ViewportLayouts {
  const defaults = createDefaultViewportLayouts();
  const desktopTargetColumns = sanitizeColumns("desktop", layouts.desktop?.targetColumns ?? defaults.desktop.targetColumns);
  const tabletTargetColumns = sanitizeColumns("tablet", layouts.tablet?.targetColumns ?? defaults.tablet.targetColumns);
  const mobileTargetColumns = sanitizeColumns("mobile", layouts.mobile?.targetColumns ?? defaults.mobile.targetColumns);
  const desktopSource = layouts.desktop ?? defaults.desktop;
  const desktopNormalized = normalizeViewportLayoutForColumns(
    { ...desktopSource, targetColumns: desktopTargetColumns },
    sanitizeColumns("desktop", desktopSource.targetColumns ?? desktopTargetColumns),
    desktopTargetColumns,
    VIEWPORT_BASE_ROWS.desktop,
  );

  const tabletSource = layouts.tablet ?? {
    tiles: fitTilesToColumns(desktopNormalized.tiles, desktopNormalized.targetColumns, tabletTargetColumns),
    targetRows: desktopNormalized.targetRows,
    targetColumns: tabletTargetColumns,
  };
  const tabletNormalized = normalizeViewportLayoutForColumns(
    { ...tabletSource, targetColumns: tabletTargetColumns },
    sanitizeColumns("tablet", tabletSource.targetColumns ?? tabletTargetColumns),
    tabletTargetColumns,
    VIEWPORT_BASE_ROWS.tablet,
  );

  const mobileSource = layouts.mobile ?? {
    tiles: fitTilesToColumns(desktopNormalized.tiles, desktopNormalized.targetColumns, mobileTargetColumns),
    targetRows: desktopNormalized.targetRows,
    targetColumns: mobileTargetColumns,
  };
  const mobileNormalized = normalizeViewportLayoutForColumns(
    { ...mobileSource, targetColumns: mobileTargetColumns },
    sanitizeColumns("mobile", mobileSource.targetColumns ?? mobileTargetColumns),
    mobileTargetColumns,
    VIEWPORT_BASE_ROWS.mobile,
  );

  return {
    desktop: desktopNormalized,
    tablet: tabletNormalized,
    mobile: mobileNormalized,
  };
}

function normalizeViewportLayoutForColumns(
  layout: ViewportLayout,
  sourceColumns: number,
  targetColumns: number,
  minRows: number,
): ViewportLayout {
  const fittedTiles = fitTilesToColumns(layout.tiles, sourceColumns, targetColumns);
  const normalizedTiles = fittedTiles.map((tile) => ({ ...tile }));
  const trimmedTargetRows = Math.max(minRows, getRequiredRows(normalizedTiles, targetColumns), layout.targetRows);
  return {
    tiles: normalizedTiles,
    targetRows: trimmedTargetRows,
    targetColumns,
  };
}

function trimAllViewportLayoutsRows(layouts: ViewportLayouts): ViewportLayouts {
  return {
    mobile: trimViewportLayoutRows(layouts.mobile, layouts.mobile.targetColumns, VIEWPORT_BASE_ROWS.mobile),
    tablet: trimViewportLayoutRows(layouts.tablet, layouts.tablet.targetColumns, VIEWPORT_BASE_ROWS.tablet),
    desktop: trimViewportLayoutRows(layouts.desktop, layouts.desktop.targetColumns, VIEWPORT_BASE_ROWS.desktop),
  };
}

function trimViewportLayoutRows(layout: ViewportLayout, columns: number, minRows: number): ViewportLayout {
  if (layout.tiles.length === 0) {
    return { tiles: [], targetRows: minRows, targetColumns: columns };
  }

  const minUsedRow = Math.min(...layout.tiles.map((tile) => getGridPosition(tile.slot, columns).row));
  const shiftedTiles = layout.tiles.map((tile) => {
    const pos = getGridPosition(tile.slot, columns);
    return { ...tile, slot: (pos.row - minUsedRow) * columns + pos.col };
  });
  const compactedTiles = compactRowGaps(shiftedTiles, columns, 1);
  const requiredRows = getRequiredRows(compactedTiles, columns);

  return {
    tiles: compactedTiles,
    targetRows: Math.min(MAX_ROWS, Math.max(minRows, requiredRows)),
    targetColumns: columns,
  };
}

function compactRowGaps(tiles: DashboardTile[], columns: number, maxEmptyGap: number): DashboardTile[] {
  if (tiles.length === 0) return tiles;

  const maxRows = getRequiredRows(tiles, columns);
  const occupied = Array.from({ length: maxRows }, () => false);
  tiles.forEach((tile) => {
    const pos = getGridPosition(tile.slot, columns);
    for (let row = pos.row; row < pos.row + tile.rowSpan; row += 1) {
      if (row >= 0 && row < maxRows) occupied[row] = true;
    }
  });

  const removedBefore = Array.from({ length: maxRows }, () => 0);
  let removed = 0;
  let emptyRun = 0;

  for (let row = 0; row < maxRows; row += 1) {
    if (occupied[row]) {
      if (emptyRun > maxEmptyGap) {
        removed += emptyRun - maxEmptyGap;
      }
      emptyRun = 0;
      removedBefore[row] = removed;
    } else {
      emptyRun += 1;
      removedBefore[row] = removed;
    }
  }

  return tiles.map((tile) => {
    const pos = getGridPosition(tile.slot, columns);
    const newRow = Math.max(0, pos.row - removedBefore[pos.row]);
    return {
      ...tile,
      slot: newRow * columns + pos.col,
    };
  });
}

function fitTilesToColumns(tiles: DashboardTile[], sourceColumns: number, targetColumns: number): DashboardTile[] {
  const placed: DashboardTile[] = [];
  const sorted = [...tiles]
    .map((tile) => ({ ...tile }))
    .sort((a, b) => (a.slot - b.slot) || (a.id - b.id));

  sorted.forEach((tile) => {
    const sourcePos = getGridPosition(tile.slot, Math.max(1, sourceColumns));
    const colSpan = clamp(tile.colSpan, 1, targetColumns);
    const rowSpan = clamp(tile.rowSpan, 1, MAX_ROW_SPAN);
    const maxStartCol = Math.max(0, targetColumns - colSpan);
    const sourceRightEdge = sourcePos.col + tile.colSpan >= sourceColumns;
    const sourceLeftEdge = sourcePos.col <= 0;
    const scaledCol = Math.round((sourcePos.col / Math.max(1, sourceColumns - 1)) * Math.max(1, targetColumns - 1));
    const preferredCol = sourceRightEdge
      ? maxStartCol
      : sourceLeftEdge
        ? 0
        : clamp(scaledCol, 0, maxStartCol);

    let row = Math.max(0, sourcePos.row);
    let candidateSlot = row * targetColumns + preferredCol;
    while (!canPlaceTile(placed, null, candidateSlot, colSpan, rowSpan, targetColumns)) {
      row += 1;
      candidateSlot = row * targetColumns + preferredCol;
    }

    placed.push({
      ...tile,
      slot: candidateSlot,
      colSpan,
      rowSpan,
    });
  });

  return placed;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function sanitizeColumns(viewport: EditViewport, value: number | undefined) {
  const fallback = VIEWPORT_DEFAULT_COLUMNS[viewport];
  return clamp(value ?? fallback, VIEWPORT_MIN_COLUMNS, VIEWPORT_MAX_COLUMNS[viewport]);
}

function getGridPosition(slot: number, columns: number) {
  return {
    row: Math.floor(slot / columns),
    col: slot % columns,
  };
}

function getRequiredRows(tiles: DashboardTile[], columns: number) {
  if (tiles.length === 0) return 1;
  return Math.max(
    1,
    ...tiles.map((tile) => {
      const pos = getGridPosition(tile.slot, columns);
      return pos.row + tile.rowSpan;
    }),
  );
}

function isColumnOccupied(tiles: DashboardTile[], columns: number, colIndex: number) {
  return tiles.some((tile) => {
    const pos = getGridPosition(tile.slot, columns);
    return pos.col <= colIndex && pos.col + tile.colSpan - 1 >= colIndex;
  });
}

function isRowOccupied(tiles: DashboardTile[], columns: number, rowIndex: number) {
  return tiles.some((tile) => {
    const pos = getGridPosition(tile.slot, columns);
    return pos.row <= rowIndex && pos.row + tile.rowSpan - 1 >= rowIndex;
  });
}

function removeColumnsFromLayout(layout: ViewportLayout, removeCols: Set<number>, minRows: number): ViewportLayout {
  if (removeCols.size === 0) return layout;
  const oldColumns = layout.targetColumns;
  const newColumns = Math.max(VIEWPORT_MIN_COLUMNS, oldColumns - removeCols.size);

  const nextTiles = layout.tiles.map((tile) => {
    const pos = getGridPosition(tile.slot, oldColumns);
    let shift = 0;
    removeCols.forEach((removedCol) => {
      if (removedCol < pos.col) shift += 1;
    });
    const nextCol = Math.max(0, pos.col - shift);
    return {
      ...tile,
      slot: pos.row * newColumns + nextCol,
      colSpan: clamp(tile.colSpan, 1, newColumns),
    };
  });

  return {
    ...layout,
    tiles: nextTiles,
    targetColumns: newColumns,
    targetRows: Math.max(minRows, getRequiredRows(nextTiles, newColumns), layout.targetRows),
  };
}

function removeRowsFromLayout(layout: ViewportLayout, removeRows: Set<number>, minRows: number): ViewportLayout {
  if (removeRows.size === 0) return layout;
  const columns = layout.targetColumns;
  const removableRows = Array.from(removeRows)
    .filter((row) => row >= 0 && row < layout.targetRows)
    .filter((row) => !isRowOccupied(layout.tiles, columns, row))
    .sort((a, b) => a - b);
  if (removableRows.length === 0) return layout;

  const nextTiles = layout.tiles.map((tile) => {
    const pos = getGridPosition(tile.slot, columns);
    const shift = removableRows.filter((removedRow) => removedRow < pos.row).length;
    return {
      ...tile,
      slot: Math.max(0, pos.row - shift) * columns + pos.col,
    };
  });

  return {
    ...layout,
    tiles: nextTiles,
    targetRows: Math.max(minRows, getRequiredRows(nextTiles, columns), layout.targetRows - removableRows.length),
  };
}

function rectanglesOverlap(
  a: { row: number; col: number; rowSpan: number; colSpan: number },
  b: { row: number; col: number; rowSpan: number; colSpan: number },
) {
  return !(
    a.col + a.colSpan <= b.col ||
    b.col + b.colSpan <= a.col ||
    a.row + a.rowSpan <= b.row ||
    b.row + b.rowSpan <= a.row
  );
}

function canPlaceTile(
  tiles: DashboardTile[],
  movingTileId: number | null,
  targetSlot: number,
  colSpan: number,
  rowSpan: number,
  columns: number,
) {
  const targetPos = getGridPosition(targetSlot, columns);
  if (targetPos.col + colSpan > columns) return false;
  const targetRect = { row: targetPos.row, col: targetPos.col, colSpan, rowSpan };

  return tiles.every((tile) => {
    if (movingTileId !== null && tile.id === movingTileId) return true;
    const pos = getGridPosition(tile.slot, columns);
    const tileRect = { row: pos.row, col: pos.col, colSpan: tile.colSpan, rowSpan: tile.rowSpan };
    return !rectanglesOverlap(targetRect, tileRect);
  });
}

function getOccupiedSlots(tiles: DashboardTile[], columns: number) {
  const occupied = new Set<number>();
  tiles.forEach((tile) => {
    const pos = getGridPosition(tile.slot, columns);
    for (let r = 0; r < tile.rowSpan; r += 1) {
      for (let c = 0; c < tile.colSpan; c += 1) {
        occupied.add((pos.row + r) * columns + pos.col + c);
      }
    }
  });
  return occupied;
}

function getAlignedTopLeftSlot(
  hoveredSlot: number,
  anchorCol: number,
  anchorRow: number,
  tile: DashboardTile,
  columns: number,
) {
  const hoveredPos = getGridPosition(hoveredSlot, columns);
  const unclampedCol = hoveredPos.col - anchorCol;
  const unclampedRow = hoveredPos.row - anchorRow;
  const maxStartCol = Math.max(0, columns - tile.colSpan);
  const col = clamp(unclampedCol, 0, maxStartCol);
  const row = Math.max(0, unclampedRow);
  return row * columns + col;
}

function getSlotFromPoint(
  clientX: number,
  clientY: number,
  gridElement: HTMLDivElement,
  metrics: GridMetrics,
  columns: number,
) {
  const rect = gridElement.getBoundingClientRect();
  const x = clientX - rect.left;
  const y = clientY - rect.top;
  if (x < 0 || y < 0 || x > rect.width || y > rect.height) return null;

  const col = clamp(Math.floor(x / Math.max(1, metrics.cellWidth + metrics.colGap)), 0, columns - 1);
  const row = Math.max(0, Math.floor(y / Math.max(1, metrics.cellHeight + metrics.rowGap)));
  return row * columns + col;
}





























