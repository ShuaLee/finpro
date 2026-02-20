export function LearnPage() {
  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
      <h1 className="font-display text-4xl font-bold tracking-tight">Learn</h1>
      <p className="mt-4 max-w-3xl text-base text-muted-foreground">
        Learn how to set up your account, structure your portfolios, and use FinPro’s core features with confidence.
      </p>

      <div className="mt-8 grid gap-4 md:grid-cols-3">
        <article className="rounded-xl border border-border bg-white/90 p-5">
          <h2 className="font-display text-2xl font-semibold tracking-tight">Getting started</h2>
          <p className="mt-2 text-sm text-muted-foreground">Create an account, verify your email, and complete core profile setup.</p>
        </article>
        <article className="rounded-xl border border-border bg-white/90 p-5">
          <h2 className="font-display text-2xl font-semibold tracking-tight">Portfolio basics</h2>
          <p className="mt-2 text-sm text-muted-foreground">Understand account structures, holdings, and valuation views.</p>
        </article>
        <article className="rounded-xl border border-border bg-white/90 p-5">
          <h2 className="font-display text-2xl font-semibold tracking-tight">Security settings</h2>
          <p className="mt-2 text-sm text-muted-foreground">Manage email verification, password updates, and account preferences.</p>
        </article>
      </div>
    </main>
  );
}

