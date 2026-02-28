import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { ChartNoAxesCombined, CircleUserRound, LogOut, Menu, Moon, Settings, Sun, X } from "lucide-react";

import { ApiError } from "../api/http";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import { Button } from "./ui/button";

export function Header() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const { theme, toggleTheme } = useTheme();
  const menuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (!menuRef.current) {
        return;
      }
      if (event.target instanceof Node && !menuRef.current.contains(event.target)) {
        setProfileMenuOpen(false);
      }
    };

    if (profileMenuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [profileMenuOpen]);

  const onLogout = async () => {
    setLoggingOut(true);
    try {
      await logout();
      setProfileMenuOpen(false);
      setMobileMenuOpen(false);
    } catch (caught) {
      if (caught instanceof ApiError) {
        // no-op
      }
    } finally {
      setLoggingOut(false);
    }
  };

  const onPortfolio = location.pathname === "/" && Boolean(user);
  const onAccounts = location.pathname === "/" && location.hash === "#accounts" && Boolean(user);
  const onAssetTypes = location.pathname === "/" && location.hash === "#asset-types" && Boolean(user);
  const onPricing = location.pathname.startsWith("/pricing");
  const onSecurity = location.pathname.startsWith("/security");
  const onLearn = location.pathname.startsWith("/learn");
  const onBusiness = location.pathname.startsWith("/business");
  const navTabClass = (isActive: boolean) =>
    `relative px-1 py-2 text-[0.95rem] font-semibold transition after:absolute after:bottom-0 after:left-0 after:h-[2px] after:w-full after:rounded-full ${
      isActive
        ? "text-foreground after:bg-primary"
        : "text-muted-foreground hover:text-foreground after:bg-transparent hover:after:bg-primary/35"
    }`;

  return (
    <header className="app-top-nav sticky top-0 z-40 relative border-b border-border bg-background">
      <div className="mx-auto flex h-20 w-full max-w-7xl items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-8">
          <Link to="/" className="inline-flex items-center gap-2">
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <ChartNoAxesCombined className="h-5 w-5" />
            </span>
            <span className="font-display text-[1.45rem] font-bold tracking-tight">FinPro</span>
          </Link>

          <nav className="hidden items-center gap-10 pl-2 lg:pl-4 lg:flex" aria-label="Primary">
            {user ? (
              <>
                <Link to="/" className={navTabClass(onPortfolio && !location.hash)}>
                  Portfolio
                </Link>
                <Link to="/#accounts" className={navTabClass(onAccounts)}>
                  Accounts
                </Link>
                <Link to="/#asset-types" className={navTabClass(onAssetTypes)}>
                  Asset Types
                </Link>
              </>
            ) : (
              <>
                <Link to="/pricing" className={navTabClass(onPricing)}>
                  Pricing
                </Link>
                <Link to="/security" className={navTabClass(onSecurity)}>
                  Security
                </Link>
                <Link to="/learn" className={navTabClass(onLearn)}>
                  Learn
                </Link>
                <Link to="/business" className={navTabClass(onBusiness)}>
                  Business
                </Link>
              </>
            )}
          </nav>
        </div>

        <nav className="hidden items-center gap-2 lg:flex" aria-label="Account">
          {user ? (
            <div className="flex items-center gap-2">
              <div className="relative" ref={menuRef}>
                <button
                  type="button"
                  onClick={() => setProfileMenuOpen((prev) => !prev)}
                  className="inline-flex h-11 w-11 items-center justify-center rounded-full border border-border bg-card hover:bg-secondary"
                  aria-label="Open profile menu"
                >
                  <CircleUserRound className="h-5 w-5 text-primary" />
                </button>

                {profileMenuOpen ? (
                  <div className="absolute right-0 mt-2 w-56 overflow-hidden rounded-xl border border-border bg-card shadow-[0_16px_34px_rgba(15,23,42,0.14)]">
                    <ul className="p-2 text-sm">
                      <li>
                        <Link
                          to="/settings#account"
                          onClick={() => setProfileMenuOpen(false)}
                          className="inline-flex w-full items-center gap-2 rounded-md px-3 py-2 text-left hover:bg-secondary"
                        >
                          <Settings className="h-4 w-4 text-muted-foreground" />
                          Settings
                        </Link>
                      </li>
                      <li className="mt-1">
                        <button
                          type="button"
                          onClick={toggleTheme}
                          className="inline-flex w-full items-center justify-between rounded-md px-3 py-2 text-left hover:bg-secondary"
                        >
                          <span className="inline-flex items-center gap-2">
                            {theme === "dark" ? <Moon className="h-4 w-4 text-muted-foreground" /> : <Sun className="h-4 w-4 text-muted-foreground" />}
                            Appearance
                          </span>
                          <span
                            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                              theme === "dark" ? "bg-emerald-500" : "bg-slate-300"
                            }`}
                            aria-hidden
                          >
                            <span
                              className={`inline-block h-5 w-5 transform rounded-full bg-card transition-transform ${
                                theme === "dark" ? "translate-x-5" : "translate-x-1"
                              }`}
                            />
                          </span>
                        </button>
                      </li>
                      <li className="mt-1 border-t border-border pt-1">
                        <button
                          type="button"
                          onClick={onLogout}
                          disabled={loggingOut}
                          className="inline-flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-destructive hover:bg-secondary disabled:opacity-60"
                        >
                          <LogOut className="h-4 w-4" />
                          {loggingOut ? "Signing out..." : "Sign out"}
                        </button>
                      </li>
                    </ul>
                  </div>
                ) : null}
                </div>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-3">
                <Link to="/login">
                  <Button variant="ghost" size="lg" className="border border-primary font-semibold text-[0.95rem] text-primary hover:bg-primary/10">Login</Button>
                </Link>
                <Link to="/signup">
                  <Button size="lg" className="text-[0.95rem]">Get started</Button>
                </Link>
              </div>
            </>
          )}
        </nav>

        <button
          type="button"
          onClick={() => setMobileMenuOpen((prev) => !prev)}
          className="inline-flex items-center justify-center rounded-lg border border-border bg-card p-2 text-foreground lg:hidden"
          aria-label="Toggle navigation menu"
        >
          {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {mobileMenuOpen ? (
        <div className="absolute left-0 right-0 top-full z-50 border-b border-black/10 bg-background/95 px-4 py-4 shadow-[0_16px_30px_rgba(15,23,42,0.12)] backdrop-blur lg:hidden">
          <div className="mx-auto flex w-full max-w-7xl flex-col gap-2">
            {user ? (
              <>
                <Link
                  to="/"
                  onClick={() => setMobileMenuOpen(false)}
                  className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-secondary"
                >
                  Portfolio
                </Link>
                <Link
                  to="/#accounts"
                  onClick={() => setMobileMenuOpen(false)}
                  className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-secondary"
                >
                  Accounts
                </Link>
                <Link
                  to="/#asset-types"
                  onClick={() => setMobileMenuOpen(false)}
                  className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-secondary"
                >
                  Asset Types
                </Link>
                <Link
                  to="/?action=add-modify"
                  onClick={() => setMobileMenuOpen(false)}
                  className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-secondary"
                >
                  Add / Modify Assets
                </Link>
                <Link
                  to="/settings#account"
                  onClick={() => setMobileMenuOpen(false)}
                  className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-secondary"
                >
                  Settings
                </Link>
                <button
                  type="button"
                  onClick={onLogout}
                  disabled={loggingOut}
                  className="rounded-md px-3 py-2 text-left text-sm font-medium text-destructive hover:bg-secondary disabled:opacity-60"
                >
                  {loggingOut ? "Signing out..." : "Sign out"}
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/pricing"
                  onClick={() => setMobileMenuOpen(false)}
                  className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-secondary"
                >
                  Pricing
                </Link>
                <Link
                  to="/security"
                  onClick={() => setMobileMenuOpen(false)}
                  className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-secondary"
                >
                  Security
                </Link>
                <Link
                  to="/learn"
                  onClick={() => setMobileMenuOpen(false)}
                  className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-secondary"
                >
                  Learn
                </Link>
                <Link
                  to="/business"
                  onClick={() => setMobileMenuOpen(false)}
                  className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-secondary"
                >
                  Business
                </Link>
                <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                  <Button variant="ghost" className="mt-1 w-full border border-primary font-semibold text-primary hover:bg-primary/10">
                    Login
                  </Button>
                </Link>
                <Link to="/signup" onClick={() => setMobileMenuOpen(false)}>
                  <Button className="w-full">Get started</Button>
                </Link>
              </>
            )}
          </div>
        </div>
      ) : null}
    </header>
  );
}
