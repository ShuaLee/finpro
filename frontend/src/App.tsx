import { useState, type FormEvent } from "react";

import { ApiError } from "./api/http";
import { useAuth } from "./context/AuthContext";
import { MainContent } from "./MainContent";
import { SideNav } from "./SideNav";
import { TopNav } from "./TopNav";

function App() {
  const { user, loading, login } = useAuth();
  const [showLoginForm, setShowLoginForm] = useState(false);
  const [sideNavCollapsed, setSideNavCollapsed] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await login(email, password);
      setPassword("");
      setShowLoginForm(false);
      window.history.replaceState({}, "", "/");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Unable to log in.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <main className="app-screen">
        <p className="status-text">Loading...</p>
      </main>
    );
  }

  if (user) {
    return (
      <div className="app-shell app-shell-authenticated">
        <SideNav collapsed={sideNavCollapsed} onToggleCollapsed={() => setSideNavCollapsed((current) => !current)} />
        <div className="app-main-shell">
          <TopNav />
          <div className="app-layout">
            <MainContent />
          </div>
        </div>
      </div>
    );
  }

  return (
    <main className="app-screen">
      {!showLoginForm ? (
        <button type="button" className="primary-button" onClick={() => setShowLoginForm(true)}>
          Log in
        </button>
      ) : (
        <form className="login-form" onSubmit={handleSubmit}>
          <label className="field-label" htmlFor="login-email">
            Email
          </label>
          <input
            id="login-email"
            className="text-field"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />

          <label className="field-label" htmlFor="login-password">
            Password
          </label>
          <input
            id="login-password"
            className="text-field"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />

          {error ? <p className="error-text">{error}</p> : null}

          <div className="form-actions">
            <button type="button" className="secondary-button" onClick={() => setShowLoginForm(false)} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="primary-button" disabled={submitting}>
              {submitting ? "Logging in..." : "Log in"}
            </button>
          </div>
        </form>
      )}
    </main>
  );
}

export default App;
