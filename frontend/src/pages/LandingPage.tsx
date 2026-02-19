import { type ComponentType, type SVGProps } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, BarChart3, Check, Lock, ShieldCheck, Sparkles, Wallet } from "lucide-react";

import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";

const heroImage =
  "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1600&q=80";
const mobileImage =
  "https://images.unsplash.com/photo-1559526324-593bc073d938?auto=format&fit=crop&w=1200&q=80";
const planningImage =
  "https://images.unsplash.com/photo-1520607162513-77705c0f0d4a?auto=format&fit=crop&w=1200&q=80";
const advisorImage =
  "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?auto=format&fit=crop&w=1400&q=80";

export function LandingPage() {
  return (
    <main>
      <section className="mx-auto grid w-full max-w-7xl gap-8 px-4 pb-12 pt-10 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:pb-20 lg:pt-16">
        <div className="animate-fade-up space-y-6">
          <Badge className="rounded-full px-3 py-1 text-xs">Investment Overview Platform</Badge>
          <h1 className="font-display text-4xl font-bold leading-tight tracking-tight text-foreground sm:text-5xl lg:text-6xl">
            Build wealth visibility with a calm, modern dashboard.
          </h1>
          <p className="max-w-2xl text-lg text-muted-foreground">
            FinPro keeps your financial picture clear with subscription-aware guardrails, secure cookie auth,
            and a focused experience designed for long-term investors.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <Link to="/signup">
              <Button size="lg" className="gap-2 shadow-lg shadow-primary/25">Start free <ArrowRight className="h-4 w-4" /></Button>
            </Link>
            <Link to="/login">
              <Button size="lg" variant="outline">Log in</Button>
            </Link>
          </div>
          <div className="grid max-w-xl grid-cols-1 gap-2 text-sm text-muted-foreground sm:grid-cols-2">
            {[
              "Email verification built-in",
              "Cookie + CSRF protection",
              "Subscription-aware limits",
              "Portfolio-ready architecture",
            ].map((item) => (
              <div key={item} className="inline-flex items-center gap-2 rounded-lg bg-white/65 px-3 py-2">
                <Check className="h-4 w-4 text-primary" />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
          <Card className="overflow-hidden border-white/50 bg-white/80 shadow-2xl backdrop-blur">
            <img src={heroImage} alt="Investor checking a laptop dashboard" className="h-full min-h-[340px] w-full object-cover" />
          </Card>
          <Card className="hidden overflow-hidden border-primary/20 bg-white/80 backdrop-blur sm:block lg:hidden">
            <img src={advisorImage} alt="Advisor reviewing investment summary" className="h-full min-h-[340px] w-full object-cover" />
          </Card>
        </div>
      </section>

      <section className="mx-auto grid w-full max-w-7xl gap-4 px-4 pb-14 sm:grid-cols-2 sm:px-6 lg:grid-cols-4 lg:px-8">
        <MetricCard label="Data Sync Success" value="99.9%" icon={ShieldCheck} />
        <MetricCard label="Avg Session" value="11m" icon={BarChart3} />
        <MetricCard label="Security Layers" value="3" icon={Lock} />
        <MetricCard label="Assets Tracked" value="10k+" icon={Wallet} />
      </section>

      <section className="mx-auto grid w-full max-w-7xl gap-6 px-4 pb-14 sm:px-6 lg:grid-cols-3 lg:px-8">
        <FeatureCard
          title="Portfolio at a glance"
          copy="View performance, allocations, and account health from one clear command center."
          image={mobileImage}
          alt="Mobile financial chart interface"
        />
        <FeatureCard
          title="Plan-aware controls"
          copy="Limits and capabilities are tied directly to your subscription for predictable behavior."
          image={planningImage}
          alt="Team discussing financial planning"
        />
        <Card className="border-primary/20 bg-gradient-to-br from-primary/10 via-background to-background">
          <CardContent className="space-y-4 p-6">
            <Badge variant="secondary" className="rounded-full">Production Ready</Badge>
            <h3 className="font-display text-2xl font-semibold">Made for fast iteration</h3>
            <p className="text-muted-foreground">
              Ship authentication now, then layer in holdings, account sync, and analytics without rewriting your foundations.
            </p>
            <Link to="/signup">
              <Button className="w-full gap-2">Create your account <ArrowRight className="h-4 w-4" /></Button>
            </Link>
          </CardContent>
        </Card>
      </section>

      <section className="mx-auto mb-16 w-full max-w-7xl px-4 sm:px-6 lg:px-8">
        <Card className="overflow-hidden border-primary/20 bg-gradient-to-br from-[#111315] via-[#1e2228] to-[#12161b] text-white">
          <CardContent className="grid gap-8 p-8 sm:p-10 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="space-y-4">
              <Badge variant="secondary" className="w-fit bg-white/20 text-white">Ready For Launch</Badge>
              <h2 className="font-display text-3xl font-bold leading-tight sm:text-4xl">
                Start with auth and onboarding now, then scale into full portfolio intelligence.
              </h2>
              <p className="max-w-2xl text-white/80">
                FinPro already matches your backend auth model and subscription flow, so your frontend can expand without security rewrites.
              </p>
              <div className="flex flex-wrap gap-3">
                <Link to="/signup">
                  <Button size="lg" variant="secondary" className="bg-white text-[#111315] hover:bg-white/90">Create free account</Button>
                </Link>
                <Link to="/login">
                  <Button size="lg" variant="ghost" className="border border-white/40 text-white hover:bg-white/10">Log in</Button>
                </Link>
              </div>
            </div>
            <div className="rounded-2xl border border-white/20 bg-white/10 p-6">
              <div className="mb-4 inline-flex items-center gap-2 text-sm text-white/90">
                <Sparkles className="h-4 w-4" />
                What you can add next
              </div>
              <ul className="space-y-3 text-sm text-white/85">
                <li className="rounded-lg bg-white/10 px-3 py-2">Portfolio value and allocation widgets</li>
                <li className="rounded-lg bg-white/10 px-3 py-2">Account sync and transaction pipelines</li>
                <li className="rounded-lg bg-white/10 px-3 py-2">Plan-based feature unlocks and pricing UI</li>
                <li className="rounded-lg bg-white/10 px-3 py-2">Analytics and drift notifications</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </section>
    </main>
  );
}

function MetricCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string;
  icon: ComponentType<SVGProps<SVGSVGElement>>;
}) {
  return (
    <Card className="bg-white/80">
      <CardContent className="flex items-center justify-between p-5">
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
          <p className="mt-1 text-2xl font-bold">{value}</p>
        </div>
        <Icon className="h-5 w-5 text-primary" />
      </CardContent>
    </Card>
  );
}

function FeatureCard({
  title,
  copy,
  image,
  alt,
}: {
  title: string;
  copy: string;
  image: string;
  alt: string;
}) {
  return (
    <Card className="overflow-hidden bg-white/85">
      <img src={image} alt={alt} className="h-48 w-full object-cover" loading="lazy" />
      <CardContent className="space-y-2 p-6">
        <h3 className="font-display text-xl font-semibold">{title}</h3>
        <p className="text-sm text-muted-foreground">{copy}</p>
      </CardContent>
    </Card>
  );
}
