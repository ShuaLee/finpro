import { type ComponentType, useEffect, useRef, useState } from "react";
import {
  Bell,
  Building2,
  ChevronDown,
  Landmark,
  Menu,
  MoveDiagonal2,
  Search,
  Wallet,
  X,
} from "lucide-react";

import { Badge } from "../components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader } from "../components/ui/card";
import { useAuth } from "../context/AuthContext";

type AccountGroup = {
  title: string;
  icon: ComponentType<{ className?: string }>;
  items: string[];
};

type DashboardTile = {
  id: number;
  slot: number;
  colSpan: number;
  rowSpan: number;
};

type ResizeSession = {
  tileId: number;
  startX: number;
  startY: number;
  startColSpan: number;
  startRowSpan: number;
  startWidth: number;
  startHeight: number;
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

const accountGroups: AccountGroup[] = [
  {
    title: "Brokerage Accounts",
    icon: Building2,
    items: ["Personal Investing", "TFSA", "RRSP"],
  },
  {
    title: "Crypto Wallets",
    icon: Wallet,
    items: ["Ledger Nano", "Coinbase Wallet", "MetaMask"],
  },
  {
    title: "Cash and Banks",
    icon: Landmark,
    items: ["Main Checking", "High-Interest Savings"],
  },
];

export function AppHomePage() {
  const { user } = useAuth();
  const [expandedGroup, setExpandedGroup] = useState<string>(accountGroups[0].title);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [tiles, setTiles] = useState<DashboardTile[]>([{ id: 1, slot: 0, colSpan: 1, rowSpan: 1 }]);
  const [nextTileId, setNextTileId] = useState(2);
  const [targetRows, setTargetRows] = useState(BASE_DASHBOARD_ROWS);
  const [activeDropSlot, setActiveDropSlot] = useState<number | null>(null);
  const [draggingTileId, setDraggingTileId] = useState<number | null>(null);
  const [gridMetrics, setGridMetrics] = useState<GridMetrics | null>(null);
  const [resizeSession, setResizeSession] = useState<ResizeSession | null>(null);
  const [resizePreview, setResizePreview] = useState<{ tileId: number; colSpan: number; rowSpan: number } | null>(null);
  const [resizeVisual, setResizeVisual] = useState<{ tileId: number; width: number; height: number } | null>(null);
  const [dragSession, setDragSession] = useState<DragSession | null>(null);
  const [dragPreview, setDragPreview] = useState<{ tileId: number; left: number; top: number } | null>(null);
  const gridRef = useRef<HTMLDivElement | null>(null);
  const overlayRef = useRef<HTMLDivElement | null>(null);
  const tileRefs = useRef<Record<number, HTMLDivElement | null>>({});

  const columns = gridMetrics?.columns ?? DESKTOP_COLUMNS;

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

      const tilePos = getGridPosition(tile.slot, columns);
      const maxColSpan = columns - tilePos.col;
      const dx = event.clientX - resizeSession.startX;
      const dy = event.clientY - resizeSession.startY;

      const colFloat = resizeSession.startColSpan + dx / Math.max(1, gridMetrics.cellWidth + gridMetrics.colGap);
      const rowFloat = resizeSession.startRowSpan + dy / Math.max(1, gridMetrics.cellHeight + gridMetrics.rowGap);
      const nextColSpan = clamp(Math.floor(colFloat + 0.5), 1, maxColSpan);
      const nextRowSpan = clamp(Math.floor(rowFloat + 0.5), 1, MAX_ROW_SPAN);
      setResizePreview({ tileId: tile.id, colSpan: nextColSpan, rowSpan: nextRowSpan });
      setResizeVisual({
        tileId: tile.id,
        width: Math.max(72, resizeSession.startWidth + dx),
        height: Math.max(72, resizeSession.startHeight + dy),
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
          tile.slot,
          resizePreview.colSpan,
          resizePreview.rowSpan,
          columns,
        );
        if (!valid) return previous;

        return previous.map((item) =>
          item.id === tile.id ? { ...item, colSpan: resizePreview.colSpan, rowSpan: resizePreview.rowSpan } : item,
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
  const totalRows = Math.max(1, targetRows, maxUsedRow);
  const totalSlots = totalRows * columns;
  const occupiedSlots = getOccupiedSlots(
    tiles.map((tile) => {
      const preview = resizePreview?.tileId === tile.id ? resizePreview : null;
      return preview ? { ...tile, colSpan: preview.colSpan, rowSpan: preview.rowSpan } : tile;
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

  return (
    <main className="w-full pb-10 pt-4">
      <div className="mx-auto w-full max-w-[1680px] px-4 sm:px-6 lg:px-8">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-4 md:hidden">
          <div>
            <p className="text-sm text-muted-foreground">Welcome back</p>
            <h1 className="font-display text-3xl font-bold tracking-tight">Portfolio Dashboard</h1>
            <p className="text-sm text-muted-foreground">Signed in as {user?.email}</p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="inline-flex rounded-lg border border-border bg-white p-2 shadow-sm md:hidden"
            >
              <Menu className="h-5 w-5" />
            </button>
            <button type="button" className="inline-flex rounded-lg border border-border bg-white p-2 text-muted-foreground">
              <Search className="h-4 w-4" />
            </button>
            <button type="button" className="inline-flex rounded-lg border border-border bg-white p-2 text-muted-foreground">
              <Bell className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="grid items-start gap-6 md:grid-cols-[280px_minmax(0,1fr)] lg:grid-cols-[300px_minmax(0,1fr)]">
          <aside className="hidden md:block">
            <SidebarPanel accountGroups={accountGroups} expandedGroup={expandedGroup} setExpandedGroup={setExpandedGroup} />
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
                <SidebarPanel accountGroups={accountGroups} expandedGroup={expandedGroup} setExpandedGroup={setExpandedGroup} />
              </div>
            </div>
          ) : null}

          <section className="space-y-4">
            <div className="mb-1 hidden items-center justify-between gap-4 md:flex">
              <div>
                <p className="text-sm text-muted-foreground">Welcome back</p>
                <h1 className="font-display text-3xl font-bold tracking-tight">Portfolio Dashboard</h1>
                <p className="text-sm text-muted-foreground">Signed in as {user?.email}</p>
              </div>
              <div className="flex items-center gap-2">
                <button type="button" className="inline-flex rounded-lg border border-border bg-white p-2 text-muted-foreground">
                  <Search className="h-4 w-4" />
                </button>
                <button type="button" className="inline-flex rounded-lg border border-border bg-white p-2 text-muted-foreground">
                  <Bell className="h-4 w-4" />
                </button>
              </div>
            </div>

            <Card className="bg-white/95">
              <CardContent className="min-h-[74vh] space-y-4 p-6">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm text-muted-foreground">
                    Drag tiles to move. Resize only affects the selected tile and snaps on release.
                  </p>
                  <button
                    type="button"
                    onClick={addTile}
                    className="inline-flex items-center rounded-lg bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground transition hover:opacity-90"
                  >
                    Add Tile
                  </button>
                </div>

                <div className="flex items-start gap-2">
                  <div className="relative flex-1">
                    <div
                      ref={gridRef}
                      className="grid grid-cols-2 auto-rows-[120px] gap-3 md:grid-cols-4 md:auto-rows-[132px]"
                    >
                      {Array.from({ length: totalSlots }, (_, slot) => (
                        <div
                          key={`slot-${slot}`}
                          className={`rounded-xl border border-dashed ${
                            activeDropSlot === slot ? "border-primary/60 bg-primary/10" : "border-border/60 bg-muted/15"
                          }`}
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
                        const liveColSpan = resizeSnapPreview ? resizeSnapPreview.colSpan : tile.colSpan;
                        const liveRowSpan = resizeSnapPreview ? resizeSnapPreview.rowSpan : tile.rowSpan;
                        const pos = getGridPosition(tile.slot, columns);
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
                              left: `${dragMovePreview ? dragMovePreview.left : left}px`,
                              top: `${dragMovePreview ? dragMovePreview.top : top}px`,
                              width: `${resizeLivePreview ? resizeLivePreview.width : snappedWidth}px`,
                              height: `${resizeLivePreview ? resizeLivePreview.height : snappedHeight}px`,
                            }}
                            className={`absolute cursor-grab rounded-xl border border-primary/20 bg-primary p-3 text-primary-foreground shadow-sm active:cursor-grabbing ${
                              draggingTileId === tile.id ? "z-40 opacity-100" : "z-10"
                            }`}
                          >
                            <div className="flex h-full flex-col justify-between">
                              <div className="text-xs font-medium uppercase tracking-wide opacity-80">Tile {tile.id}</div>
                              <div className="text-[11px] opacity-85">
                                {liveColSpan}x{liveRowSpan} tile
                              </div>
                            </div>
                            <button
                              type="button"
                              onMouseDown={(event) => {
                                event.preventDefault();
                                event.stopPropagation();
                                setResizeSession({
                                  tileId: tile.id,
                                  startX: event.clientX,
                                  startY: event.clientY,
                                  startColSpan: tile.colSpan,
                                  startRowSpan: tile.rowSpan,
                                  startWidth:
                                    tile.colSpan * (gridMetrics?.cellWidth ?? 0) + (tile.colSpan - 1) * (gridMetrics?.colGap ?? 0),
                                  startHeight:
                                    tile.rowSpan * (gridMetrics?.cellHeight ?? 0) + (tile.rowSpan - 1) * (gridMetrics?.rowGap ?? 0),
                                });
                                setResizePreview({
                                  tileId: tile.id,
                                  colSpan: tile.colSpan,
                                  rowSpan: tile.rowSpan,
                                });
                              }}
                              style={{ right: "-8px", bottom: "-8px" }}
                              className="absolute z-20 inline-flex h-8 w-8 cursor-se-resize items-center justify-center rounded-md border-2 border-slate-300 bg-white text-slate-700 shadow-md"
                              aria-label={`Resize tile ${tile.id}`}
                              title="Click and hold to resize"
                            >
                              <MoveDiagonal2 className="pointer-events-none h-4 w-4" />
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  </div>

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
                    onClick={() => setTargetRows((previous) => previous + 1)}
                    className="inline-flex items-center rounded-md border px-3 py-1.5 text-xs font-semibold hover:opacity-90"
                    style={{
                      backgroundColor: "rgba(22,163,74,0.14)",
                      borderColor: "rgba(21,128,61,0.35)",
                      color: "#166534",
                    }}
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
  accountGroups,
  expandedGroup,
  setExpandedGroup,
}: {
  accountGroups: AccountGroup[];
  expandedGroup: string;
  setExpandedGroup: (value: string) => void;
}) {
  return (
    <Card className="bg-white/95">
      <CardHeader className="space-y-3">
        <Badge className="w-fit">Accounts</Badge>
        <CardDescription>Quick access to grouped accounts</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {accountGroups.map((group) => {
          const isExpanded = expandedGroup === group.title;
          const Icon = group.icon;

          return (
            <div key={group.title} className="rounded-lg border border-border bg-secondary/35">
              <button
                type="button"
                onClick={() => setExpandedGroup(isExpanded ? "" : group.title)}
                className="inline-flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-sm font-semibold"
              >
                <span className="inline-flex items-center gap-2">
                  <Icon className="h-4 w-4 text-primary" />
                  {group.title}
                </span>
                <ChevronDown className={`h-4 w-4 transition ${isExpanded ? "rotate-180" : ""}`} />
              </button>
              {isExpanded ? (
                <ul className="space-y-1 border-t border-border px-3 py-2 text-sm text-muted-foreground">
                  {group.items.map((item) => (
                    <li key={item} className="rounded px-2 py-1 hover:bg-secondary/70">
                      {item}
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
