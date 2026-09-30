import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Layout } from "./components/Layout";

import Login from "./pages/Login";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import Dashboard from "./pages/Dashboard";
import Equity from "./pages/Equity";
import EquityDetail from "./pages/EquityDetail";
import TradeIdeas from "./pages/TradeIdeas";
import Monitoring from "./pages/Monitoring";
import Journal from "./pages/Journal";
import MarketOverview from "./pages/MarketOverview";
import Settings from "./pages/Settings";
import FnoComingSoon from "./pages/FnoComingSoon";

const withLayout = (el) => (
  <ProtectedRoute>
    <Layout>{el}</Layout>
  </ProtectedRoute>
);

function App() {
  return (
    <AuthProvider>
      <Toaster position="top-right" theme="dark" richColors />
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/" element={withLayout(<Dashboard />)} />
          <Route path="/equity" element={withLayout(<Equity />)} />
          <Route path="/equity/:symbol" element={withLayout(<EquityDetail />)} />
          <Route path="/ideas" element={withLayout(<TradeIdeas />)} />
          <Route path="/monitoring" element={withLayout(<Monitoring />)} />
          <Route path="/journal" element={withLayout(<Journal />)} />
          <Route path="/market-overview" element={withLayout(<MarketOverview />)} />
          <Route path="/settings" element={withLayout(<Settings />)} />
          <Route path="/fo" element={withLayout(<FnoComingSoon />)} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
