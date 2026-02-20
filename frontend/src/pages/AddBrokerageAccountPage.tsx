import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { type AccountCreateOptions, createAccount, getAccountCreateOptions } from "../api/accounts";
import { ApiError } from "../api/http";
import { Card, CardContent, CardHeader } from "../components/ui/card";

export function AddBrokerageAccountPage() {
  const navigate = useNavigate();
  const [options, setOptions] = useState<AccountCreateOptions | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [broker, setBroker] = useState("");
  const [portfolioId, setPortfolioId] = useState<number | null>(null);
  const [accountTypeId, setAccountTypeId] = useState<number | null>(null);
  const [classificationDefinitionId, setClassificationDefinitionId] = useState<number | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const payload = await getAccountCreateOptions();
        setOptions(payload);
        setPortfolioId(payload.portfolios[0]?.id ?? null);
        setAccountTypeId(payload.account_types[0]?.id ?? null);
        setClassificationDefinitionId(payload.classification_definitions[0]?.id ?? null);
      } catch (caught) {
        const message = caught instanceof Error ? caught.message : "Unable to load account form options.";
        setError(message);
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, []);

  const canSubmit = useMemo(
    () => name.trim().length > 0 && portfolioId !== null && accountTypeId !== null && classificationDefinitionId !== null,
    [name, portfolioId, accountTypeId, classificationDefinitionId],
  );

  const onSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!canSubmit || saving) return;

    setSaving(true);
    setError(null);
    try {
      await createAccount({
        portfolio_id: portfolioId!,
        name: name.trim(),
        account_type_id: accountTypeId!,
        broker: broker.trim() || undefined,
        classification_definition_id: classificationDefinitionId!,
      });
      navigate("/", { replace: true });
    } catch (caught) {
      if (caught instanceof ApiError) {
        setError(caught.message);
      } else {
        setError("Unable to create brokerage account.");
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <main className="w-full pb-10 pt-4">
      <div className="mx-auto w-full max-w-[920px] px-4 sm:px-6 lg:px-8">
        <Card className="bg-white/95">
          <CardHeader className="space-y-2">
            <p className="text-sm text-muted-foreground">Accounts</p>
            <h1 className="font-display text-3xl font-bold tracking-tight">Add Brokerage Account</h1>
          </CardHeader>
          <CardContent>
            {loading ? <p className="text-sm text-muted-foreground">Loading form options...</p> : null}
            {error ? <p className="mb-4 text-sm text-destructive">{error}</p> : null}
            {!loading && options ? (
              <form onSubmit={onSubmit} className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <label className="space-y-1 text-sm">
                    <span className="text-muted-foreground">Account Name</span>
                    <input
                      type="text"
                      value={name}
                      onChange={(event) => setName(event.target.value)}
                      className="w-full rounded-md border border-border bg-white px-3 py-2"
                      placeholder="My Brokerage Account"
                      required
                    />
                  </label>
                  <label className="space-y-1 text-sm">
                    <span className="text-muted-foreground">Broker (optional)</span>
                    <input
                      type="text"
                      value={broker}
                      onChange={(event) => setBroker(event.target.value)}
                      className="w-full rounded-md border border-border bg-white px-3 py-2"
                      placeholder="Fidelity / Schwab / etc."
                    />
                  </label>
                </div>

                <div className="grid gap-4 sm:grid-cols-3">
                  <label className="space-y-1 text-sm">
                    <span className="text-muted-foreground">Portfolio</span>
                    <select
                      value={portfolioId ?? ""}
                      onChange={(event) => setPortfolioId(Number(event.target.value))}
                      className="w-full rounded-md border border-border bg-white px-3 py-2"
                    >
                      {options.portfolios.map((portfolio) => (
                        <option key={portfolio.id} value={portfolio.id}>
                          {portfolio.name}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="space-y-1 text-sm">
                    <span className="text-muted-foreground">Account Type</span>
                    <select
                      value={accountTypeId ?? ""}
                      onChange={(event) => setAccountTypeId(Number(event.target.value))}
                      className="w-full rounded-md border border-border bg-white px-3 py-2"
                    >
                      {options.account_types.map((accountType) => (
                        <option key={accountType.id} value={accountType.id}>
                          {accountType.name}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="space-y-1 text-sm">
                    <span className="text-muted-foreground">Classification</span>
                    <select
                      value={classificationDefinitionId ?? ""}
                      onChange={(event) => setClassificationDefinitionId(Number(event.target.value))}
                      className="w-full rounded-md border border-border bg-white px-3 py-2"
                    >
                      {options.classification_definitions.map((classification) => (
                        <option key={classification.id} value={classification.id}>
                          {classification.name}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="submit"
                    disabled={!canSubmit || saving}
                    className="rounded-md border border-border bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-50"
                  >
                    {saving ? "Creating..." : "Create Brokerage Account"}
                  </button>
                  <button
                    type="button"
                    onClick={() => navigate("/", { replace: true })}
                    className="rounded-md border border-border bg-white px-4 py-2 text-sm font-semibold"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
