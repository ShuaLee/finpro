import { useMemo, useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";

import { verifyLoginCode } from "../api/auth";
import { ApiError } from "../api/http";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { FloatingInput } from "../components/ui/floating-input";
import { useAuth } from "../context/AuthContext";

export function LoginVerifyCodePage() {
  const { user, refreshAuth } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const defaultEmail = useMemo(() => searchParams.get("email") ?? "", [searchParams]);
  const defaultRemember = useMemo(() => searchParams.get("remember") === "1", [searchParams]);

  const [email, setEmail] = useState(defaultEmail);
  const [code, setCode] = useState("");
  const [rememberDevice, setRememberDevice] = useState(defaultRemember);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (user) {
    return <Navigate to="/" replace />;
  }

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await verifyLoginCode(email.trim(), code.trim(), rememberDevice);
      await refreshAuth();
      navigate("/", { replace: true });
    } catch (caught) {
      if (caught instanceof ApiError) {
        setError(caught.message);
      } else {
        setError("Unable to verify security code.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <Card className="mx-auto max-w-lg bg-white/95">
        <CardHeader>
          <Badge className="w-fit">Login Security Code</Badge>
          <CardTitle className="font-display text-3xl">Confirm sign in</CardTitle>
          <CardDescription>Enter the 6-digit security code sent to your email.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={onSubmit}>
            <FloatingInput
              id="login-email"
              label="Email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />

            <FloatingInput
              id="login-code"
              label="6-digit code"
              type="text"
              inputMode="numeric"
              pattern="[0-9]{6}"
              maxLength={6}
              value={code}
              onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
              required
            />

            <label className="flex items-start gap-2 rounded-lg border border-border bg-secondary/40 p-3 text-sm" htmlFor="remember-device-login-verify">
              <input
                id="remember-device-login-verify"
                type="checkbox"
                className="mt-1 h-4 w-4 rounded border-border"
                checked={rememberDevice}
                onChange={(event) => setRememberDevice(event.target.checked)}
              />
              <span>Remember this device and skip code on future logins.</span>
            </label>

            {error ? <p className="text-sm text-destructive">{error}</p> : null}

            <Button className="w-full" type="submit" disabled={submitting}>
              {submitting ? "Verifying..." : "Verify and sign in"}
            </Button>
          </form>

          <p className="mt-5 text-sm text-muted-foreground">
            Back to <Link className="font-semibold text-primary" to="/login">login</Link>
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
