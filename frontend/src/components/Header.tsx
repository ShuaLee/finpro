import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { CircleUserRound, LogOut, Settings, SlidersHorizontal } from "lucide-react";

import { ApiError } from "../api/http";
import { useAuth } from "../context/AuthContext";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";

export function Header() {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (!menuRef.current) {
        return;
      }
      if (event.target instanceof Node && !menuRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    };

    if (menuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [menuOpen]);

  const onLogout = async () => {
    setLoggingOut(true);
    try {
      await logout();
      setMenuOpen(false);
    } catch (caught) {
      if (caught instanceof ApiError) {
        // no-op
      }
    } finally {
      setLoggingOut(false);
    }
  };

  return (
    <header className="sticky top-0 z-40 px-4 pb-2 pt-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl rounded-2xl border border-black/10 bg-white/90 px-4 py-3 shadow-[0_14px_34px_rgba(15,23,42,0.08)] backdrop-blur sm:px-5">
        <div className="flex w-full items-center justify-between gap-3">
          <Link to="/" className="group inline-flex items-center gap-3">
            <span className="h-3 w-3 rounded-full bg-primary shadow-[0_0_0_8px_rgba(15,23,42,0.12)]" />
            <span className="font-display text-xl font-bold tracking-tight">FinPro</span>
            <Badge variant="secondary" className="hidden rounded-full sm:inline-flex">Beta</Badge>
          </Link>

          <nav className="flex items-center gap-2" aria-label="Primary">
            {user ? (
              <div className="relative" ref={menuRef}>
                <button
                  type="button"
                  onClick={() => setMenuOpen((prev) => !prev)}
                  className="inline-flex items-center justify-center rounded-full border border-border bg-secondary p-2 hover:bg-accent"
                  aria-label="Open profile menu"
                >
                  <CircleUserRound className="h-5 w-5 text-primary" />
                </button>

                {menuOpen ? (
                  <div className="absolute right-0 mt-2 w-56 overflow-hidden rounded-xl border border-border bg-white shadow-[0_16px_34px_rgba(15,23,42,0.14)]">
                    <ul className="p-2 text-sm">
                      <li>
                        <button type="button" className="inline-flex w-full items-center gap-2 rounded-md px-3 py-2 text-left hover:bg-secondary">
                          <Settings className="h-4 w-4 text-muted-foreground" />
                          Settings
                        </button>
                      </li>
                      <li>
                        <button type="button" className="inline-flex w-full items-center gap-2 rounded-md px-3 py-2 text-left hover:bg-secondary">
                          <SlidersHorizontal className="h-4 w-4 text-muted-foreground" />
                          Preferences
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
            ) : (
              <>
                <Link to="/login">
                  <Button variant="ghost">Login</Button>
                </Link>
                <Link to="/signup">
                  <Button>Sign up</Button>
                </Link>
              </>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
}
