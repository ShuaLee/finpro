import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import { ensureCsrfToken } from "./api/http";
import { AuthProvider } from "./context/AuthContext";
import { ThemeProvider } from "./context/ThemeContext";
import "./index.css";

void ensureCsrfToken().catch(() => {
  // Non-blocking during boot; individual requests still surface errors.
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider>
      <AuthProvider>
        <App />
      </AuthProvider>
    </ThemeProvider>
  </StrictMode>,
);
