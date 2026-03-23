/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useEffect, useMemo, useState } from "react";

type Theme = "light" | "dark";
type ThemeSource = "localStorage" | "default";

type ThemeContextValue = {
  theme: Theme;
  source: ThemeSource;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
};

const THEME_STORAGE_KEY = "finpro-theme";
const DEFAULT_THEME: Theme = "light";

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

function applyTheme(theme: Theme) {
  document.documentElement.classList.toggle("dark", theme === "dark");
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(DEFAULT_THEME);
  const [source, setSource] = useState<ThemeSource>("default");

  useEffect(() => {
    setThemeState(DEFAULT_THEME);
    setSource("default");
    applyTheme(DEFAULT_THEME);
    localStorage.setItem(THEME_STORAGE_KEY, DEFAULT_THEME);
  }, []);

  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (event.key !== THEME_STORAGE_KEY) return;
      setThemeState(DEFAULT_THEME);
      setSource("default");
      applyTheme(DEFAULT_THEME);
      if (event.newValue !== DEFAULT_THEME) {
        localStorage.setItem(THEME_STORAGE_KEY, DEFAULT_THEME);
      }
    };

    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const setTheme = (nextTheme: Theme) => {
    const forcedTheme = nextTheme === "light" ? "light" : DEFAULT_THEME;
    setThemeState(forcedTheme);
    setSource("default");
    applyTheme(forcedTheme);
    localStorage.setItem(THEME_STORAGE_KEY, forcedTheme);
  };

  const toggleTheme = () => {
    setTheme(DEFAULT_THEME);
  };

  const value = useMemo<ThemeContextValue>(
    () => ({
      theme,
      source,
      setTheme,
      toggleTheme,
    }),
    [theme, source],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
