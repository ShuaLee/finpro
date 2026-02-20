import { type ComponentType, useMemo, useState } from "react";
import {
  Bell,
  Building2,
  ChevronDown,
  Landmark,
  Menu,
  Search,
  Wallet,
  X,
} from "lucide-react";

import { Badge } from "../components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { useAuth } from "../context/AuthContext";

type AccountGroup = {
  title: string;
  icon: ComponentType<{ className?: string }>;
  items: string[];
};

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

const netWorthSeries = [
  182000, 185000, 190500, 196000, 201000, 205500,
  208250, 211000, 214300, 218500, 221200, 225400,
];

export function AppHomePage() {
  const { user } = useAuth();
  const [expandedGroup, setExpandedGroup] = useState<string>(accountGroups[0].title);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("Overview");

  const graphPoints = useMemo(() => {
    const max = Math.max(...netWorthSeries);
    const min = Math.min(...netWorthSeries);
    const width = 900;
    const height = 260;

    return netWorthSeries
      .map((value, index) => {
        const x = (index / (netWorthSeries.length - 1)) * width;
        const y = height - ((value - min) / (max - min || 1)) * height;
        return `${x},${y}`;
      })
      .join(" ");
  }, []);

  return (
    <main className="mx-auto w-full max-w-7xl px-4 pb-10 pt-6 sm:px-6 lg:px-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm text-muted-foreground">Welcome back</p>
          <h1 className="font-display text-3xl font-bold tracking-tight">Portfolio Dashboard</h1>
          <p className="text-sm text-muted-foreground">Signed in as {user?.email}</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            className="inline-flex rounded-lg border border-border bg-white p-2 shadow-sm lg:hidden"
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

      <div className="grid items-start gap-6 lg:grid-cols-[280px_1fr]">
        <aside className="hidden lg:block">
          <SidebarPanel accountGroups={accountGroups} expandedGroup={expandedGroup} setExpandedGroup={setExpandedGroup} />
        </aside>

        {sidebarOpen ? (
          <div className="fixed inset-0 z-50 bg-black/35 lg:hidden" onClick={() => setSidebarOpen(false)}>
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

        <section className="space-y-6">
          <div className="flex flex-wrap items-center gap-2">
            {["Overview", "Performance", "Allocations"].map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setActiveTab(tab)}
                className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
                  activeTab === tab
                    ? "bg-primary text-primary-foreground"
                    : "bg-white text-muted-foreground hover:bg-secondary hover:text-foreground"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricTile label="Net Worth" value="$225,400" change="+4.8%" />
            <MetricTile label="Monthly Return" value="$8,720" change="+2.1%" />
            <MetricTile label="Accounts" value="8" change="+1 new" />
            <MetricTile label="Risk Level" value="Moderate" change="Stable" />
          </div>

          <Card className="bg-white/95">
            <CardHeader className="flex flex-row items-center justify-between gap-4">
              <div>
                <CardTitle className="font-display text-2xl">Net Worth Trend</CardTitle>
                <CardDescription>Last 12 months</CardDescription>
              </div>
              <Badge>$225,400</Badge>
            </CardHeader>
            <CardContent>
              <div className="overflow-hidden rounded-lg border border-border bg-[#f8f9fb] p-4">
                <svg viewBox="0 0 900 260" className="h-64 w-full">
                  <defs>
                    <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#111315" stopOpacity="0.16" />
                      <stop offset="100%" stopColor="#111315" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  {[0, 1, 2, 3, 4].map((i) => (
                    <line
                      key={`grid-${i}`}
                      x1="0"
                      y1={i * 65}
                      x2="900"
                      y2={i * 65}
                      stroke="rgba(15,23,42,0.12)"
                      strokeDasharray="4 6"
                    />
                  ))}
                  <polyline
                    fill="url(#areaFill)"
                    stroke="none"
                    points={`0,260 ${graphPoints} 900,260`}
                  />
                  <polyline
                    fill="none"
                    stroke="#111315"
                    strokeWidth="4"
                    strokeLinecap="round"
                    points={graphPoints}
                  />
                </svg>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-4 xl:grid-cols-2">
            <Card className="bg-white/95">
              <CardHeader>
                <CardTitle className="font-display text-xl">Allocation</CardTitle>
                <CardDescription>Current split by asset class</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-[180px_1fr]">
                <svg viewBox="0 0 140 140" className="mx-auto h-40 w-40 -rotate-90">
                  <circle cx="70" cy="70" r="48" fill="none" stroke="#e7e9ee" strokeWidth="22" />
                  <circle cx="70" cy="70" r="48" fill="none" stroke="#111315" strokeWidth="22" strokeDasharray="301.6" strokeDashoffset="174.9" />
                  <circle cx="70" cy="70" r="48" fill="none" stroke="#454d5b" strokeWidth="22" strokeDasharray="301.6" strokeDashoffset="224" />
                  <circle cx="70" cy="70" r="48" fill="none" stroke="#697384" strokeWidth="22" strokeDasharray="301.6" strokeDashoffset="260" />
                  <circle cx="70" cy="70" r="48" fill="none" stroke="#9aa2af" strokeWidth="22" strokeDasharray="301.6" strokeDashoffset="282" />
                </svg>
                <ul className="space-y-2 text-sm">
                  <LegendRow label="Equities" value="42%" color="bg-[#12151b]" />
                  <LegendRow label="Cash" value="25%" color="bg-[#454d5b]" />
                  <LegendRow label="Crypto" value="16%" color="bg-[#697384]" />
                  <LegendRow label="Alternatives" value="17%" color="bg-[#9aa2af]" />
                </ul>
              </CardContent>
            </Card>

            <Card className="bg-white/95">
              <CardHeader>
                <CardTitle className="font-display text-xl">Top Holdings</CardTitle>
                <CardDescription>Largest positions by current value</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <HoldingRow symbol="AAPL" name="Apple" value="$32,550" change="+1.2%" positive />
                <HoldingRow symbol="MSFT" name="Microsoft" value="$28,140" change="+0.7%" positive />
                <HoldingRow symbol="BTC" name="Bitcoin" value="$19,380" change="-0.9%" />
                <HoldingRow symbol="CASH" name="Cash Reserve" value="$14,220" change="0.0%" positive />
              </CardContent>
            </Card>
          </div>
        </section>
      </div>
    </main>
  );
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

function MetricTile({ label, value, change }: { label: string; value: string; change: string }) {
  return (
    <Card className="bg-white/95">
      <CardContent className="space-y-1 p-5">
        <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
        <p className="text-2xl font-bold tracking-tight">{value}</p>
        <p className="text-sm text-muted-foreground">{change}</p>
      </CardContent>
    </Card>
  );
}

function LegendRow({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <li className="flex items-center justify-between rounded-lg border border-border px-3 py-2">
      <span className="inline-flex items-center gap-2">
        <span className={`h-3 w-3 rounded ${color}`} />
        {label}
      </span>
      <span className="font-semibold">{value}</span>
    </li>
  );
}

function HoldingRow({
  symbol,
  name,
  value,
  change,
  positive = false,
}: {
  symbol: string;
  name: string;
  value: string;
  change: string;
  positive?: boolean;
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border px-3 py-2">
      <div>
        <p className="text-sm font-semibold">{symbol}</p>
        <p className="text-xs text-muted-foreground">{name}</p>
      </div>
      <div className="text-right">
        <p className="text-sm font-semibold">{value}</p>
        <p className={`text-xs ${positive ? "text-green-600" : "text-destructive"}`}>{change}</p>
      </div>
    </div>
  );
}
