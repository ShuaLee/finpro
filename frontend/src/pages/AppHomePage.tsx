import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Check,
  Columns3,
  Eye,
  MoreHorizontal,
  Monitor,
  MoveDiagonal2,
  Plus,
  Repeat2,
  Settings,
  Smartphone,
  Tablet,
  X,
} from "lucide-react";

import { getAccountsSidebar } from "../api/accounts";
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

type InsightTileView = {
  id: string;
  label: string;
  value: string;
  delta: string;
  hint: string;
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
const INSIGHT_TILE_VIEWS: InsightTileView[] = [
  {
    id: "total-value",
    label: "Total Portfolio Value",
    value: "$102,844.27",
    delta: "+4.2% this month",
    hint: "Your core holdings are driving most of this move.",
  },
  {
    id: "cash-position",
    label: "Available Cash",
    value: "$8,210.14",
    delta: "+$540.00 this week",
    hint: "Dry powder ready for new positions or transfers.",
  },
  {
    id: "income",
    label: "Projected Annual Income",
    value: "$3,904.55",
    delta: "+6.9% year-over-year",
    hint: "Dividend and interest projections are trending up.",
  },
];
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

export function AppHomePage() {
  const { user } = useAuth();
  const [activeSidebarCategory] = useState("portfolio");
  const [isEditing, setIsEditing] = useState(false);
  const [settingsMenuOpen, setSettingsMenuOpen] = useState(false);
  const [layoutsMenuOpen, setLayoutsMenuOpen] = useState(false);
  const [tileMenuOpenId, setTileMenuOpenId] = useState<number | null>(null);
  const [holderMenuOpenId, setHolderMenuOpenId] = useState<number | null>(null);
  const [isNewLayoutDialogOpen, setIsNewLayoutDialogOpen] = useState(false);
  const [isAddTileDialogOpen, setIsAddTileDialogOpen] = useState(false);
  const [layoutNameDialogMode, setLayoutNameDialogMode] = useState<"create" | "rename">("create");
  const [layoutActionsMenuOpen, setLayoutActionsMenuOpen] = useState(false);
  const [pendingLayoutName, setPendingLayoutName] = useState("");
  const [layoutNameError, setLayoutNameError] = useState<string | null>(null);
  const [isSwitchLayoutDialogOpen, setIsSwitchLayoutDialogOpen] = useState(false);
  const [pendingSwitchLayoutId, setPendingSwitchLayoutId] = useState<string | null>(null);
  const [pendingCreateLayout, setPendingCreateLayout] = useState(false);
  const [isExitEditDialogOpen, setIsExitEditDialogOpen] = useState(false);
  const [isSetActiveDialogOpen, setIsSetActiveDialogOpen] = useState(false);
  const [pendingSetActiveLayoutId, setPendingSetActiveLayoutId] = useState<string | null>(null);
  const [viewportLayouts, setViewportLayouts] = useState<ViewportLayouts>(() => createDefaultViewportLayouts());
  const [viewportHolders, setViewportHolders] = useState<ViewportHolders>(() => createDefaultViewportHolders());
  const [nextTileId, setNextTileId] = useState(2);
  const [insightTileIndex, setInsightTileIndex] = useState(0);
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
  const [isDeleteStructureMode, setIsDeleteStructureMode] = useState(false);
  const [selectedDeleteRows, setSelectedDeleteRows] = useState<number[]>([]);
  const [selectedDeleteCols, setSelectedDeleteCols] = useState<number[]>([]);
  const [gridActionsMenuOpen, setGridActionsMenuOpen] = useState(false);
  const [gridActionError, setGridActionError] = useState<string | null>(null);
  const gridRef = useRef<HTMLDivElement | null>(null);
  const gridScrollRef = useRef<HTMLDivElement | null>(null);
  const overlayRef = useRef<HTMLDivElement | null>(null);
  const holderDropRef = useRef<HTMLDivElement | null>(null);
  const tileRefs = useRef<Record<number, HTMLDivElement | null>>({});

  const displayViewport: EditViewport = windowWidth < 768 ? "mobile" : windowWidth < 1280 ? "tablet" : "desktop";
  const activeViewport: EditViewport = isEditing ? editingViewport : displayViewport;
  const columns = clamp(
    viewportLayouts[activeViewport]?.targetColumns ?? VIEWPORT_DEFAULT_COLUMNS[activeViewport],
    VIEWPORT_MIN_COLUMNS,
    VIEWPORT_MAX_COLUMNS[activeViewport],
  );
  const tiles = viewportLayouts[activeViewport].tiles;
  const targetRows = viewportLayouts[activeViewport].targetRows;
  const heldTileIds = viewportHolders[activeViewport];
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
  const activeInsightTile = INSIGHT_TILE_VIEWS[insightTileIndex];
  const sectionLabel = "Portfolio";
  const defaultLayoutName = `${sectionLabel} Default Layout`;
  const dashboardScope = activeSidebarCategory;
  const storageKey = `finpro.dashboard.layouts.${(user?.email ?? "anonymous").toLowerCase()}.${dashboardScope}`;

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
    localStorage.setItem(storageKey, JSON.stringify({ activeLayoutId: activeId, layouts: normalized }));
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
    if (hasUnsavedChanges) {
      setIsExitEditDialogOpen(true);
      return;
    }
    if (activeLayout && !activeLayout.isPrimary) {
      setPendingSetActiveLayoutId(activeLayout.id);
      setIsSetActiveDialogOpen(true);
      return;
    }
    setIsEditing(false);
  };

  const cancelExitEditDialog = () => {
    setIsExitEditDialogOpen(false);
  };

  const confirmExitEditSave = () => {
    const layout = savedLayouts.find((item) => item.id === activeLayoutId);
    const wasActive = Boolean(layout?.isPrimary);
    saveCurrentLayout(activeLayoutId, layout?.name ?? defaultLayoutName, false);
    setIsExitEditDialogOpen(false);
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
    if (activeLayout) {
      applyLayout(activeLayout);
    }
    if (activeLayout && !activeLayout.isPrimary) {
      setPendingSetActiveLayoutId(activeLayout.id);
      setIsSetActiveDialogOpen(true);
      setIsExitEditDialogOpen(false);
      return;
    }
    setIsEditing(false);
    setIsExitEditDialogOpen(false);
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

  const loadBrokerageAccounts = useCallback(async () => {
    try {
      await getAccountsSidebar();
    } catch {
      // Keep dashboard functional if accounts sidebar request fails.
    }
  }, []);

  useEffect(() => {
    const onDocClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement | null;
      if (!target) return;
      if (target.closest("[data-dashboard-menu]")) return;
      if (target.closest("[data-tile-menu]")) return;
      if (target.closest("[data-holder-menu]")) return;
      setSettingsMenuOpen(false);
      setLayoutsMenuOpen(false);
      setLayoutActionsMenuOpen(false);
      setGridActionsMenuOpen(false);
      setTileMenuOpenId(null);
      setHolderMenuOpenId(null);
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
    void loadBrokerageAccounts();
  }, [loadBrokerageAccounts, user?.email]);

  useEffect(() => {
    const raw = localStorage.getItem(storageKey);
    if (!raw) {
      const defaultLayout: SavedLayout = {
        id: DEFAULT_LAYOUT_ID,
        name: defaultLayoutName,
        viewportLayouts: createDefaultViewportLayouts(),
        viewportHolders: createDefaultViewportHolders(),
        isPrimary: true,
        updatedAt: new Date().toISOString(),
      };
      setSavedLayouts([defaultLayout]);
      setActiveLayoutId(defaultLayout.id);
      applyLayout(defaultLayout);
      persistLayouts([defaultLayout], defaultLayout.id);
      return;
    }

    try {
      const parsed = JSON.parse(raw) as { activeLayoutId?: string; layouts?: Array<SavedLayout & { tiles?: DashboardTile[]; targetRows?: number }> };
      const layoutsRaw = Array.isArray(parsed.layouts) && parsed.layouts.length > 0 ? parsed.layouts : [];
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
      if (layouts.length === 0) throw new Error("No layouts");
      const activeId = parsed.activeLayoutId && layouts.some((layout) => layout.id === parsed.activeLayoutId)
        ? parsed.activeLayoutId
        : layouts[0].id;
      const activeLayout = layouts.find((layout) => layout.id === activeId) ?? layouts[0];
      setSavedLayouts(layouts);
      setActiveLayoutId(activeId);
      applyLayout(activeLayout);
      persistLayouts(layouts, activeId);
    } catch {
      const fallback: SavedLayout = {
        id: DEFAULT_LAYOUT_ID,
        name: defaultLayoutName,
        viewportLayouts: createDefaultViewportLayouts(),
        viewportHolders: createDefaultViewportHolders(),
        isPrimary: true,
        updatedAt: new Date().toISOString(),
      };
      setSavedLayouts([fallback]);
      setActiveLayoutId(fallback.id);
      applyLayout(fallback);
      persistLayouts([fallback], fallback.id);
    } finally {
    }
  }, [defaultLayoutName, storageKey]);

  useEffect(() => {
    if (isEditing) return;
    setActiveDropSlot(null);
    setDraggingTileId(null);
    setDragSession(null);
    setDragPreview(null);
    setResizeSession(null);
    setResizePreview(null);
    setResizeVisual(null);
    setTileMenuOpenId(null);
    setHolderMenuOpenId(null);
    setIsOverHolderDrop(false);
    setIsAddTileDialogOpen(false);
    setIsNewLayoutDialogOpen(false);
    setIsSwitchLayoutDialogOpen(false);
    setPendingSwitchLayoutId(null);
    setIsDeleteStructureMode(false);
    setSelectedDeleteRows([]);
    setSelectedDeleteCols([]);
    setGridActionsMenuOpen(false);
    setGridActionError(null);
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
    const onResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    setSelectedDeleteRows([]);
    setSelectedDeleteCols([]);
    setGridActionError(null);
    setHolderMenuOpenId(null);
  }, [activeViewport]);

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
    setViewportLayouts((previous) => {
      const current = previous[activeViewport];
      const currentColumns = current.targetColumns;
      const maxColumns = VIEWPORT_MAX_COLUMNS[activeViewport];
      if (currentColumns >= maxColumns) return previous;
      const nextColumns = currentColumns + 1;
      const nextTiles = current.tiles.map((tile) => {
        const pos = getGridPosition(tile.slot, currentColumns);
        return {
          ...tile,
          slot: pos.row * nextColumns + pos.col,
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

  const confirmDeleteStructure = () => {
    setViewportLayouts((previous) => {
      const current = previous[activeViewport];
      let nextLayout: ViewportLayout = {
        ...current,
        tiles: current.tiles.map((tile) => ({ ...tile })),
      };

      if (selectedDeleteCols.length > 0 && nextLayout.targetColumns > VIEWPORT_MIN_COLUMNS) {
        const deletableCols = selectedDeleteCols
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

      if (selectedDeleteRows.length > 0) {
        const trailingEmptyRows = getTrailingEmptyRows(
          nextLayout.tiles,
          nextLayout.targetColumns,
          nextLayout.targetRows,
          VIEWPORT_BASE_ROWS[activeViewport],
        );
        const removableRows = selectedDeleteRows.filter((row) => trailingEmptyRows.includes(row));
        if (removableRows.length > 0) {
          const requiredRows = getRequiredRows(nextLayout.tiles, nextLayout.targetColumns);
          nextLayout = {
            ...nextLayout,
            targetRows: Math.max(
              VIEWPORT_BASE_ROWS[activeViewport],
              requiredRows,
              nextLayout.targetRows - removableRows.length,
            ),
          };
        }
      }

      return {
        ...previous,
        [activeViewport]: nextLayout,
      };
    });
    setSelectedDeleteRows([]);
    setSelectedDeleteCols([]);
    setIsDeleteStructureMode(false);
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
    setTileMenuOpenId(null);
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
  const trailingEmptyRows = getTrailingEmptyRows(tiles, columns, totalRows, viewportMinRows);
  const deletableColumns = Array.from({ length: columns }, (_, colIndex) => colIndex).filter(
    (colIndex) => !isColumnOccupied(tiles, columns, colIndex),
  );
  const editViewportIndex = editingViewport === "mobile" ? 0 : editingViewport === "tablet" ? 1 : 2;
  const editPreviewWidthClass =
    editingViewport === "mobile"
      ? "max-w-[420px]"
      : editingViewport === "tablet"
        ? "max-w-[900px]"
        : "max-w-[1320px]";
  const useCompactEditToolbar = windowWidth < 860 || editingViewport === "mobile";
  const useTabletEditToolbar = !useCompactEditToolbar && editingViewport === "tablet";

  return (
    <main className="w-full pb-10 pt-4">
      <div className="mx-auto w-full max-w-[1680px] px-4 sm:px-6 lg:px-8">
        <div>
          <section>
            <div className="grid grid-cols-1 gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
              <Card className="h-fit border-transparent bg-transparent shadow-none xl:sticky xl:top-24 xl:self-start">
                <CardContent className="p-0">
                  <Card className="border-border bg-[#f4f6fa]">
                    <CardContent className="space-y-4 p-4">
                      <Card className="border-blue-100 bg-white">
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between gap-3">
                            <h1 className="font-display text-2xl font-bold tracking-tight text-slate-900">Portfolio Dashboard</h1>
                            <div className="flex items-center gap-2">
                              <div className="relative" data-dashboard-menu>
                                <button
                                  type="button"
                                  onClick={() => {
                                    setLayoutsMenuOpen((previous) => !previous);
                                    setSettingsMenuOpen(false);
                                  }}
                                  className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-blue-100 bg-white text-muted-foreground transition-colors hover:bg-blue-50 hover:text-foreground"
                                >
                                  <Eye className="h-5 w-5" />
                                </button>
                                {layoutsMenuOpen ? (
                                  <div className="absolute right-0 z-50 mt-2 min-w-[19rem] max-w-[26rem] rounded-xl border border-border bg-white p-1 shadow-lg">
                                    <button
                                      type="button"
                                      onClick={() => {
                                        setPrimaryLayout(activeLayoutId);
                                        setLayoutsMenuOpen(false);
                                      }}
                                      className="w-full rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-secondary/80 hover:text-foreground"
                                    >
                                      Set Current as Active
                                    </button>
                                    <div className="my-1 border-t border-border/80" />
                                    {savedLayouts.map((layout) => (
                                      <button
                                        key={`rail-layout-${layout.id}`}
                                        type="button"
                                        onClick={() => {
                                          requestLayoutSwitch(layout.id);
                                          setLayoutsMenuOpen(false);
                                        }}
                                        className={`flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-secondary/80 hover:text-foreground ${
                                          layout.id === activeLayoutId ? "bg-secondary/50" : ""
                                        }`}
                                      >
                                        <span className="truncate pr-2" title={layout.name}>{getDisplayLayoutName(layout.name)}</span>
                                        <span className="text-[10px] text-muted-foreground">{layout.isPrimary ? "Active" : ""}</span>
                                      </button>
                                    ))}
                                  </div>
                                ) : null}
                              </div>
                              <div className="relative" data-dashboard-menu>
                                <button
                                  type="button"
                                  onClick={() => {
                                    setSettingsMenuOpen((previous) => !previous);
                                    setLayoutsMenuOpen(false);
                                  }}
                                  className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-blue-100 bg-white text-muted-foreground transition-colors hover:bg-blue-50 hover:text-foreground"
                                >
                                  <Settings className="h-5 w-5" />
                                </button>
                                {settingsMenuOpen ? (
                                  <div className="absolute right-0 z-50 mt-2 w-40 rounded-xl border border-border bg-white p-1 shadow-lg">
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
                          </div>
                        </CardContent>
                      </Card>
                      <Card className="border-blue-100 bg-white">
                        <CardContent className="space-y-4 p-4">
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Dashboard Tile</p>
                              <h2 className="mt-1 text-lg font-semibold text-slate-900">{activeInsightTile.label}</h2>
                            </div>
                            <button
                              type="button"
                              onClick={() =>
                                setInsightTileIndex((previous) => (previous + 1) % INSIGHT_TILE_VIEWS.length)}
                              className="inline-flex items-center gap-1 rounded-md border border-blue-200 bg-white px-3 py-1.5 text-xs font-semibold text-blue-700 transition-colors hover:bg-blue-50"
                            >
                              <Repeat2 className="h-3.5 w-3.5" />
                              Flip view
                            </button>
                          </div>
                          <div className="rounded-lg border border-blue-100 bg-white p-4">
                            <p className="text-3xl font-semibold text-slate-900">{activeInsightTile.value}</p>
                            <p className="mt-1 text-sm font-medium text-blue-700">{activeInsightTile.delta}</p>
                            <p className="mt-3 text-sm text-slate-600">{activeInsightTile.hint}</p>
                          </div>
                          <div className="h-2 w-full overflow-hidden rounded-full bg-blue-100/70">
                            <div
                              className="h-full rounded-full bg-blue-600 transition-all"
                              style={{ width: `${((insightTileIndex + 1) / INSIGHT_TILE_VIEWS.length) * 100}%` }}
                            />
                          </div>
                        </CardContent>
                      </Card>
                      <Card className="border-blue-100 bg-white">
                        <CardContent className="space-y-4 p-4">
                          <div>
                            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Dashboard Tile</p>
                            <h2 className="mt-1 text-lg font-semibold text-slate-900">Quick Actions</h2>
                          </div>
                          <div className="space-y-2">
                            {["Transfer funds", "Review subscriptions", "Manage accounts"].map((item) => (
                              <button
                                key={item}
                                type="button"
                                className="w-full rounded-md border border-blue-100 bg-white px-3 py-2 text-left text-sm font-medium text-slate-700 transition-colors hover:bg-blue-50 hover:text-blue-700"
                              >
                                {item}
                              </button>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    </CardContent>
                  </Card>
                </CardContent>
              </Card>
              {!isEditing ? (
                <Card className="overflow-visible border-border bg-[#f4f6fa]">
                  <CardContent className="min-h-[74vh] space-y-4 p-5">
                {isEditing ? (
                  <p className="text-sm text-muted-foreground">
                    Drag and resize tiles. Drop zones and row controls are edit-only.
                  </p>
                ) : null}
                <div className="flex items-start gap-2">
                  <div className="relative flex-1 overflow-hidden">
                    {isEditing && isDeleteStructureMode ? (
                      <div className="absolute left-0 right-0 top-1 z-30 h-7">
                        {Array.from({ length: columns }, (_, colIndex) => {
                          const colCenter =
                            colIndex * ((gridMetrics?.cellWidth ?? 0) + (gridMetrics?.colGap ?? 0)) + (gridMetrics?.cellWidth ?? 0) / 2;
                          const deletable = columns > VIEWPORT_MIN_COLUMNS && deletableColumns.includes(colIndex);
                          const selected = selectedDeleteCols.includes(colIndex);
                          return (
                            <button
                              key={`col-del-${colIndex}`}
                              type="button"
                              onClick={() => {
                                setSelectedDeleteCols((previous) =>
                                  previous.includes(colIndex)
                                    ? previous.filter((item) => item !== colIndex)
                                    : [...previous, colIndex],
                                );
                              }}
                              className="absolute inline-flex h-6 w-6 -translate-x-1/2 items-center justify-center rounded-md border-2 text-[10px] font-bold"
                              style={{
                                left: `${colCenter}px`,
                                borderColor: selected ? "#b91c1c" : deletable ? "#ef4444" : "#94a3b8",
                                backgroundColor: selected ? "#fecaca" : deletable ? "#fee2e2" : "#e2e8f0",
                                color: deletable ? "#b91c1c" : "#475569",
                              }}
                              title={deletable ? "Select column to delete" : "Column currently occupied"}
                            >
                              <X className="h-3.5 w-3.5" />
                            </button>
                          );
                        })}
                      </div>
                    ) : null}
                    <div
                      ref={gridRef}
                      className="grid auto-rows-[120px] gap-3 md:auto-rows-[132px]"
                      style={{ gridTemplateColumns: `repeat(${Math.max(1, columns)}, minmax(0, 1fr))` }}
                    >
                      {Array.from({ length: totalSlots }, (_, slot) => {
                        const slotPos = getGridPosition(slot, columns);
                        const selectedForDelete =
                          isDeleteStructureMode
                          && (selectedDeleteRows.includes(slotPos.row) || selectedDeleteCols.includes(slotPos.col));
                        return (
                        <div
                          key={`slot-${slot}`}
                          className={
                            isEditing
                              ? `rounded-xl border border-dashed ${
                                  selectedForDelete
                                    ? "border-red-400 bg-red-100/40"
                                    : activeDropSlot === slot
                                      ? "border-primary/60 bg-primary/10"
                                      : "border-border/60 bg-muted/15"
                                }`
                              : "pointer-events-none rounded-xl border border-transparent bg-transparent"
                          }
                        >
                          {isEditing ? (
                            <div className="flex h-full items-center justify-center rounded-lg text-xs text-muted-foreground">
                              {occupiedSlots.has(slot) ? "" : "Drop tile here"}
                            </div>
                          ) : null}
                        </div>
                      );
                      })}
                    </div>

                    <div
                      ref={overlayRef}
                      className="absolute inset-0 z-10"
                    >
                    {tiles.map((tile) => {
                      const resizeSnapPreview = resizePreview?.tileId === tile.id ? resizePreview : null;
                      const liveSlot = resizeSnapPreview ? resizeSnapPreview.slot : tile.slot;
                      const liveColSpan = resizeSnapPreview ? resizeSnapPreview.colSpan : tile.colSpan;
                      const liveRowSpan = resizeSnapPreview ? resizeSnapPreview.rowSpan : tile.rowSpan;
                      const pos = getGridPosition(liveSlot, columns);
                      const deleteHighlight =
                        isDeleteStructureMode
                        && (selectedDeleteRows.some((row) => row >= pos.row && row < pos.row + liveRowSpan)
                          || selectedDeleteCols.some((col) => col >= pos.col && col < pos.col + liveColSpan));
                        const left = pos.col * (gridMetrics?.cellWidth ?? 0) + pos.col * (gridMetrics?.colGap ?? 0);
                        const top = pos.row * (gridMetrics?.cellHeight ?? 0) + pos.row * (gridMetrics?.rowGap ?? 0);
                        const snappedWidth =
                          liveColSpan * (gridMetrics?.cellWidth ?? 0) + (liveColSpan - 1) * (gridMetrics?.colGap ?? 0);
                            const snappedHeight =
                              liveRowSpan * (gridMetrics?.cellHeight ?? 0) + (liveRowSpan - 1) * (gridMetrics?.rowGap ?? 0);
                            const resizeLivePreview = resizeVisual?.tileId === tile.id ? resizeVisual : null;

                        return (
                          <div
                            key={`tile-${tile.id}`}
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
                            className={`absolute rounded-xl border p-3 text-primary-foreground shadow-sm ${
                              deleteHighlight ? "border-red-300 bg-red-400/85" : "border-primary/20 bg-primary"
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
                            {isEditing
                              ? [
                              { key: "tl", style: { left: "-8px", top: "-8px" }, cursor: "cursor-nwse-resize", icon: "rotate-180" },
                              { key: "tr", style: { right: "-8px", top: "-8px" }, cursor: "cursor-nesw-resize", icon: "rotate-90" },
                              { key: "bl", style: { left: "-8px", bottom: "-8px" }, cursor: "cursor-nesw-resize", icon: "-rotate-90" },
                              { key: "br", style: { right: "-8px", bottom: "-8px" }, cursor: "cursor-se-resize", icon: "" },
                            ].map((handle) => (
                              <button
                                key={`${tile.id}-${handle.key}`}
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
                            ))
                              : null}
                          </div>
                        );
                      })}
                    </div>
                  </div>

                    {isEditing && isDeleteStructureMode ? (
                      <div className="relative w-8">
                        {Array.from({ length: totalRows }, (_, rowIndex) => {
                          const deletable = trailingEmptyRows.includes(rowIndex);
                          const top = rowIndex * ((gridMetrics?.cellHeight ?? 132) + (gridMetrics?.rowGap ?? 12));
                          const selected = selectedDeleteRows.includes(rowIndex);
                          return (
                            <button
                              key={`del-row-${rowIndex}`}
                              type="button"
                              onClick={() => {
                                setSelectedDeleteRows((previous) =>
                                  previous.includes(rowIndex) ? previous.filter((item) => item !== rowIndex) : [...previous, rowIndex],
                                );
                              }}
                              className="absolute left-0 inline-flex h-6 w-6 items-center justify-center rounded-md border-2 text-[10px] font-bold hover:opacity-90"
                              style={{
                                top: `${top + ((gridMetrics?.cellHeight ?? 132) / 2) - 12}px`,
                                borderColor: selected ? "#b91c1c" : deletable ? "#ef4444" : "#94a3b8",
                                backgroundColor: selected ? "#fecaca" : deletable ? "#fee2e2" : "#e2e8f0",
                                color: deletable ? "#b91c1c" : "#475569",
                              }}
                              title={deletable ? "Select row to delete" : "Only trailing empty rows can be deleted"}
                            >
                              <X className="h-3.5 w-3.5" />
                            </button>
                          );
                        })}
                      </div>
                    ) : null}
                  </div>
                {isEditing ? (
                  <div className="flex w-full items-center gap-3">
                    <ul className="flex items-center gap-1 text-xs text-muted-foreground">
                      <li>rows:{totalRows}</li>
                      <li>|</li>
                      <li>tiles:{tiles.length}</li>
                    </ul>
                    <div className="h-[1px] flex-1" style={{ backgroundColor: "rgba(22,163,74,0.35)" }} />
                    <button
                      type="button"
                      onClick={() => {
                        if (!canAddRow) return;
                        setTargetRows((previous) => previous + 1);
                      }}
                      className={`inline-flex items-center rounded-md border px-3 py-1.5 text-xs font-semibold ${
                        canAddRow ? "hover:opacity-90" : "cursor-not-allowed opacity-55"
                      }`}
                      style={{
                        backgroundColor: "rgba(22,163,74,0.14)",
                        borderColor: "rgba(21,128,61,0.35)",
                        color: "#166534",
                      }}
                      title={canAddRow ? "Add Row" : "Max blank rows reached"}
                    >
                      Add Row
                    </button>
                    <div className="h-[1px] flex-1" style={{ backgroundColor: "rgba(22,163,74,0.35)" }} />
                    <ul className="flex items-center gap-1 text-xs text-muted-foreground">
                      <li>min:1</li>
                      <li>|</li>
                      <li>set:{targetRows}</li>
                    </ul>
                  </div>
                ) : null}
                  </CardContent>
                </Card>
              ) : null}
            </div>
          </section>
        </div>
      </div>
      {isEditing ? (
        <div className="fixed inset-x-0 bottom-0 top-20 z-50 bg-slate-900/25 backdrop-blur-[4px]">
          <div className="mx-auto h-full w-full max-w-[1680px] overflow-y-auto px-4 py-4 sm:px-6 lg:px-8">
            <div className="space-y-3">
              <div className="flex justify-center">
                <div className={`h-[calc(100vh-7rem)] w-full ${editPreviewWidthClass}`}>
                <Card className="h-full overflow-hidden border-border bg-[#f4f6fa]">
                  <CardContent className="flex h-full flex-col gap-4 overflow-hidden p-5">
                    <div ref={gridScrollRef} className="min-h-0 flex-1 overflow-auto pr-1">
                    {useCompactEditToolbar ? (
                    <div className="space-y-3">
                      <div className="flex justify-center">
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
                      <div className="space-y-2">
                        <div className="flex items-center justify-end gap-2">
                          <span
                            className={`rounded-md border px-2.5 py-1 text-xs font-semibold ${
                              hasUnsavedChanges
                                ? "border-amber-200 bg-amber-50 text-amber-900"
                                : "border-blue-200 bg-blue-50 text-blue-800"
                            }`}
                          >
                            {hasUnsavedChanges ? "Unsaved Changes" : "No Changes"}
                          </span>
                          <button
                            type="button"
                            onClick={requestExitEditing}
                            className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-border bg-white text-foreground transition-colors hover:bg-secondary/80 disabled:cursor-not-allowed disabled:opacity-55"
                            title="Save and close"
                            aria-label="Save and close"
                          >
                            <Check className="h-4 w-4" />
                          </button>
                        </div>
                        <div>
                          <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Layout</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <select
                            value={activeLayoutId}
                            onChange={(event) => requestLayoutSwitch(event.target.value)}
                            className="min-w-0 flex-1 rounded-xl border border-blue-100 bg-white px-2 py-1.5 text-sm text-foreground"
                          >
                            {savedLayouts.map((layout) => (
                              <option key={`dashboard-layout-select-mobile-${layout.id}`} value={layout.id}>
                                {getDisplayLayoutName(layout.name)}{layout.isPrimary ? " (Active)" : ""}
                              </option>
                            ))}
                          </select>
                          <div className="relative" data-dashboard-menu>
                            <button
                              type="button"
                              onClick={() => setLayoutActionsMenuOpen((previous) => !previous)}
                              className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-border bg-white text-foreground transition-colors hover:bg-secondary/80"
                              title="Layout actions"
                              aria-label="Layout actions"
                            >
                              <MoreHorizontal className="h-4 w-4" />
                            </button>
                            {layoutActionsMenuOpen ? (
                              <div className="absolute right-0 z-50 mt-2 w-52 rounded-xl border border-border bg-white p-1 shadow-lg">
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
                        </div>
                      </div>
                    </div>
                    ) : useTabletEditToolbar ? (
                    <div className="space-y-3">
                      <div className="flex justify-center">
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
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Layout</span>
                            <select
                              value={activeLayoutId}
                              onChange={(event) => requestLayoutSwitch(event.target.value)}
                              className="min-w-0 max-w-[360px] flex-1 rounded-xl border border-blue-100 bg-white px-2 py-1.5 text-sm text-foreground"
                            >
                              {savedLayouts.map((layout) => (
                                <option key={`dashboard-layout-select-tablet-${layout.id}`} value={layout.id}>
                                  {getDisplayLayoutName(layout.name)}{layout.isPrimary ? " (Active)" : ""}
                                </option>
                              ))}
                            </select>
                            <div className="relative" data-dashboard-menu>
                              <button
                                type="button"
                                onClick={() => setLayoutActionsMenuOpen((previous) => !previous)}
                                className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-border bg-white text-foreground transition-colors hover:bg-secondary/80"
                                title="Layout actions"
                                aria-label="Layout actions"
                              >
                                <MoreHorizontal className="h-4 w-4" />
                              </button>
                              {layoutActionsMenuOpen ? (
                                <div className="absolute left-0 z-50 mt-2 w-52 rounded-xl border border-border bg-white p-1 shadow-lg">
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
                          </div>
                        </div>
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
                          <button
                            type="button"
                            onClick={requestExitEditing}
                            className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-border bg-white text-foreground transition-colors hover:bg-secondary/80 disabled:cursor-not-allowed disabled:opacity-55"
                            title="Save and close"
                            aria-label="Save and close"
                          >
                            <Check className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                    ) : (
                    <div className="grid items-center gap-4 md:grid-cols-[minmax(0,1fr)_auto] xl:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)]">
                      <div className="flex flex-col gap-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Layout</span>
                          <select
                            value={activeLayoutId}
                            onChange={(event) => requestLayoutSwitch(event.target.value)}
                            className="w-full min-w-0 rounded-xl border border-blue-100 bg-white px-2 py-1.5 text-sm text-foreground sm:w-auto sm:min-w-[220px]"
                          >
                            {savedLayouts.map((layout) => (
                              <option key={`dashboard-layout-select-${layout.id}`} value={layout.id}>
                                {getDisplayLayoutName(layout.name)}{layout.isPrimary ? " (Active)" : ""}
                              </option>
                            ))}
                          </select>
                          <div className="relative" data-dashboard-menu>
                            <button
                              type="button"
                              onClick={() => setLayoutActionsMenuOpen((previous) => !previous)}
                              className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-border bg-white text-foreground transition-colors hover:bg-secondary/80"
                              title="Layout actions"
                              aria-label="Layout actions"
                            >
                              <MoreHorizontal className="h-4 w-4" />
                            </button>
                            {layoutActionsMenuOpen ? (
                              <div className="absolute left-0 z-50 mt-2 w-52 rounded-xl border border-border bg-white p-1 shadow-lg">
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
                        </div>
                      </div>
                      <div className="justify-self-center w-full md:w-auto">
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
                      <div className="flex items-center justify-end gap-3 md:col-span-2 xl:col-span-1">
                        <span
                          className={`rounded-md border px-2.5 py-1 text-xs font-semibold ${
                            hasUnsavedChanges
                              ? "border-amber-200 bg-amber-50 text-amber-900"
                              : "border-blue-200 bg-blue-50 text-blue-800"
                          }`}
                        >
                          {hasUnsavedChanges ? "Unsaved Changes" : "No Changes"}
                        </span>
                        <button
                          type="button"
                          onClick={requestExitEditing}
                          className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-border bg-white text-foreground transition-colors hover:bg-secondary/80 disabled:cursor-not-allowed disabled:opacity-55"
                          title="Save and close"
                          aria-label="Save and close"
                        >
                          <Check className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                    )}
                      <div className="sticky top-0 z-[90] isolate mb-2 mt-3 space-y-2 bg-[#f4f6fa] pb-2">
                      <div className="min-h-24 rounded-2xl border border-blue-200 bg-white p-3">
                        <div className="mb-2">
                          <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">Tile Storage</p>
                          <p className="mt-1 text-xs text-muted-foreground">
                            Drag tiles here to hide for this display size while keeping for others, or park while reorganizing.
                          </p>
                        </div>
                        <div
                          ref={holderDropRef}
                          className={`mb-2 flex h-10 items-center justify-center rounded-xl border border-dashed transition-colors ${
                            isOverHolderDrop && dragSession?.source === "grid"
                              ? "border-primary/60 bg-primary/10 text-primary"
                              : "border-blue-200 bg-[#f8fafc] text-slate-500"
                          }`}
                        >
                          <div className="inline-flex items-center gap-1 text-xs font-medium">
                            <Plus className="h-3.5 w-3.5" />
                            <span>Drop to store</span>
                          </div>
                        </div>
                        {heldTileIds.length > 0 ? (
                          <div className="flex flex-wrap gap-2">
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
                                  <MoreHorizontal className="h-3 w-3" />
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
                        ) : null}
                      </div>
                      <div className="flex items-center justify-center gap-3 pb-2 pt-3">
                        <button
                          type="button"
                          onClick={() => setIsAddTileDialogOpen(true)}
                          className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-border bg-white text-foreground transition-colors hover:bg-secondary/80"
                          title="Add Tile"
                          aria-label="Add Tile"
                        >
                          <Plus className="h-4 w-4" />
                        </button>
                        <div className="relative" data-dashboard-menu>
                          <button
                            type="button"
                            onClick={() => setGridActionsMenuOpen((previous) => !previous)}
                            className={`inline-flex h-9 w-9 items-center justify-center rounded-full border transition-colors ${
                              isDeleteStructureMode
                                ? "border-red-300 bg-red-100 text-red-700"
                                : "border-border bg-white text-foreground hover:bg-secondary/80"
                            }`}
                            title="Grid actions"
                            aria-label="Grid actions"
                          >
                            <Columns3 className="h-4 w-4" />
                          </button>
                          {gridActionsMenuOpen ? (
                            <div className="absolute left-1/2 z-50 mt-2 w-44 -translate-x-1/2 rounded-xl border border-border bg-white p-1 shadow-lg">
                              <button
                                type="button"
                                onClick={() => {
                                  if (columns >= VIEWPORT_MAX_COLUMNS[activeViewport]) {
                                    setGridActionError("maximum columns reached for this display size.");
                                  } else {
                                    addColumn();
                                    setGridActionError(null);
                                  }
                                  setGridActionsMenuOpen(false);
                                }}
                                className="w-full rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-secondary/80 hover:text-foreground"
                              >
                                Add Column
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  if (canAddRow) {
                                    setTargetRows((previous) => Math.min(MAX_ROWS, previous + 1));
                                  }
                                  setGridActionError(null);
                                  setGridActionsMenuOpen(false);
                                }}
                                disabled={!canAddRow}
                                className="w-full rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-secondary/80 hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50"
                              >
                                Add Row
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  setIsDeleteStructureMode((previous) => {
                                    const next = !previous;
                                    if (!next) {
                                      setSelectedDeleteRows([]);
                                      setSelectedDeleteCols([]);
                                    }
                                    return next;
                                  });
                                  setGridActionError(null);
                                  setGridActionsMenuOpen(false);
                                }}
                                className="w-full rounded px-2 py-1.5 text-left text-sm text-red-700 transition-colors hover:bg-red-50"
                              >
                                {isDeleteStructureMode ? "Exit Delete Mode" : "Delete Rows/Columns"}
                              </button>
                            </div>
                          ) : null}
                        </div>
                        {isDeleteStructureMode ? (
                          <>
                            <button
                              type="button"
                              onClick={() => {
                                setIsDeleteStructureMode(false);
                                setSelectedDeleteRows([]);
                                setSelectedDeleteCols([]);
                              }}
                              className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-border bg-white text-foreground transition-colors hover:bg-secondary/80"
                              title="Cancel"
                              aria-label="Cancel"
                            >
                              <X className="h-4 w-4" />
                            </button>
                            <button
                              type="button"
                              onClick={confirmDeleteStructure}
                              disabled={selectedDeleteRows.length === 0 && selectedDeleteCols.length === 0}
                              className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-border bg-primary text-primary-foreground transition-colors hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-55"
                              title="Confirm delete"
                              aria-label="Confirm delete"
                            >
                              <Check className="h-4 w-4" />
                            </button>
                          </>
                        ) : null}
                      </div>
                      {gridActionError ? (
                        <p className="text-center text-xs text-red-700">{gridActionError}</p>
                      ) : null}
                      </div>
                      <div className="flex items-start gap-2 px-2 pb-2 pt-0">
                      <div className="relative flex-1 overflow-visible pt-2">
                        {isDeleteStructureMode ? (
                          <div className="absolute left-0 right-0 top-1 z-30 h-7">
                            {Array.from({ length: columns }, (_, colIndex) => {
                              const colCenter =
                                colIndex * ((gridMetrics?.cellWidth ?? 0) + (gridMetrics?.colGap ?? 0)) + (gridMetrics?.cellWidth ?? 0) / 2;
                              const deletable = columns > VIEWPORT_MIN_COLUMNS && deletableColumns.includes(colIndex);
                              const selected = selectedDeleteCols.includes(colIndex);
                              return (
                                <button
                                  key={`edit-col-del-${colIndex}`}
                                  type="button"
                                  onClick={() => {
                                    setSelectedDeleteCols((previous) =>
                                      previous.includes(colIndex)
                                        ? previous.filter((item) => item !== colIndex)
                                        : [...previous, colIndex],
                                    );
                                  }}
                                  className="absolute inline-flex h-6 w-6 -translate-x-1/2 items-center justify-center rounded-md border-2 text-[10px] font-bold"
                                  style={{
                                    left: `${colCenter}px`,
                                    borderColor: selected ? "#b91c1c" : deletable ? "#ef4444" : "#94a3b8",
                                    backgroundColor: selected ? "#fecaca" : deletable ? "#fee2e2" : "#e2e8f0",
                                    color: deletable ? "#b91c1c" : "#475569",
                                  }}
                                  title={deletable ? "Select column to delete" : "Column currently occupied"}
                                >
                                  <X className="h-3.5 w-3.5" />
                                </button>
                              );
                            })}
                          </div>
                        ) : null}
                        <div
                          ref={gridRef}
                          className="grid auto-rows-[120px] gap-3 md:auto-rows-[132px]"
                          style={{ gridTemplateColumns: `repeat(${Math.max(1, columns)}, minmax(0, 1fr))` }}
                        >
                          {Array.from({ length: totalSlots }, (_, slot) => {
                            const slotPos = getGridPosition(slot, columns);
                            const selectedForDelete =
                              isDeleteStructureMode
                              && (selectedDeleteRows.includes(slotPos.row) || selectedDeleteCols.includes(slotPos.col));
                            return (
                            <div
                              key={`edit-slot-${slot}`}
                              className={
                                isEditing
                                  ? `rounded-xl border border-dashed ${
                                      selectedForDelete
                                        ? "border-red-400 bg-red-100/40"
                                        : activeDropSlot === slot
                                          ? "border-primary/60 bg-primary/10"
                                          : "border-border/60 bg-muted/15"
                                    }`
                                  : "pointer-events-none rounded-xl border border-transparent bg-transparent"
                              }
                            >
                              <div className="flex h-full items-center justify-center rounded-lg text-xs text-muted-foreground">
                                {occupiedSlots.has(slot) ? "" : "Drop tile here"}
                              </div>
                            </div>
                            );
                          })}
                        </div>

                        <div
                          ref={overlayRef}
                          className="absolute inset-0 z-10"
                        >
                        {tiles.map((tile) => {
                          const resizeSnapPreview = resizePreview?.tileId === tile.id ? resizePreview : null;
                          const liveSlot = resizeSnapPreview ? resizeSnapPreview.slot : tile.slot;
                          const liveColSpan = resizeSnapPreview ? resizeSnapPreview.colSpan : tile.colSpan;
                          const liveRowSpan = resizeSnapPreview ? resizeSnapPreview.rowSpan : tile.rowSpan;
                          const pos = getGridPosition(liveSlot, columns);
                          const deleteHighlight =
                            isDeleteStructureMode
                            && (selectedDeleteRows.some((row) => row >= pos.row && row < pos.row + liveRowSpan)
                              || selectedDeleteCols.some((col) => col >= pos.col && col < pos.col + liveColSpan));
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
                                className={`absolute rounded-xl border p-3 text-primary-foreground shadow-sm ${
                                  deleteHighlight ? "border-red-300 bg-red-400/85" : "border-primary/20 bg-primary"
                                } ${
                                  isEditing ? "cursor-grab active:cursor-grabbing" : "cursor-default"
                                } ${
                                  draggingTileId === tile.id ? "z-40 opacity-30" : "z-10"
                                }`}
                              >
                                <div className="absolute left-1/2 top-2 z-30 -translate-x-1/2" data-tile-menu>
                                  <button
                                    type="button"
                                    onMouseDown={(event) => {
                                      event.preventDefault();
                                      event.stopPropagation();
                                    }}
                                    onClick={(event) => {
                                      event.preventDefault();
                                      event.stopPropagation();
                                      setTileMenuOpenId((previous) => (previous === tile.id ? null : tile.id));
                                    }}
                                    className="inline-flex h-6 w-6 items-center justify-center rounded-full border border-white/70 bg-white/90 text-slate-700 transition-colors hover:bg-white"
                                    aria-label={`Open tile ${tile.id} menu`}
                                  >
                                    <MoreHorizontal className="h-3.5 w-3.5" />
                                  </button>
                                  {tileMenuOpenId === tile.id ? (
                                    <div className="absolute left-1/2 top-7 z-40 w-28 -translate-x-1/2 rounded-xl border border-border bg-white p-1 shadow-lg">
                                      <button
                                        type="button"
                                        onMouseDown={(event) => {
                                          event.preventDefault();
                                          event.stopPropagation();
                                        }}
                                        onClick={(event) => {
                                          event.preventDefault();
                                          event.stopPropagation();
                                          deleteTile(tile.id);
                                        }}
                                        className="w-full rounded px-2 py-1.5 text-left text-xs text-destructive transition-colors hover:bg-destructive/10"
                                      >
                                        Delete tile
                                      </button>
                                    </div>
                                  ) : null}
                                </div>
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

                      <div className="relative w-8">
                        {Array.from({ length: totalRows }, (_, rowIndex) => {
                          if (!isDeleteStructureMode) return null;
                          const deletable = trailingEmptyRows.includes(rowIndex);
                          const top = rowIndex * ((gridMetrics?.cellHeight ?? 132) + (gridMetrics?.rowGap ?? 12));
                          const selected = selectedDeleteRows.includes(rowIndex);
                          return (
                            <button
                              key={`edit-del-row-${rowIndex}`}
                              type="button"
                              onClick={() => {
                                setSelectedDeleteRows((previous) =>
                                  previous.includes(rowIndex) ? previous.filter((item) => item !== rowIndex) : [...previous, rowIndex],
                                );
                              }}
                              className="absolute left-0 inline-flex h-6 w-6 items-center justify-center rounded-md border-2 text-[10px] font-bold hover:opacity-90"
                              style={{
                                top: `${top + ((gridMetrics?.cellHeight ?? 132) / 2) - 12}px`,
                                borderColor: selected ? "#b91c1c" : deletable ? "#ef4444" : "#94a3b8",
                                backgroundColor: selected ? "#fecaca" : deletable ? "#fee2e2" : "#e2e8f0",
                                color: deletable ? "#b91c1c" : "#475569",
                              }}
                              title={deletable ? "Select row to delete" : "Only trailing empty rows can be deleted"}
                            >
                              <X className="h-3.5 w-3.5" />
                            </button>
                          );
                        })}
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
                  className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-border bg-white text-foreground transition-colors hover:bg-secondary/80"
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
                  className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-border bg-white text-foreground transition-colors hover:bg-secondary/80"
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
        <div className="fixed inset-0 z-[82] flex items-center justify-center bg-slate-900/30 px-4">
          <Card className="w-full max-w-lg border-border bg-white">
            <CardContent className="space-y-3 p-4">
              <p className="text-sm font-semibold text-slate-900">
                There are unsaved changes in "{activeLayout?.name ?? "layout"}". Would you like to save and proceed,
                lose changes, or cancel
                {pendingCreateLayout ? " before creating a new layout?" : "?"}
              </p>
              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={cancelLayoutSwitchDialog}
                  className="rounded-md border border-border bg-white px-3 py-2 text-xs font-semibold text-foreground transition-colors hover:bg-secondary/80"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={confirmLayoutSwitchLose}
                  className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-900 transition-colors hover:bg-amber-100"
                >
                  Lose Changes
                </button>
                <button
                  type="button"
                  onClick={confirmLayoutSwitchSave}
                  className="rounded-md border border-border bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground transition-colors hover:opacity-90"
                >
                  Save and Proceed
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : null}
      {isEditing && isExitEditDialogOpen ? (
        <div className="fixed inset-0 z-[83] flex items-center justify-center bg-slate-900/30 px-4">
          <Card className="w-full max-w-lg border-border bg-white">
            <CardContent className="space-y-3 p-4">
              <p className="text-sm font-semibold text-slate-900">
                You have unsaved changes. Save and Exit, Discard Changes, or Cancel?
              </p>
              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={cancelExitEditDialog}
                  className="rounded-md border border-border bg-white px-3 py-2 text-xs font-semibold text-foreground transition-colors hover:bg-secondary/80"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={confirmExitEditDiscard}
                  className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-900 transition-colors hover:bg-amber-100"
                >
                  Discard Changes
                </button>
                <button
                  type="button"
                  onClick={confirmExitEditSave}
                  className="rounded-md border border-blue-600 bg-blue-600 px-3 py-2 text-xs font-semibold text-white transition-colors hover:bg-blue-700"
                >
                  Save and Exit
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : null}
      {isSetActiveDialogOpen ? (
        <div className="fixed inset-0 z-[84] flex items-center justify-center bg-slate-900/30 px-4">
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

function getTrailingEmptyRows(tiles: DashboardTile[], columns: number, totalRows: number, minRows: number) {
  const rows: number[] = [];
  for (let row = totalRows - 1; row >= minRows; row -= 1) {
    const occupied = tiles.some((tile) => {
      const pos = getGridPosition(tile.slot, columns);
      return pos.row <= row && pos.row + tile.rowSpan - 1 >= row;
    });
    if (occupied) break;
    rows.push(row);
  }
  return rows;
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



