import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import { Footer } from "./components/Footer";
import { Header } from "./components/Header";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { useAuth } from "./context/AuthContext";
import { AppHomePage } from "./pages/AppHomePage";
import { AddBrokerageAccountPage } from "./pages/AddBrokerageAccountPage";
import { AboutPage } from "./pages/AboutPage";
import { BusinessPage } from "./pages/BusinessPage";
import { ContactPage } from "./pages/ContactPage";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { LandingPage } from "./pages/LandingPage";
import { LearnPage } from "./pages/LearnPage";
import { LoginPage } from "./pages/LoginPage";
import { HoldingsPage } from "./pages/HoldingsPage";
import { PricingPage } from "./pages/PricingPage";
import { PrivacyPage } from "./pages/PrivacyPage";
import { ResetPasswordPage } from "./pages/ResetPasswordPage";
import { SecurityPage } from "./pages/SecurityPage";
import { SignupPage } from "./pages/SignupPage";
import { TermsPage } from "./pages/TermsPage";
import { VerifyEmailPage } from "./pages/VerifyEmailPage";

function RootRedirect() {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="grid min-h-[70vh] place-items-center text-sm text-muted-foreground">Loading...</div>;
  }

  if (user) {
    return <AppHomePage />;
  }

  return <LandingPage />;
}

function App() {
  const location = useLocation();
  const { user } = useAuth();
  const authStandalonePaths = new Set(["/signup", "/login", "/login-verify", "/forgot-password", "/reset-password"]);
  const hideHeader = authStandalonePaths.has(location.pathname) || (Boolean(user) && location.pathname === "/");
  const hideFooter = authStandalonePaths.has(location.pathname) || Boolean(user);

  return (
    <div className="min-h-screen flex flex-col">
      {hideHeader ? null : <Header />}
      <div className="flex-1">
        <Routes>
          <Route path="/" element={<RootRedirect />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/login-verify" element={<Navigate to="/login" replace />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/business" element={<BusinessPage />} />
          <Route path="/contact" element={<ContactPage />} />
          <Route path="/learn" element={<LearnPage />} />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="/terms" element={<TermsPage />} />
          <Route path="/pricing" element={<PricingPage />} />
          <Route path="/security" element={<SecurityPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/verify-email" element={<VerifyEmailPage />} />
          <Route
            path="/settings"
            element={(
              <ProtectedRoute>
                <AppHomePage />
              </ProtectedRoute>
            )}
          />
          <Route
            path="/accounts/brokerage/new"
            element={(
              <ProtectedRoute>
                <AddBrokerageAccountPage />
              </ProtectedRoute>
            )}
          />
          <Route
            path="/holdings"
            element={(
              <ProtectedRoute>
                <HoldingsPage />
              </ProtectedRoute>
            )}
          />
          <Route path="/app" element={<Navigate to="/" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
      {hideFooter ? null : <Footer />}
    </div>
  );
}

export default App;
