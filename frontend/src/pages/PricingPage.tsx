import { useState } from "react";
import { Link } from "react-router-dom";

import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";

type PricingMode = "individual" | "business";
type BillingCycle = "monthly" | "annual";

type IndividualPlan = {
  name: string;
  monthly: number;
  description: string;
  features: string[];
  cta: string;
  highlighted?: boolean;
  trialDays?: number;
};

const individualPlans: IndividualPlan[] = [
  {
    name: "Base",
    monthly: 9,
    description: "For investors getting started with simple portfolio tracking and planning.",
    features: ["Portfolio dashboard", "Account connections", "Core insights"],
    cta: "Choose Base",
  },
  {
    name: "Pro",
    monthly: 15,
    description: "For focused investors who want stronger analytics and better visibility.",
    features: ["Everything in Base", "Advanced analytics", "Priority support"],
    cta: "Start 14-day trial",
    highlighted: true,
    trialDays: 14,
  },
  {
    name: "Wealth Manager",
    monthly: 30,
    description: "For advanced users managing larger portfolios with deeper planning needs.",
    features: ["Everything in Pro", "Expanded limits", "Premium workflows"],
    cta: "Choose Wealth Manager",
  },
];

function formatPrice(value: number): string {
  return `$${value.toFixed(2)}`;
}

export function PricingPage() {
  const [mode, setMode] = useState<PricingMode>("individual");
  const [billing, setBilling] = useState<BillingCycle>("monthly");
  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-8">
        <p className="text-sm text-muted-foreground">Plans</p>
        <h1 className="font-display text-4xl font-bold tracking-tight">Pricing</h1>
      </div>

      <div className="mb-3 inline-flex rounded-lg border border-border bg-white p-1">
        <button
          type="button"
          onClick={() => setMode("individual")}
          className={`rounded-md px-4 py-2 text-sm font-semibold transition ${
            mode === "individual" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-secondary"
          }`}
        >
          Individual
        </button>
        <button
          type="button"
          onClick={() => setMode("business")}
          className={`rounded-md px-4 py-2 text-sm font-semibold transition ${
            mode === "business" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-secondary"
          }`}
        >
          Business
        </button>
      </div>

      <div className="mb-8 flex items-center justify-center">
        <div className="flex items-center gap-3 rounded-full border border-border bg-white px-3 py-1.5">
          <button
            type="button"
            onClick={() => setBilling("monthly")}
            className={`text-sm font-semibold transition ${billing === "monthly" ? "text-foreground" : "text-muted-foreground"}`}
          >
            Monthly
          </button>
          <button
            type="button"
            role="switch"
            aria-checked={billing === "annual"}
            aria-label="Toggle billing cycle"
            onClick={() => setBilling((current) => (current === "monthly" ? "annual" : "monthly"))}
            className="relative h-5 w-9 rounded-full bg-secondary transition"
          >
            <span
              className={`absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-primary transition ${billing === "annual" ? "translate-x-[16px]" : "translate-x-0"}`}
            />
          </button>
          <button
            type="button"
            onClick={() => setBilling("annual")}
            className={`text-sm font-semibold transition ${billing === "annual" ? "text-foreground" : "text-muted-foreground"}`}
          >
            Annual
          </button>
        </div>
      </div>

      {mode === "individual" ? (
        <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {individualPlans.map((plan) => {
            const annualPrice = plan.monthly * 12 * 0.9;
            const price = billing === "annual" ? annualPrice : plan.monthly;
            const cycle = billing === "annual" ? "/yr" : "/mo";
            return (
              <Card key={plan.name} className={`${plan.highlighted ? "border-primary/50 bg-white" : "bg-white/95"} min-h-[430px] flex flex-col`}>
                <CardHeader>
                  <div className="mb-2 flex items-center justify-between">
                    <CardTitle className="font-display text-2xl">{plan.name}</CardTitle>
                    {plan.highlighted ? <Badge>Popular</Badge> : null}
                  </div>
                  <div className="flex items-end gap-1">
                    <span className="font-display text-3xl font-bold tracking-tight">{formatPrice(price)}</span>
                    <span className="pb-1 text-sm text-muted-foreground">{cycle}</span>
                    {billing === "annual" ? (
                      <span className="mb-1 ml-1 rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-semibold text-primary">
                        10% off
                      </span>
                    ) : null}
                  </div>
                  <CardDescription>{plan.description}</CardDescription>
                  {plan.trialDays ? <p className="text-xs font-semibold text-primary">{plan.trialDays}-day free trial</p> : null}
                </CardHeader>
                <CardContent className="flex flex-1 flex-col">
                  <ul className="space-y-2 text-sm text-muted-foreground">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-center gap-2">
                        <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/80" aria-hidden="true" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <Link to="/signup" className="mt-auto pt-6">
                    <Button className="w-full" variant={plan.highlighted ? "default" : "outline"}>
                      {plan.cta}
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            );
          })}
        </section>
      ) : (
        <section className="grid min-h-[430px] place-items-center">
          <Card className="w-full max-w-xl bg-white/95 min-h-[430px] flex flex-col">
            <CardHeader>
              <div className="mb-2 flex items-center justify-between">
                <CardTitle className="font-display text-2xl">Business</CardTitle>
                <Badge>Coming soon</Badge>
              </div>
              <CardDescription>Business pricing is currently being finalized.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-1 flex-col justify-between">
              <p className="text-sm text-muted-foreground">
                We are currently designing business workflows and team-level capabilities.
              </p>
            </CardContent>
          </Card>
        </section>
      )}
      <p className="mt-6 text-center text-xs text-muted-foreground">*All prices in USD.</p>
    </main>
  );
}



