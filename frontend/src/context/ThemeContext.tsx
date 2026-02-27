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
    const storedTheme = localStorage.getItem(THEME_STORAGE_KEY);
    const hasStoredTheme = storedTheme === "light" || storedTheme === "dark";
    const initialTheme: Theme = hasStoredTheme ? storedTheme : DEFAULT_THEME;

    setThemeState(initialTheme);
    setSource(hasStoredTheme ? "localStorage" : "default");
    applyTheme(initialTheme);

    if (!hasStoredTheme) {
      localStorage.setItem(THEME_STORAGE_KEY, initialTheme);
    }
  }, []);

  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (event.key !== THEME_STORAGE_KEY) return;
      const nextValue = event.newValue;
      if (nextValue !== "light" && nextValue !== "dark") return;
      setThemeState(nextValue);
      setSource("localStorage");
      applyTheme(nextValue);
    };

    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const setTheme = (nextTheme: Theme) => {
    setThemeState(nextTheme);
    setSource("localStorage");
    applyTheme(nextTheme);
    localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
  };

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark");
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

