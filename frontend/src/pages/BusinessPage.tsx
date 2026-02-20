import { Badge } from "../components/ui/badge";

export function BusinessPage() {
  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
      <h1 className="font-display text-4xl font-bold tracking-tight">Business</h1>
      <p className="mt-4 max-w-3xl text-base text-muted-foreground">
        Business workflows are being designed for advisors and teams that manage multiple portfolios at scale.
      </p>

      <div className="mt-8 max-w-xl rounded-xl border border-border bg-white/90 p-6">
        <h2 className="font-display text-2xl font-semibold tracking-tight">Business features</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Multi-client workflows, team collaboration, and operational controls are currently in planning.
        </p>
        <div className="mt-4">
          <Badge>Coming soon</Badge>
        </div>
      </div>
    </main>
  );
}

