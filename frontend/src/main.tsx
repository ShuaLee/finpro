import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./App";
import { ensureCsrfToken } from "./api/http";
import { AuthProvider } from "./context/AuthContext";
import "./index.css";

void ensureCsrfToken().catch(() => {
  // Non-blocking during boot; individual requests still surface errors.
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
);
