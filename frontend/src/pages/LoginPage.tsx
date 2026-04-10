import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { ChartNoAxesCombined } from "lucide-react";

import { login as loginRequest } from "../api/auth";
import { ApiError } from "../api/http";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { FloatingInput } from "../components/ui/floating-input";
import { useAuth } from "../context/AuthContext";

export function LoginPage() {
  const { user, refreshAuth } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  if (user) {
    return <Navigate to="/" replace />;
  }

  const fromPath = typeof location.state === "object" && location.state && "from" in location.state
    ? String(location.state.from)
    : "/";

  const onSubmitLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await loginRequest(email.trim(), password);
      setSuccessMessage(response.detail);
      await refreshAuth();
      navigate(fromPath, { replace: true });
    } catch (caught) {
      if (caught instanceof ApiError) {
        setError(caught.message);
      } else {
        setError("Login failed. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="w-full">
      <div className="mx-auto flex h-20 w-full max-w-7xl items-center px-4 sm:px-6 lg:px-8">
        <Link to="/" className="inline-flex items-center gap-2">
          <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <ChartNoAxesCombined className="h-5 w-5" />
          </span>
          <span className="font-display text-[1.45rem] font-bold tracking-tight">FinPro</span>
        </Link>
      </div>

      <div className="mx-auto w-full max-w-7xl px-4 pb-10 pt-6 sm:px-6 lg:px-8">
        <Card className="mx-auto max-w-lg bg-white/95">
          <CardHeader>
            <CardTitle className="font-display text-3xl">Welcome back</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={onSubmitLogin}>
              <FloatingInput
                id="login-email"
                label="Email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
                autoComplete="email"
              />

              <div className="space-y-1">
                <FloatingInput
                  id="login-password"
                  label="Password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                  autoComplete="current-password"
                />
                <p>
                  <Link to="/forgot-password" className="text-sm font-semibold text-primary">
                    Forgot password?
                  </Link>
                </p>
              </div>

              {error ? <p className="text-sm text-destructive">{error}</p> : null}
              {successMessage ? <p className="text-sm text-primary">{successMessage}</p> : null}

              <Button className="w-full" type="submit" disabled={submitting}>
                {submitting ? "Logging in..." : "Continue"}
              </Button>
            </form>

            <p className="mt-6 text-sm text-muted-foreground">
              New here? <Link className="font-semibold text-primary" to="/signup">Create an account</Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
