import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { ShieldCheck } from "lucide-react";

import { login as loginRequest } from "../api/auth";
import { ApiError } from "../api/http";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { useAuth } from "../context/AuthContext";

const loginImage =
  "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1400&q=80";

export function LoginPage() {
  const { user, refreshAuth } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberDevice, setRememberDevice] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (user) {
    return <Navigate to="/" replace />;
  }

  const fromPath = typeof location.state === "object" && location.state && "from" in location.state
    ? String(location.state.from)
     : "/";

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const response = await loginRequest(email.trim(), password);
      if (response.requires_login_code) {
        const rememberParam = rememberDevice ? "&remember=1" : "";
        navigate(`/login-verify?email=${encodeURIComponent(email.trim())}${rememberParam}`);
      } else {
        await refreshAuth();
        navigate(fromPath, { replace: true });
      }
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
    <main className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="grid items-stretch gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <Card className="overflow-hidden border-primary/20 bg-gradient-to-br from-[#14171b] to-[#252a31] text-white">
          <CardContent className="relative h-full p-0">
            <img src={loginImage} alt="Market charts on trading screen" className="h-72 w-full object-cover opacity-75 lg:h-full" />
            <div className="pointer-events-none absolute inset-0 hidden bg-gradient-to-t from-[#0d1014] via-transparent to-transparent lg:block" />
          </CardContent>
        </Card>

        <Card className="mx-auto w-full max-w-md bg-white/95 lg:max-w-none">
          <CardHeader>
            <Badge className="w-fit">Secure Login</Badge>
            <CardTitle className="font-display text-3xl">Welcome back</CardTitle>
            <CardDescription>Use your credentials to access your dashboard.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={onSubmit}>
              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium">Email</label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                  autoComplete="email"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="password" className="text-sm font-medium">Password</label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                  autoComplete="current-password"
                />
              </div>

              <label className="flex items-start gap-2 rounded-lg border border-border bg-secondary/40 p-3 text-sm" htmlFor="remember-device">
                <input
                  id="remember-device"
                  type="checkbox"
                  className="mt-1 h-4 w-4 rounded border-border"
                  checked={rememberDevice}
                  onChange={(event) => setRememberDevice(event.target.checked)}
                />
                <span>Remember this device and skip security code next time.</span>
              </label>

              {error ? <p className="text-sm text-destructive">{error}</p> : null}

              <Button className="w-full" type="submit" disabled={submitting}>
                {submitting ? "Logging in..." : "Login"}
              </Button>
            </form>

            <div className="mt-6 rounded-lg border border-border bg-secondary/40 p-3 text-sm text-muted-foreground">
              <div className="mb-1 flex items-center gap-2 text-foreground">
                <ShieldCheck className="h-4 w-4 text-primary" />
                Protected by cookie + CSRF auth
              </div>
              New here? <Link className="font-semibold text-primary" to="/signup">Create an account</Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
