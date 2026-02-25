import { useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, Columns3 } from "lucide-react";

import { Card, CardContent } from "../components/ui/card";

export function HoldingsPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const scope = (searchParams.get("scope") ?? "").trim();
  const name = (searchParams.get("name") ?? "").trim();

  const scopeLabel = useMemo(() => {
    if (scope === "asset_type" && name) return `Asset Type: ${name}`;
    if (scope === "account" && name) return `Account: ${name}`;
    if (scope === "accounts") return "All Accounts";
    return "All Holdings";
  }, [name, scope]);

  return (
    <main className="w-full pb-10 pt-4">
      <div className="mx-auto w-full max-w-[1680px] px-4 sm:px-6 lg:px-8">
        <Card className="border-blue-100 bg-white">
          <CardContent className="space-y-4 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="space-y-1">
                <h1 className="font-display text-2xl font-bold tracking-tight text-slate-900">All Holdings</h1>
                <p className="text-sm text-slate-600">Scope: {scopeLabel}</p>
              </div>
              <button
                type="button"
                onClick={() => navigate(-1)}
                className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition-colors hover:bg-slate-100 hover:text-slate-900"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                <span>Back</span>
              </button>
            </div>

            <div className="rounded-xl border border-dashed border-blue-100 bg-[#f4f6fa] px-4 py-5 text-sm text-slate-600">
              <div className="mb-2 inline-flex items-center gap-2 text-slate-800">
                <Columns3 className="h-4 w-4" />
                <span className="font-semibold">Holdings table placeholder</span>
              </div>
              <p>
                This screen is wired for scoped navigation. Next step is to render the unified holdings table with filters,
                sorting, and pagination.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
