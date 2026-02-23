import { useCallback, useEffect, useRef, useState } from "react";
import {
  Eye,
  MoreHorizontal,
  Monitor,
  MoveDiagonal2,
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
};

type ViewportLayouts = Record<EditViewport, ViewportLayout>;
type HolderTile = {
  id: number;
  colSpan: number;
  rowSpan: number;
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
const VIEWPORT_COLUMNS: Record<EditViewport, number> = {
  mobile: 2,
  tablet: 4,
  desktop: 5,
};
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
  const gridRef = useRef<HTMLDivElement | null>(null);
  const overlayRef = useRef<HTMLDivElement | null>(null);
  const holderDropRef = useRef<HTMLDivElement | null>(null);
  const tileRefs = useRef<Record<number, HTMLDivElement | null>>({});

  const columns = gridMetrics?.columns ?? DESKTOP_COLUMNS;
  const displayViewport: EditViewport = columns <= 2 ? "mobile" : columns === 4 ? "tablet" : "desktop";
  const activeViewport: EditViewport = isEditing ? editingViewport : displayViewport;
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

  const saveCurrentLayout = (layoutId: string, layoutName: string, exitEdit: boolean) => {
    const now = new Date().toISOString();
    const normalizedViewportLayouts = trimAllViewportLayoutsRows(viewportLayouts);
    const snapshot: SavedLayout = {
      id: layoutId,
      name: normalizeLayoutName(layoutName),
      viewportLayouts: normalizedViewportLayouts,
      viewportHolders: normalizeViewportHolders(viewportHolders),
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
    persistLayouts(nextLayouts, layoutId);
    if (exitEdit) setIsEditing(false);
  };

  const saveAsLayout = () => {
    const raw = window.prompt("Layout name", `${sectionLabel} Layout ${savedLayouts.length + 1}`);
    const name = raw ? normalizeLayoutName(raw) : "";
    if (!name) return;
    const id = `layout_${Date.now()}`;
    saveCurrentLayout(id, name, false);
  };

  const switchLayout = (layoutId: string) => {
    const layout = savedLayouts.find((item) => item.id === layoutId);
    if (!layout) return;
    setActiveLayoutId(layoutId);
    applyLayout(layout);
    persistLayouts(savedLayouts, layoutId);
  };

  const setPrimaryLayout = (layoutId: string) => {
    const nextLayouts = savedLayouts.map((layout) => ({ ...layout, isPrimary: layout.id === layoutId }));
    setSavedLayouts(nextLayouts);
    persistLayouts(nextLayouts, activeLayoutId);
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
      setSettingsMenuOpen(false);
      setLayoutsMenuOpen(false);
      setTileMenuOpenId(null);
    };

    window.addEventListener("mousedown", onDocClick);
    return () => window.removeEventListener("mousedown", onDocClick);
  }, []);

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
    setIsOverHolderDrop(false);
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
  }, [isEditing, editingViewport]);

  const addTile = () => {
    const newTileId = nextTileId;
    setViewportLayouts((previous) => {
      const next: ViewportLayouts = {
        mobile: { ...previous.mobile, tiles: [...previous.mobile.tiles] },
        tablet: { ...previous.tablet, tiles: [...previous.tablet.tiles] },
        desktop: { ...previous.desktop, tiles: [...previous.desktop.tiles] },
      };

      (Object.keys(VIEWPORT_COLUMNS) as EditViewport[]).forEach((viewport) => {
        const viewportColumns = VIEWPORT_COLUMNS[viewport];
        let nextSlot = 0;
        while (!canPlaceTile(next[viewport].tiles, null, nextSlot, 1, 1, viewportColumns)) nextSlot += 1;
        next[viewport].tiles.push({ id: newTileId, slot: nextSlot, colSpan: 1, rowSpan: 1 });
        next[viewport].targetRows = Math.max(1, getRequiredRows(next[viewport].tiles, viewportColumns));
      });

      return next;
    });
    setNextTileId((previous) => previous + 1);
  };

  const moveTileToHolder = (tileId: number) => {
    const tile = viewportLayouts[activeViewport].tiles.find((item) => item.id === tileId);
    if (!tile) return;
    setViewportLayouts((previous) => {
      const viewportColumns = VIEWPORT_COLUMNS[activeViewport];
      const current = previous[activeViewport];
      const nextTiles = current.tiles.filter((tile) => tile.id !== tileId);
      if (nextTiles.length === current.tiles.length) return previous;
      return {
        ...previous,
        [activeViewport]: {
          ...current,
          tiles: nextTiles,
          targetRows: Math.max(1, getRequiredRows(nextTiles, viewportColumns)),
        },
      };
    });
    setViewportHolders((previous) => {
      const current = previous[activeViewport];
      if (current.some((holderTile) => holderTile.id === tileId)) return previous;
      return {
        ...previous,
        [activeViewport]: [...current, { id: tile.id, colSpan: tile.colSpan, rowSpan: tile.rowSpan }],
      };
    });
  };

  const restoreHeldTileToViewport = (tileId: number, preferredSlot: number | null) => {
    setViewportLayouts((previous) => {
      const viewportColumns = VIEWPORT_COLUMNS[activeViewport];
      const current = previous[activeViewport];
      if (current.tiles.some((tile) => tile.id === tileId)) return previous;
      let slot = preferredSlot ?? 0;
      while (!canPlaceTile(current.tiles, null, slot, 1, 1, viewportColumns)) slot += 1;
      const nextTiles = [...current.tiles, { id: tileId, slot, colSpan: 1, rowSpan: 1 }];
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
          targetRows: Math.max(1, getRequiredRows(next.mobile.tiles, VIEWPORT_COLUMNS.mobile)),
        },
        tablet: {
          ...next.tablet,
          targetRows: Math.max(1, getRequiredRows(next.tablet.tiles, VIEWPORT_COLUMNS.tablet)),
        },
        desktop: {
          ...next.desktop,
          targetRows: Math.max(1, getRequiredRows(next.desktop.tiles, VIEWPORT_COLUMNS.desktop)),
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
      const viewportColumns = VIEWPORT_COLUMNS[activeViewport];
      const currentLayout = previous[activeViewport];
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
        const sourceColumns = VIEWPORT_COLUMNS[sourceViewport];
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

        (Object.keys(VIEWPORT_COLUMNS) as EditViewport[]).forEach((viewport) => {
          const viewportColumns = VIEWPORT_COLUMNS[viewport];
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
            targetRows: Math.max(1, getRequiredRows(nextTiles, viewportColumns)),
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

  const isRowOccupied = (rowIndex: number) =>
    tiles.some((tile) => {
      const pos = getGridPosition(tile.slot, columns);
      return pos.row <= rowIndex && pos.row + tile.rowSpan - 1 >= rowIndex;
    });

  const canDeleteRow = (rowIndex: number) =>
    rowIndex === totalRows - 1
      && !isRowOccupied(rowIndex)
      && totalRows > viewportMinRows
      && computeTotalRows(Math.max(viewportMinRows, targetRows - 1)) < totalRows;
  const canAddRow = totalRows < MAX_ROWS;
  const editViewportIndex = editingViewport === "mobile" ? 0 : editingViewport === "tablet" ? 1 : 2;
  const gridColumnsClass = isEditing
    ? editingViewport === "mobile"
      ? "grid-cols-2"
      : editingViewport === "tablet"
        ? "grid-cols-4"
        : "grid-cols-5"
    : "grid-cols-2 md:grid-cols-4 xl:grid-cols-5";
  const editPreviewWidthClass =
    editingViewport === "mobile"
      ? "max-w-[420px]"
      : editingViewport === "tablet"
        ? "max-w-[900px]"
        : "max-w-[1320px]";

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
                                  <div className="absolute right-0 z-50 mt-2 min-w-[19rem] max-w-[26rem] rounded-md border border-border bg-white p-1 shadow-lg">
                                    <button
                                      type="button"
                                      onClick={() => {
                                        setPrimaryLayout(activeLayoutId);
                                        setLayoutsMenuOpen(false);
                                      }}
                                      className="w-full rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-secondary/80 hover:text-foreground"
                                    >
                                      Set Current as Primary
                                    </button>
                                    <div className="my-1 border-t border-border/80" />
                                    {savedLayouts.map((layout) => (
                                      <button
                                        key={`rail-layout-${layout.id}`}
                                        type="button"
                                        onClick={() => {
                                          switchLayout(layout.id);
                                          setLayoutsMenuOpen(false);
                                        }}
                                        className={`flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-secondary/80 hover:text-foreground ${
                                          layout.id === activeLayoutId ? "bg-secondary/50" : ""
                                        }`}
                                      >
                                        <span className="truncate pr-2" title={layout.name}>{getDisplayLayoutName(layout.name)}</span>
                                        <span className="text-[10px] text-muted-foreground">{layout.isPrimary ? "Primary" : ""}</span>
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
                                  <div className="absolute right-0 z-50 mt-2 w-40 rounded-md border border-border bg-white p-1 shadow-lg">
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
                    <div
                      ref={gridRef}
                      className={`grid ${gridColumnsClass} auto-rows-[120px] gap-3 md:auto-rows-[132px]`}
                    >
                      {Array.from({ length: totalSlots }, (_, slot) => (
                        <div
                          key={`slot-${slot}`}
                          className={
                            isEditing
                              ? `rounded-xl border border-dashed ${
                                  activeDropSlot === slot ? "border-primary/60 bg-primary/10" : "border-border/60 bg-muted/15"
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
                      ))}
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
                            className={`absolute rounded-xl border border-primary/20 bg-primary p-3 text-primary-foreground shadow-sm ${
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

                    {isEditing ? (
                      <div className="relative w-8">
                        {Array.from({ length: totalRows }, (_, rowIndex) => {
                          if (!canDeleteRow(rowIndex)) return null;
                          const top = rowIndex * ((gridMetrics?.cellHeight ?? 132) + (gridMetrics?.rowGap ?? 12));
                          return (
                            <button
                              key={`del-row-${rowIndex}`}
                              type="button"
                              onClick={() => {
                                setTargetRows((previous) => Math.max(viewportMinRows, previous - 1));
                              }}
                              className="absolute left-0 inline-flex h-6 w-6 items-center justify-center rounded-md border-2 text-[10px] font-bold hover:opacity-90"
                              style={{
                                top: `${top + ((gridMetrics?.cellHeight ?? 132) / 2) - 12}px`,
                                borderColor: "#ef4444",
                                backgroundColor: "#fee2e2",
                                color: "#b91c1c",
                              }}
                              title="Del row"
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
                <div className={`h-[74vh] w-full ${editPreviewWidthClass}`}>
                <Card className="h-full overflow-hidden border-border bg-[#f4f6fa]">
                  <CardContent className="flex h-full flex-col gap-4 overflow-hidden p-5">
                    <div className="grid items-center gap-3 md:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)]">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Layout</span>
                        <select
                          value={activeLayoutId}
                          onChange={(event) => switchLayout(event.target.value)}
                          className="min-w-[220px] rounded border border-blue-100 bg-white px-2 py-1.5 text-sm text-foreground"
                        >
                          {savedLayouts.map((layout) => (
                            <option key={`dashboard-layout-select-${layout.id}`} value={layout.id}>
                              {getDisplayLayoutName(layout.name)}{layout.isPrimary ? " (Primary)" : ""}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="justify-self-center">
                        <div className="relative grid w-[220px] grid-cols-3 rounded-lg border border-blue-100 bg-white p-1">
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
                      <div className="flex items-center justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => {
                            const layout = savedLayouts.find((item) => item.id === activeLayoutId);
                            saveCurrentLayout(activeLayoutId, layout?.name ?? defaultLayoutName, false);
                          }}
                          className="rounded border border-border bg-white px-3 py-2 text-sm font-medium transition-colors hover:bg-secondary/80"
                        >
                          Save
                        </button>
                        <button
                          type="button"
                          onClick={() => saveAsLayout()}
                          className="rounded border border-border bg-white px-3 py-2 text-sm font-medium transition-colors hover:bg-secondary/80"
                        >
                          Save As
                        </button>
                        <button
                          type="button"
                          onClick={() => setIsEditing(false)}
                          className="rounded border border-border bg-white px-3 py-2 text-sm font-medium transition-colors hover:bg-secondary/80"
                        >
                          Done
                        </button>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">Holder</p>
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() => addTile()}
                            className="rounded border border-border bg-white px-3 py-1.5 text-xs font-medium transition-colors hover:bg-secondary/80"
                          >
                            Add Tile
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              if (!canAddRow) return;
                              setTargetRows((previous) => Math.min(MAX_ROWS, previous + 1));
                            }}
                            className={`rounded border border-border bg-white px-3 py-1.5 text-xs font-medium transition-colors ${
                              canAddRow ? "hover:bg-secondary/80" : "cursor-not-allowed opacity-55"
                            }`}
                          >
                            Add Row
                          </button>
                        </div>
                      </div>
                      <div
                        ref={holderDropRef}
                        className={`min-h-20 rounded-lg border p-2 transition-colors ${
                          isOverHolderDrop && dragSession?.source === "grid"
                            ? "border-blue-400 bg-blue-50"
                            : "border-blue-100 bg-white"
                        }`}
                      >
                        {heldTileIds.length === 0 ? (
                          <p className="text-xs text-muted-foreground">Drag tiles here to hide in this viewport.</p>
                        ) : (
                          <div className="flex flex-wrap gap-2">
                            {heldTileIds.map((holderTile) => (
                              <button
                                key={`holder-tile-${activeViewport}-${holderTile.id}`}
                                type="button"
                                onMouseDown={(event) => {
                                  if (event.button !== 0) return;
                                  event.preventDefault();
                                  const viewportColumns = VIEWPORT_COLUMNS[activeViewport];
                                  const cellWidth = gridMetrics?.cellWidth ?? 120;
                                  const cellHeight = gridMetrics?.cellHeight ?? 132;
                                  const colGap = gridMetrics?.colGap ?? 12;
                                  const rowGap = gridMetrics?.rowGap ?? 12;
                                  const ghostColSpan = clamp(holderTile.colSpan, 1, viewportColumns);
                                  const ghostRowSpan = clamp(holderTile.rowSpan, 1, MAX_ROW_SPAN);
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
                                className="inline-flex items-center rounded-md border border-blue-100 bg-[#f4f6fa] px-2 py-1 text-xs font-medium text-slate-700 transition-colors hover:bg-blue-50"
                              >
                                Tile {holderTile.id}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="min-h-0 flex-1 overflow-auto pr-1">
                      <div className="flex items-start gap-2 p-2">
                      <div className="relative flex-1 overflow-visible">
                        <div
                          ref={gridRef}
                          className={`grid ${gridColumnsClass} auto-rows-[120px] gap-3 md:auto-rows-[132px]`}
                        >
                          {Array.from({ length: totalSlots }, (_, slot) => (
                            <div
                              key={`edit-slot-${slot}`}
                              className={
                                isEditing
                                  ? `rounded-xl border border-dashed ${
                                      activeDropSlot === slot ? "border-primary/60 bg-primary/10" : "border-border/60 bg-muted/15"
                                    }`
                                  : "pointer-events-none rounded-xl border border-transparent bg-transparent"
                              }
                            >
                              <div className="flex h-full items-center justify-center rounded-lg text-xs text-muted-foreground">
                                {occupiedSlots.has(slot) ? "" : "Drop tile here"}
                              </div>
                            </div>
                          ))}
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
                                className={`absolute rounded-xl border border-primary/20 bg-primary p-3 text-primary-foreground shadow-sm ${
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
                                    <div className="absolute left-1/2 top-7 z-40 w-28 -translate-x-1/2 rounded-md border border-border bg-white p-1 shadow-lg">
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
                          if (!canDeleteRow(rowIndex)) return null;
                          const top = rowIndex * ((gridMetrics?.cellHeight ?? 132) + (gridMetrics?.rowGap ?? 12));
                          return (
                            <button
                              key={`edit-del-row-${rowIndex}`}
                              type="button"
                              onClick={() => {
                                setTargetRows((previous) => Math.max(viewportMinRows, previous - 1));
                              }}
                              className="absolute left-0 inline-flex h-6 w-6 items-center justify-center rounded-md border-2 text-[10px] font-bold hover:opacity-90"
                              style={{
                                top: `${top + ((gridMetrics?.cellHeight ?? 132) / 2) - 12}px`,
                                borderColor: "#ef4444",
                                backgroundColor: "#fee2e2",
                                color: "#b91c1c",
                              }}
                              title="Del row"
                            >
                              <X className="h-3.5 w-3.5" />
                            </button>
                          );
                        })}
                      </div>
                      </div>
                    </div>
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
    </main>
  );
}

function createDefaultViewportLayouts(): ViewportLayouts {
  return {
    mobile: { tiles: DEFAULT_TILES.map((tile) => ({ ...tile })), targetRows: VIEWPORT_BASE_ROWS.mobile },
    tablet: { tiles: DEFAULT_TILES.map((tile) => ({ ...tile })), targetRows: VIEWPORT_BASE_ROWS.tablet },
    desktop: { tiles: DEFAULT_TILES.map((tile) => ({ ...tile })), targetRows: VIEWPORT_BASE_ROWS.desktop },
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
        return { id: item, colSpan: 1, rowSpan: 1 };
      }
      return {
        id: item.id,
        colSpan: clamp(item.colSpan ?? 1, 1, VIEWPORT_COLUMNS.desktop),
        rowSpan: clamp(item.rowSpan ?? 1, 1, MAX_ROW_SPAN),
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
  const desktopNormalized = normalizeViewportLayoutForColumns(
    { tiles: tiles.map((tile) => ({ ...tile })), targetRows },
    VIEWPORT_COLUMNS.desktop,
    VIEWPORT_COLUMNS.desktop,
  );
  const desktopTiles = desktopNormalized.tiles;
  return normalizeAllViewportLayouts({
    desktop: desktopNormalized,
    tablet: {
      tiles: fitTilesToColumns(desktopTiles, VIEWPORT_COLUMNS.desktop, VIEWPORT_COLUMNS.tablet),
      targetRows: targetRows,
    },
    mobile: {
      tiles: fitTilesToColumns(desktopTiles, VIEWPORT_COLUMNS.desktop, VIEWPORT_COLUMNS.mobile),
      targetRows: targetRows,
    },
  });
}

function normalizeAllViewportLayouts(layouts: Partial<ViewportLayouts>): ViewportLayouts {
  const desktopSource = layouts.desktop ?? createDefaultViewportLayouts().desktop;
  const desktopNormalized = normalizeViewportLayoutForColumns(
    desktopSource,
    VIEWPORT_COLUMNS.desktop,
    VIEWPORT_COLUMNS.desktop,
  );

  const tabletSource = layouts.tablet ?? {
    tiles: fitTilesToColumns(desktopNormalized.tiles, VIEWPORT_COLUMNS.desktop, VIEWPORT_COLUMNS.tablet),
    targetRows: desktopNormalized.targetRows,
  };
  const tabletNormalized = normalizeViewportLayoutForColumns(
    tabletSource,
    VIEWPORT_COLUMNS.tablet,
    VIEWPORT_COLUMNS.tablet,
  );

  const mobileSource = layouts.mobile ?? {
    tiles: fitTilesToColumns(desktopNormalized.tiles, VIEWPORT_COLUMNS.desktop, VIEWPORT_COLUMNS.mobile),
    targetRows: desktopNormalized.targetRows,
  };
  const mobileNormalized = normalizeViewportLayoutForColumns(
    mobileSource,
    VIEWPORT_COLUMNS.mobile,
    VIEWPORT_COLUMNS.mobile,
  );

  return {
    desktop: desktopNormalized,
    tablet: tabletNormalized,
    mobile: mobileNormalized,
  };
}

function normalizeViewportLayoutForColumns(layout: ViewportLayout, sourceColumns: number, targetColumns: number): ViewportLayout {
  const fittedTiles = fitTilesToColumns(layout.tiles, sourceColumns, targetColumns);
  const normalizedTiles = fittedTiles.map((tile) => ({ ...tile }));
  const minRowsForColumns =
    targetColumns === VIEWPORT_COLUMNS.desktop
      ? VIEWPORT_BASE_ROWS.desktop
      : targetColumns === VIEWPORT_COLUMNS.tablet
        ? VIEWPORT_BASE_ROWS.tablet
        : VIEWPORT_BASE_ROWS.mobile;
  const trimmedTargetRows = Math.max(minRowsForColumns, getRequiredRows(normalizedTiles, targetColumns), layout.targetRows);
  return {
    tiles: normalizedTiles,
    targetRows: trimmedTargetRows,
  };
}

function trimAllViewportLayoutsRows(layouts: ViewportLayouts): ViewportLayouts {
  return {
    mobile: trimViewportLayoutRows(layouts.mobile, VIEWPORT_COLUMNS.mobile, VIEWPORT_BASE_ROWS.mobile),
    tablet: trimViewportLayoutRows(layouts.tablet, VIEWPORT_COLUMNS.tablet, VIEWPORT_BASE_ROWS.tablet),
    desktop: trimViewportLayoutRows(layouts.desktop, VIEWPORT_COLUMNS.desktop, VIEWPORT_BASE_ROWS.desktop),
  };
}

function trimViewportLayoutRows(layout: ViewportLayout, columns: number, minRows: number): ViewportLayout {
  if (layout.tiles.length === 0) {
    return { tiles: [], targetRows: minRows };
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


