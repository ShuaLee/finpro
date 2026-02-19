import { type ComponentType, type ReactNode, useMemo, useState } from "react";
import { Building2, ChevronDown, Landmark, Menu, Wallet, X } from "lucide-react";

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
    const width = 760;
    const height = 230;

    return netWorthSeries
      .map((value, index) => {
        const x = (index / (netWorthSeries.length - 1)) * width;
        const y = height - ((value - min) / (max - min || 1)) * height;
        return `${x},${y}`;
      })
      .join(" ");
  }, []);

  return (
    <main className="mx-auto w-full max-w-7xl px-4 pb-8 pt-4 sm:px-6 lg:px-8">
      <div className="grid items-start gap-5 lg:grid-cols-[280px_1fr]">
        <div className="hidden lg:block">
          <div className="fixed left-[max(1rem,calc((100vw-80rem)/2+2rem))] top-24 h-[calc(100vh-7.5rem)] w-[280px]">
            <SidebarPanel
              accountGroups={accountGroups}
              expandedGroup={expandedGroup}
              setExpandedGroup={setExpandedGroup}
              className="h-full"
            />
          </div>
        </div>

        {sidebarOpen ? (
          <div className="fixed inset-0 z-50 bg-black/35 lg:hidden" onClick={() => setSidebarOpen(false)}>
            <SidebarPanel
              accountGroups={accountGroups}
              expandedGroup={expandedGroup}
              setExpandedGroup={setExpandedGroup}
              className="h-full w-80 max-w-[85vw] rounded-none border-r bg-white"
            >
              <button
                type="button"
                onClick={() => setSidebarOpen(false)}
                className="rounded-md border border-border p-1"
              >
                <X className="h-4 w-4" />
              </button>
            </SidebarPanel>
          </div>
        ) : null}

        <section className="space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setSidebarOpen(true)}
                className="inline-flex rounded-lg border border-border bg-white p-2 shadow-sm lg:hidden"
              >
                <Menu className="h-5 w-5" />
              </button>
              <div>
                <p className="text-sm text-muted-foreground">Welcome back</p>
                <h1 className="font-display text-3xl font-bold">Dashboard</h1>
                <p className="text-sm text-muted-foreground">Signed in as {user?.email}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {["Overview", "Performance", "Allocations"].map((tab) => (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setActiveTab(tab)}
                  className={`rounded-full px-3 py-1.5 text-sm font-medium ${
                    activeTab === tab ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>

          <Card className="bg-white/95">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="font-display text-2xl">Net Worth</CardTitle>
                <CardDescription>12-month trend overview</CardDescription>
              </div>
              <Badge>$225,400</Badge>
            </CardHeader>
            <CardContent>
              <div className="mb-3 inline-flex rounded-full bg-secondary px-2 py-1 text-xs text-muted-foreground">
                +4.8% in last 30 days
              </div>
              <div className="overflow-hidden rounded-lg border border-border bg-[#f8f9fb] p-3">
                <svg viewBox="0 0 760 230" className="h-56 w-full">
                  {[0, 1, 2, 3, 4].map((i) => (
                    <line
                      key={`grid-${i}`}
                      x1="0"
                      y1={i * 57.5}
                      x2="760"
                      y2={i * 57.5}
                      stroke="rgba(15,23,42,0.12)"
                      strokeDasharray="4 5"
                    />
                  ))}
                  <polyline
                    fill="none"
                    stroke="#111315"
                    strokeWidth="4"
                    strokeLinecap="round"
                    points={graphPoints}
                  />
                  <circle cx="760" cy="0" r="0" fill="#111315" />
                </svg>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-5 lg:grid-cols-2">
            <Card className="bg-white/95">
              <CardHeader>
                <CardTitle className="font-display text-xl">Allocation Pie</CardTitle>
                <CardDescription>Current allocation split</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-[190px_1fr]">
                <svg viewBox="0 0 140 140" className="mx-auto h-44 w-44 -rotate-90">
                  <circle cx="70" cy="70" r="48" fill="none" stroke="#e7e9ee" strokeWidth="22" />
                  <circle cx="70" cy="70" r="48" fill="none" stroke="#12151b" strokeWidth="22" strokeDasharray="301.6" strokeDashoffset="174.9" />
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
                <CardTitle className="font-display text-xl">Allocation Bars</CardTitle>
                <CardDescription>Category exposure snapshot</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <BarRow label="US Equities" value={74} />
                <BarRow label="International" value={48} />
                <BarRow label="Fixed Income" value={31} />
                <BarRow label="Cash" value={22} />
                <BarRow label="Crypto" value={14} />
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
  className,
  children,
}: {
  accountGroups: AccountGroup[];
  expandedGroup: string;
  setExpandedGroup: (value: string) => void;
  className?: string;
  children?: ReactNode;
}) {
  return (
    <Card className={`flex flex-col bg-white/95 ${className ?? ""}`} onClick={(e) => e.stopPropagation()}>
      <CardHeader className="shrink-0 space-y-3">
        <div className="flex items-center justify-between">
          <Badge className="w-fit">Navigation</Badge>
          {children}
        </div>
      </CardHeader>
      <CardContent className="flex-1 space-y-4 overflow-y-auto">
        <div className="space-y-2 pb-1">
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
        </div>
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

function BarRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-semibold">{value}%</span>
      </div>
      <div className="h-2.5 w-full rounded-full bg-secondary">
        <div className="h-2.5 rounded-full bg-primary" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}
