import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

import heroPortfolioRise from "../assets/hero-portfolio-rise.png";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";

export function LandingPage() {
  return (
    <main>
      <section className="mx-auto w-full max-w-6xl px-4 pb-24 pt-16 sm:px-6 lg:pb-28 lg:pt-24">
        <div className="grid items-start gap-10 lg:grid-cols-[1fr_0.85fr] lg:gap-12">
          <div className="space-y-8">
            <h1 className="max-w-4xl font-display text-5xl font-bold leading-[1.02] tracking-tight sm:text-6xl lg:text-7xl">
              Better visibility for long-term investors.
            </h1>
            <p className="max-w-2xl text-base text-muted-foreground sm:text-lg">
              Build and monitor your portfolios in one calm workspace, with secure sign-in and plan-aware controls from day one.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link to="/signup">
                <Button size="lg" className="gap-2">
                  Get started
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link to="/login">
                <Button size="lg" variant="outline">
                  Log in
                </Button>
              </Link>
            </div>
          </div>

          <div className="relative hidden h-[480px] overflow-hidden lg:block">
            <img
              src={heroPortfolioRise}
              alt="Long-term portfolio trend rising"
              className="absolute -right-10 top-0 h-full w-[115%] object-cover opacity-80"
            />
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-background via-background/65 to-transparent" />
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-background/45 via-transparent to-background/55" />
          </div>
        </div>
      </section>

      <section className="border-y border-border/70 bg-white/60">
        <div className="mx-auto grid w-full max-w-6xl gap-6 px-4 py-10 sm:grid-cols-3 sm:px-6">
          <Stat value="99.9%" label="Data reliability" />
          <Stat value="3" label="Security controls" />
          <Stat value="10k+" label="Tracked positions" />
        </div>
      </section>

      <section id="security" className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6 lg:py-20 scroll-mt-24">
        <div className="mb-8 max-w-2xl">
          <h2 className="font-display text-3xl font-semibold tracking-tight sm:text-4xl">Everything you need, without clutter.</h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          <FeatureCard
            title="Portfolio overview"
            copy="See performance, allocations, and account health in one place."
            cta="View dashboard"
          />
          <FeatureCard
            title="Secure authentication"
            copy="Email verification, login code support, cookie sessions, and CSRF protection."
            cta="See security"
          />
          <FeatureCard
            title="Plan-aware controls"
            copy="Feature access and limits that map directly to your subscription tier."
            cta="See plans"
          />
        </div>
      </section>

      <section id="learn" className="mx-auto mb-10 w-full max-w-6xl px-4 sm:px-6 scroll-mt-24">
        <Card className="border-black/10 bg-white/85">
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Learn</p>
            <h3 className="mt-1 font-display text-2xl font-bold tracking-tight">Learn the platform, portfolio structure, and security model quickly.</h3>
          </CardContent>
        </Card>
      </section>

      <section id="pricing" className="mx-auto mb-20 w-full max-w-6xl px-4 sm:px-6 scroll-mt-24">
        <Card className="border-black/10 bg-white/90">
          <CardContent className="flex flex-col gap-6 p-8 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Ready to begin?</p>
              <h3 className="mt-1 font-display text-2xl font-bold tracking-tight">Create your FinPro account.</h3>
            </div>
            <Link to="/signup">
              <Button size="lg">Create free account</Button>
            </Link>
          </CardContent>
        </Card>
      </section>

      <section id="business" className="mx-auto mb-16 w-full max-w-6xl px-4 sm:px-6 scroll-mt-24">
        <Card className="border-black/10 bg-white/85">
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Business</p>
            <h3 className="mt-1 font-display text-2xl font-bold tracking-tight">Built for individual investors now, with a path to advisor and business workflows.</h3>
          </CardContent>
        </Card>
      </section>
    </main>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div className="space-y-1">
      <p className="font-display text-4xl font-bold tracking-tight">{value}</p>
      <p className="text-sm text-muted-foreground">{label}</p>
    </div>
  );
}

function FeatureCard({
  title,
  copy,
  cta,
}: {
  title: string;
  copy: string;
  cta: string;
}) {
  return (
    <Card className="border-black/10 bg-white/85">
      <CardContent className="space-y-4 p-6">
        <h3 className="font-display text-xl font-semibold">{title}</h3>
        <p className="text-sm text-muted-foreground">{copy}</p>
        <Link to="/signup" className="inline-flex items-center text-sm font-semibold text-foreground hover:opacity-75">
          {cta}
        </Link>
      </CardContent>
    </Card>
  );
}
