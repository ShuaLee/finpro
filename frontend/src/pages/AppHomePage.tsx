import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BriefcaseBusiness,
  Building2,
  ChevronDown,
  Coins,
  Eye,
  House,
  Menu,
  MoveDiagonal2,
  Settings,
  Trash2,
  X,
} from "lucide-react";

import { type SidebarAccount, getAccountsSidebar } from "../api/accounts";
import { Badge } from "../components/ui/badge";
import { Card, CardContent, CardHeader } from "../components/ui/card";
import { useAuth } from "../context/AuthContext";

type DashboardTile = {
  id: number;
  slot: number;
  colSpan: number;
  rowSpan: number;
};

type SavedLayout = {
  id: string;
  name: string;
  tiles: DashboardTile[];
  targetRows: number;
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
  tileId: number;
  startX: number;
  startY: number;
  startLeft: number;
  startTop: number;
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

const DESKTOP_COLUMNS = 4;
const BASE_DASHBOARD_ROWS = 4;
const MAX_ROW_SPAN = 8;
const MAX_ROWS = 20;
const MAX_LAYOUT_NAME_LENGTH = 30;
const DEFAULT_LAYOUT_ID = "default";
const DEFAULT_TILES: DashboardTile[] = [{ id: 1, slot: 0, colSpan: 1, rowSpan: 1 }];

const normalizeLayoutName = (name: string) => name.trim().slice(0, MAX_LAYOUT_NAME_LENGTH);
const getDisplayLayoutName = (name: string) =>
  name.length > MAX_LAYOUT_NAME_LENGTH ? `${name.slice(0, MAX_LAYOUT_NAME_LENGTH)}...` : name;

export function AppHomePage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [customSidebarCategories] = useState<Array<{ key: string; label: string }>>([
    { key: "private-equity", label: "Private Equity" },
  ]);
  const [activeSidebarCategory, setActiveSidebarCategory] = useState("portfolio");
  const [isBrokerageExpanded, setIsBrokerageExpanded] = useState(true);
  const [brokerageAccounts, setBrokerageAccounts] = useState<SidebarAccount[]>([]);
  const [accountsLoading, setAccountsLoading] = useState(false);
  const [accountsError, setAccountsError] = useState<string | null>(null);
  const [selectedView, setSelectedView] = useState<"brokerage-summary" | "account">("brokerage-summary");
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [settingsMenuOpen, setSettingsMenuOpen] = useState(false);
  const [layoutsMenuOpen, setLayoutsMenuOpen] = useState(false);
  const [tiles, setTiles] = useState<DashboardTile[]>(DEFAULT_TILES);
  const [nextTileId, setNextTileId] = useState(2);
  const [targetRows, setTargetRows] = useState(BASE_DASHBOARD_ROWS);
  const [savedLayouts, setSavedLayouts] = useState<SavedLayout[]>([]);
  const [activeLayoutId, setActiveLayoutId] = useState(DEFAULT_LAYOUT_ID);
  const [activeDropSlot, setActiveDropSlot] = useState<number | null>(null);
  const [draggingTileId, setDraggingTileId] = useState<number | null>(null);
  const [gridMetrics, setGridMetrics] = useState<GridMetrics | null>(null);
  const [resizeSession, setResizeSession] = useState<ResizeSession | null>(null);
  const [resizePreview, setResizePreview] = useState<{ tileId: number; slot: number; colSpan: number; rowSpan: number } | null>(null);
  const [resizeVisual, setResizeVisual] = useState<{ tileId: number; left: number; top: number; width: number; height: number } | null>(
    null,
  );
  const [dragSession, setDragSession] = useState<DragSession | null>(null);
  const [dragPreview, setDragPreview] = useState<{ tileId: number; left: number; top: number } | null>(null);
  const gridRef = useRef<HTMLDivElement | null>(null);
  const overlayRef = useRef<HTMLDivElement | null>(null);
  const tileRefs = useRef<Record<number, HTMLDivElement | null>>({});

  const columns = gridMetrics?.columns ?? DESKTOP_COLUMNS;
  const sectionLabel = (() => {
    if (activeSidebarCategory === "brokerage") return "Brokerage";
    if (activeSidebarCategory === "crypto") return "Crypto";
    if (activeSidebarCategory === "real-estate") return "Real Estate";
    if (activeSidebarCategory === "portfolio") return "Portfolio";
    return customSidebarCategories.find((category) => category.key === activeSidebarCategory)?.label ?? "Custom";
  })();
  const defaultLayoutName = `${sectionLabel} Default Layout`;
  const dashboardScope = (() => {
    if (activeSidebarCategory === "brokerage") {
      if (selectedView === "account" && selectedAccountId) return `brokerage-account-${selectedAccountId}`;
      return "brokerage-summary";
    }
    return activeSidebarCategory;
  })();
  const storageKey = `finpro.dashboard.layouts.${(user?.email ?? "anonymous").toLowerCase()}.${dashboardScope}`;

  const normalizePrimary = (layouts: SavedLayout[]) => {
    if (layouts.length === 0) return layouts;
    const primaryCount = layouts.filter((layout) => layout.isPrimary).length;
    if (primaryCount === 1) return layouts;
    return layouts.map((layout, index) => ({ ...layout, isPrimary: index === 0 }));
  };

  const applyLayout = (layout: SavedLayout) => {
    setTiles(layout.tiles);
    setTargetRows(layout.targetRows);
    const maxId = layout.tiles.reduce((max, tile) => Math.max(max, tile.id), 0);
    setNextTileId(maxId + 1);
  };

  const persistLayouts = (layouts: SavedLayout[], activeId: string) => {
    const normalized = normalizePrimary(layouts);
    localStorage.setItem(storageKey, JSON.stringify({ activeLayoutId: activeId, layouts: normalized }));
  };

  const saveCurrentLayout = (layoutId: string, layoutName: string, exitEdit: boolean) => {
    const now = new Date().toISOString();
    const minUsedRow = tiles.length > 0
      ? Math.min(...tiles.map((tile) => getGridPosition(tile.slot, columns).row))
      : 0;
    const normalizedTiles = minUsedRow > 0
      ? tiles.map((tile) => {
          const pos = getGridPosition(tile.slot, columns);
          const normalizedRow = pos.row - minUsedRow;
          return { ...tile, slot: normalizedRow * columns + pos.col };
        })
      : tiles.map((tile) => ({ ...tile }));
    const trimmedTargetRows = Math.max(1, getRequiredRows(normalizedTiles, columns));
    const snapshot: SavedLayout = {
      id: layoutId,
      name: normalizeLayoutName(layoutName),
      tiles: normalizedTiles,
      targetRows: trimmedTargetRows,
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
    setTiles(normalizedTiles);
    setTargetRows(trimmedTargetRows);
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
    setAccountsLoading(true);
    setAccountsError(null);
    try {
      const groups = await getAccountsSidebar();
      const brokerageGroup = groups.find((group) =>
        /brokerage/i.test(group.group_label) || /brokerage/i.test(group.group_key)
      );
      const accounts = brokerageGroup ? brokerageGroup.accounts : [];
      setBrokerageAccounts(accounts);
      if (accounts.length === 0) {
        setSelectedView("brokerage-summary");
        setSelectedAccountId(null);
      }
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Unable to load brokerage accounts.";
      setAccountsError(message);
      setBrokerageAccounts([]);
      setSelectedView("brokerage-summary");
      setSelectedAccountId(null);
    } finally {
      setAccountsLoading(false);
    }
  }, []);

  const deleteLayout = (layoutId: string) => {
    if (savedLayouts.length <= 1) return;

    const deletingLayout = savedLayouts.find((layout) => layout.id === layoutId);
    let remaining = savedLayouts.filter((layout) => layout.id !== layoutId);
    if (remaining.length === 0) return;

    if (deletingLayout?.isPrimary || !remaining.some((layout) => layout.isPrimary)) {
      const nextPrimaryId = remaining[0].id;
      remaining = remaining.map((layout) => ({ ...layout, isPrimary: layout.id === nextPrimaryId }));
    }

    const nextActiveId = activeLayoutId === layoutId ? remaining[0].id : activeLayoutId;
    const normalized = normalizePrimary(remaining);
    setSavedLayouts(normalized);
    setActiveLayoutId(nextActiveId);
    const nextActiveLayout = normalized.find((layout) => layout.id === nextActiveId);
    if (nextActiveLayout) applyLayout(nextActiveLayout);
    persistLayouts(normalized, nextActiveId);
  };

  useEffect(() => {
    const onDocClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement | null;
      if (!target) return;
      if (target.closest("[data-dashboard-menu]")) return;
      setSettingsMenuOpen(false);
      setLayoutsMenuOpen(false);
    };

    window.addEventListener("mousedown", onDocClick);
    return () => window.removeEventListener("mousedown", onDocClick);
  }, []);

  useEffect(() => {
    void loadBrokerageAccounts();
  }, [loadBrokerageAccounts, user?.email]);

  useEffect(() => {
    if (!selectedAccountId) return;
    if (brokerageAccounts.some((account) => account.id === selectedAccountId)) return;
    setSelectedAccountId(null);
    setSelectedView("brokerage-summary");
  }, [brokerageAccounts, selectedAccountId]);

  useEffect(() => {
    const raw = localStorage.getItem(storageKey);
    if (!raw) {
      const defaultLayout: SavedLayout = {
        id: DEFAULT_LAYOUT_ID,
        name: defaultLayoutName,
        tiles: DEFAULT_TILES,
        targetRows: BASE_DASHBOARD_ROWS,
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
      const parsed = JSON.parse(raw) as { activeLayoutId?: string; layouts?: SavedLayout[] };
      const layoutsRaw = Array.isArray(parsed.layouts) && parsed.layouts.length > 0 ? parsed.layouts : [];
      const layouts = normalizePrimary(
        layoutsRaw.map((layout) => ({
          ...layout,
          name: normalizeLayoutName(layout.name || defaultLayoutName),
          isPrimary: Boolean(layout.isPrimary),
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
        tiles: DEFAULT_TILES,
        targetRows: BASE_DASHBOARD_ROWS,
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
    window.addEventListener("resize", updateMetrics);
    return () => window.removeEventListener("resize", updateMetrics);
  }, []);

  const addTile = () => {
    let nextSlot = 0;
    while (!canPlaceTile(tiles, null, nextSlot, 1, 1, columns)) nextSlot += 1;
    setTiles((previous) => [...previous, { id: nextTileId, slot: nextSlot, colSpan: 1, rowSpan: 1 }]);
    setNextTileId((previous) => previous + 1);
  };

  const moveTileToSlot = (tileId: number, targetSlot: number) => {
    setTiles((previous) => {
      const tile = previous.find((item) => item.id === tileId);
      if (!tile) return previous;
      if (tile.slot === targetSlot) return previous;
      if (!canPlaceTile(previous, tile.id, targetSlot, tile.colSpan, tile.rowSpan, columns)) return previous;
      return previous.map((item) => (item.id === tileId ? { ...item, slot: targetSlot } : item));
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
      setTiles((previous) => {
        if (!resizePreview || resizePreview.tileId !== resizeSession.tileId) return previous;
        const tile = previous.find((item) => item.id === resizeSession.tileId);
        if (!tile) return previous;

        const valid = canPlaceTile(
          previous,
          tile.id,
          resizePreview.slot,
          resizePreview.colSpan,
          resizePreview.rowSpan,
          columns,
        );
        if (!valid) return previous;

        return previous.map((item) =>
          item.id === tile.id
            ? { ...item, slot: resizePreview.slot, colSpan: resizePreview.colSpan, rowSpan: resizePreview.rowSpan }
            : item,
        );
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
  }, [columns, gridMetrics, resizePreview, resizeSession, tiles]);

  useEffect(() => {
    if (!dragSession || !gridMetrics || !gridRef.current) return;

    const onMouseMove = (event: MouseEvent) => {
      const dx = event.clientX - dragSession.startX;
      const dy = event.clientY - dragSession.startY;
      const left = dragSession.startLeft + dx;
      const top = dragSession.startTop + dy;
      setDragPreview({ tileId: dragSession.tileId, left, top });

      const slot = getSlotFromPoint(event.clientX, event.clientY, gridRef.current!, gridMetrics, columns);

      setActiveDropSlot(slot);
    };

    const onMouseUp = (event: MouseEvent) => {
      const slot = getSlotFromPoint(event.clientX, event.clientY, gridRef.current!, gridMetrics, columns);
      if (slot !== null) {
        const tile = tiles.find((item) => item.id === dragSession.tileId);
        if (tile) {
          const alignedSlot = getAlignedTopLeftSlot(slot, dragSession.anchorCol, dragSession.anchorRow, tile, columns);
          moveTileToSlot(dragSession.tileId, alignedSlot);
        }
      }
      setDraggingTileId(null);
      setActiveDropSlot(null);
      setDragSession(null);
      setDragPreview(null);
    };

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, [columns, dragSession, gridMetrics]);

  const maxUsedRow =
    tiles.length > 0
      ? Math.max(...tiles.map((tile) => getGridPosition(tile.slot, columns).row + tile.rowSpan))
      : 0;
  const totalRows = Math.min(MAX_ROWS, Math.max(1, targetRows, maxUsedRow));
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
    rowIndex === totalRows - 1 && !isRowOccupied(rowIndex) && totalRows > 1;
  const canAddRow = totalRows < MAX_ROWS;

  return (
    <main className="w-full pb-10 pt-4">
      <div className="mx-auto w-full max-w-[1680px] px-4 sm:px-6 lg:px-8">
        <div className="mb-4 flex flex-wrap items-end justify-between gap-4 md:hidden">
          <div>
            <p className="text-sm text-muted-foreground">Welcome back</p>
            <h1 className="font-display text-3xl font-bold tracking-tight">Portfolio Dashboard</h1>
          </div>

          <div className="mt-3 flex items-center gap-2">
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="inline-flex rounded-lg border border-border bg-white p-2.5 shadow-sm md:hidden"
            >
              <Menu className="h-6 w-6" />
            </button>
            <div className="relative" data-dashboard-menu>
              <button
                type="button"
                onClick={() => {
                  setLayoutsMenuOpen((previous) => !previous);
                  setSettingsMenuOpen(false);
                }}
                className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-border bg-white text-muted-foreground transition-colors hover:bg-secondary/70 hover:text-foreground"
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
                      key={`mobile-layout-${layout.id}`}
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
                className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-border bg-white text-muted-foreground transition-colors hover:bg-secondary/70 hover:text-foreground"
              >
                <Settings className="h-5 w-5" />
              </button>
              {settingsMenuOpen ? (
                <div className="absolute right-0 z-50 mt-2 w-40 rounded-md border border-border bg-white p-1 shadow-lg">
                  {!isEditing ? (
                    <>
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
                    </>
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

        <div className="grid items-stretch gap-6 md:grid-cols-[280px_minmax(0,1fr)] lg:grid-cols-[300px_minmax(0,1fr)]">
          <aside className="hidden md:block md:self-stretch">
            <SidebarPanel
              customSidebarCategories={customSidebarCategories}
              activeSidebarCategory={activeSidebarCategory}
              setActiveSidebarCategory={setActiveSidebarCategory}
              isBrokerageExpanded={isBrokerageExpanded}
              setIsBrokerageExpanded={setIsBrokerageExpanded}
              brokerageAccounts={brokerageAccounts}
              selectedView={selectedView}
              selectedAccountId={selectedAccountId}
              accountsLoading={accountsLoading}
              accountsError={accountsError}
              onSelectSummary={() => {
                setSelectedView("brokerage-summary");
                setSelectedAccountId(null);
              }}
              onSelectAccount={(accountId) => {
                setSelectedView("account");
                setSelectedAccountId(accountId);
              }}
              onAddBrokerageAccount={() => navigate("/accounts/brokerage/new")}
            />
          </aside>

          {sidebarOpen ? (
            <div className="fixed inset-0 z-50 bg-black/35 md:hidden" onClick={() => setSidebarOpen(false)}>
              <div className="h-full w-80 max-w-[85vw] bg-white p-4" onClick={(event) => event.stopPropagation()}>
                <div className="mb-3 flex justify-end">
                  <button
                    type="button"
                    onClick={() => setSidebarOpen(false)}
                    className="rounded-md border border-border p-1"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
                <SidebarPanel
                  customSidebarCategories={customSidebarCategories}
                  activeSidebarCategory={activeSidebarCategory}
                  setActiveSidebarCategory={setActiveSidebarCategory}
                  isBrokerageExpanded={isBrokerageExpanded}
                  setIsBrokerageExpanded={setIsBrokerageExpanded}
                  brokerageAccounts={brokerageAccounts}
                  selectedView={selectedView}
                  selectedAccountId={selectedAccountId}
                  accountsLoading={accountsLoading}
                  accountsError={accountsError}
                  onSelectSummary={() => {
                    setSelectedView("brokerage-summary");
                    setSelectedAccountId(null);
                    setSidebarOpen(false);
                  }}
                  onSelectAccount={(accountId) => {
                    setSelectedView("account");
                    setSelectedAccountId(accountId);
                    setSidebarOpen(false);
                  }}
                  onAddBrokerageAccount={() => {
                    setSidebarOpen(false);
                    navigate("/accounts/brokerage/new");
                  }}
                />
              </div>
            </div>
          ) : null}

          <section className="space-y-4">
            <div className="mb-1 hidden items-end justify-between gap-4 md:flex">
              <div>
                <p className="text-sm text-muted-foreground">Welcome back</p>
                <h1 className="font-display text-3xl font-bold tracking-tight">Portfolio Dashboard</h1>
              </div>
              <div className="mt-3 flex items-center gap-2">
                <div className="relative" data-dashboard-menu>
                  <button
                    type="button"
                    onClick={() => {
                      setLayoutsMenuOpen((previous) => !previous);
                      setSettingsMenuOpen(false);
                    }}
                    className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-border bg-white text-muted-foreground transition-colors hover:bg-secondary/70 hover:text-foreground"
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
                          key={`desktop-layout-${layout.id}`}
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
                    className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-border bg-white text-muted-foreground transition-colors hover:bg-secondary/70 hover:text-foreground"
                  >
                    <Settings className="h-5 w-5" />
                  </button>
                  {settingsMenuOpen ? (
                    <div className="absolute right-0 z-50 mt-2 w-40 rounded-md border border-border bg-white p-1 shadow-lg">
                      {!isEditing ? (
                        <>
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
                        </>
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

                {isEditing ? (
                  <div className="rounded-lg border border-border/80 bg-muted/20 p-3">
                    <div className="flex flex-wrap items-end gap-3">
                      <div className="min-w-[220px] flex-1">
                        <label className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                          Working Layout
                        </label>
                        <select
                          value={activeLayoutId}
                          onChange={(event) => switchLayout(event.target.value)}
                          className="w-full rounded border border-border bg-white px-2 py-2 text-sm text-foreground"
                        >
                          {savedLayouts.map((layout) => (
                            <option key={`dashboard-edit-layout-option-${layout.id}`} value={layout.id}>
                              {getDisplayLayoutName(layout.name)}{layout.isPrimary ? " (Primary)" : ""}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="flex items-center gap-2">
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
                          onClick={() => addTile()}
                          className="rounded border border-border bg-white px-3 py-2 text-sm font-medium transition-colors hover:bg-secondary/80"
                        >
                          Add Tile
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
                    <div className="mt-3 max-h-28 space-y-1 overflow-y-auto pr-1">
                      {savedLayouts.map((layout) => (
                        <div key={`dashboard-edit-layout-delete-${layout.id}`} className="flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() => switchLayout(layout.id)}
                            className={`flex-1 rounded border px-2 py-1.5 text-left text-xs transition-colors hover:bg-secondary/80 hover:text-foreground ${
                              layout.id === activeLayoutId ? "border-primary/40 bg-secondary/50" : "border-border/70 bg-white"
                            }`}
                          >
                            {getDisplayLayoutName(layout.name)}
                            {layout.isPrimary ? " (Primary)" : ""}
                          </button>
                          <button
                            type="button"
                            onClick={() => deleteLayout(layout.id)}
                            disabled={savedLayouts.length <= 1}
                            title={savedLayouts.length <= 1 ? "At least one layout is required" : "Delete layout"}
                            className="inline-flex h-8 w-8 items-center justify-center rounded border border-destructive/50 bg-white text-destructive transition-colors hover:bg-destructive/10 disabled:cursor-not-allowed disabled:opacity-40"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}
            <Card className="bg-white/95">
              <CardContent className="min-h-[74vh] space-y-4 p-6">
                {isEditing ? (
                  <p className="text-sm text-muted-foreground">
                    Drag and resize tiles. Drop zones and row controls are edit-only.
                  </p>
                ) : null}
                <div className="flex items-start gap-2">
                  <div className="relative flex-1">
                    <div
                      ref={gridRef}
                      className="grid grid-cols-2 auto-rows-[120px] gap-3 md:grid-cols-4 md:auto-rows-[132px]"
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
                        const dragMovePreview = dragPreview?.tileId === tile.id ? dragPreview : null;
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
                                tileId: tile.id,
                                startX: event.clientX,
                                startY: event.clientY,
                                startLeft: left,
                                startTop: top,
                                anchorCol,
                                anchorRow,
                              });
                              setDragPreview({ tileId: tile.id, left, top });
                            }}
                            style={{
                              left: `${dragMovePreview ? dragMovePreview.left : resizeLivePreview ? resizeLivePreview.left : left}px`,
                              top: `${dragMovePreview ? dragMovePreview.top : resizeLivePreview ? resizeLivePreview.top : top}px`,
                              width: `${resizeLivePreview ? resizeLivePreview.width : snappedWidth}px`,
                              height: `${resizeLivePreview ? resizeLivePreview.height : snappedHeight}px`,
                            }}
                            className={`absolute rounded-xl border border-primary/20 bg-primary p-3 text-primary-foreground shadow-sm ${
                              isEditing ? "cursor-grab active:cursor-grabbing" : "cursor-default"
                            } ${
                              draggingTileId === tile.id ? "z-40 opacity-100" : "z-10"
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
                          const top = rowIndex * ((gridMetrics?.cellHeight ?? 132) + (gridMetrics?.rowGap ?? 12));
                          return (
                            <button
                              key={`del-row-${rowIndex}`}
                              type="button"
                              onClick={() => {
                                if (!canDeleteRow(rowIndex)) return;
                                setTargetRows((previous) => Math.max(1, previous - 1));
                              }}
                              className={`absolute left-0 inline-flex h-6 w-6 items-center justify-center rounded-md border-2 text-[10px] font-bold ${
                                canDeleteRow(rowIndex) ? "hover:opacity-90" : "cursor-not-allowed opacity-55"
                              }`}
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
          </section>
        </div>
      </div>
    </main>
  );
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


function SidebarPanel({
  customSidebarCategories,
  activeSidebarCategory,
  setActiveSidebarCategory,
  isBrokerageExpanded,
  setIsBrokerageExpanded,
  brokerageAccounts,
  selectedView,
  selectedAccountId,
  accountsLoading,
  accountsError,
  onSelectSummary,
  onSelectAccount,
  onAddBrokerageAccount,
}: {
  customSidebarCategories: Array<{ key: string; label: string }>;
  activeSidebarCategory: string;
  setActiveSidebarCategory: (value: string) => void;
  isBrokerageExpanded: boolean;
  setIsBrokerageExpanded: (value: boolean) => void;
  brokerageAccounts: SidebarAccount[];
  selectedView: "brokerage-summary" | "account";
  selectedAccountId: number | null;
  accountsLoading: boolean;
  accountsError: string | null;
  onSelectSummary: () => void;
  onSelectAccount: (accountId: number) => void;
  onAddBrokerageAccount: () => void;
}) {
  return (
    <Card className="h-full overflow-hidden border-border/80 bg-white/95">
      <CardHeader className="space-y-4 border-b border-border/80 pb-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <Badge className="w-fit">Accounts</Badge>
            <p className="mt-2 text-xs uppercase tracking-wide text-muted-foreground">Navigation</p>
          </div>
          <div className="rounded-md border border-border/70 bg-secondary/40 px-2 py-1 text-xs text-muted-foreground">
            {brokerageAccounts.length}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 p-3">
        <button
          type="button"
          onClick={() => setActiveSidebarCategory("portfolio")}
          className={`flex w-full items-center gap-2 rounded-md border px-3 py-2 text-left text-sm font-semibold transition-colors ${
            activeSidebarCategory === "portfolio"
              ? "border-primary/30 bg-primary/10 text-foreground"
              : "border-border/70 bg-white text-foreground hover:bg-secondary/50"
          }`}
        >
          <BriefcaseBusiness className="h-4 w-4 text-primary" />
          Portfolio
        </button>

        <div className="rounded-md border border-border/70 bg-white">
          <div className="flex items-stretch">
            <button
              type="button"
              onClick={() => {
                setActiveSidebarCategory("brokerage");
                onSelectSummary();
              }}
              className={`flex min-w-0 flex-1 items-center gap-2 rounded-l-md px-3 py-2 text-left text-sm font-semibold transition-colors ${
                activeSidebarCategory === "brokerage"
                  ? "bg-primary/10 text-foreground"
                  : "text-foreground hover:bg-secondary/50"
              }`}
            >
              <Building2 className="h-4 w-4 text-primary" />
              Brokerage
            </button>
            <button
              type="button"
              onClick={() => setIsBrokerageExpanded(!isBrokerageExpanded)}
              className="inline-flex w-10 items-center justify-center rounded-r-md border-l border-border/70 text-muted-foreground transition-colors hover:bg-secondary/50 hover:text-foreground"
              aria-label={isBrokerageExpanded ? "Collapse brokerage accounts" : "Expand brokerage accounts"}
            >
              <ChevronDown className={`h-4 w-4 transition-transform ${isBrokerageExpanded ? "rotate-180" : ""}`} />
            </button>
          </div>
          {isBrokerageExpanded ? (
            <div className="space-y-2 border-t border-border/70 p-2">
              <button
                type="button"
                onClick={onAddBrokerageAccount}
                className="w-full rounded-md border border-green-700/40 bg-green-600/15 px-3 py-2 text-left text-sm font-semibold text-green-900 transition-colors hover:bg-green-600/30"
              >
                + Add New Brokerage Account
              </button>
              {accountsLoading ? (
                <p className="px-2 py-1 text-xs text-muted-foreground">Loading accounts...</p>
              ) : null}
              {accountsError ? (
                <p className="px-2 py-1 text-xs text-destructive">{accountsError}</p>
              ) : null}
              {!accountsLoading && !accountsError ? (
                <ul className="space-y-1">
                  {brokerageAccounts.map((account) => (
                    <li key={account.id}>
                      <button
                        type="button"
                        onClick={() => {
                          setActiveSidebarCategory("brokerage");
                          onSelectAccount(account.id);
                        }}
                        className={`w-full rounded-md border px-3 py-2 text-left transition-colors ${
                          selectedView === "account" && selectedAccountId === account.id
                            ? "border-primary/30 bg-primary/10 text-foreground"
                            : "border-transparent text-foreground hover:border-border/70 hover:bg-secondary/50"
                        }`}
                      >
                        <span className="block truncate text-sm font-medium">{account.name}</span>
                        <span className="mt-0.5 block text-[11px] text-muted-foreground">
                          {account.broker || "Broker"} · {account.holdings_count} holdings
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}
        </div>

        <button
          type="button"
          onClick={() => setActiveSidebarCategory("crypto")}
          className={`flex w-full items-center gap-2 rounded-md border px-3 py-2 text-left text-sm font-semibold transition-colors ${
            activeSidebarCategory === "crypto"
              ? "border-primary/30 bg-primary/10 text-foreground"
              : "border-border/70 bg-white text-foreground hover:bg-secondary/50"
          }`}
        >
          <Coins className="h-4 w-4 text-primary" />
          Crypto
        </button>

        <button
          type="button"
          onClick={() => setActiveSidebarCategory("real-estate")}
          className={`flex w-full items-center gap-2 rounded-md border px-3 py-2 text-left text-sm font-semibold transition-colors ${
            activeSidebarCategory === "real-estate"
              ? "border-primary/30 bg-primary/10 text-foreground"
              : "border-border/70 bg-white text-foreground hover:bg-secondary/50"
          }`}
        >
          <House className="h-4 w-4 text-primary" />
          Real Estate
        </button>

        {customSidebarCategories.map((category) => (
          <button
            key={category.key}
            type="button"
            onClick={() => setActiveSidebarCategory(category.key)}
            className={`flex w-full items-center gap-2 rounded-md border px-3 py-2 text-left text-sm font-semibold transition-colors ${
              activeSidebarCategory === category.key
                ? "border-primary/30 bg-primary/10 text-foreground"
                : "border-border/70 bg-white text-foreground hover:bg-secondary/50"
            }`}
          >
            <BriefcaseBusiness className="h-4 w-4 text-primary" />
            {category.label}
          </button>
        ))}
      </CardContent>
    </Card>
  );
}

