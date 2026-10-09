import { NavLink, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import {
  LayoutDashboard, TrendingUp, Lightbulb, Activity, BookOpen, Globe,
  Settings, Zap, LogOut, Bell, Menu, X,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";
import { fmtPct, regimeStyle } from "../lib/format";
import { Badge } from "./ui/badge";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, id: "dashboard" },
  { to: "/equity", label: "Equity Research", icon: TrendingUp, id: "equity" },
  { to: "/ideas", label: "Trade Ideas", icon: Lightbulb, id: "ideas" },
  { to: "/monitoring", label: "My Monitoring", icon: Activity, id: "monitoring" },
  { to: "/journal", label: "Trade Journal", icon: BookOpen, id: "journal" },
  { to: "/market-overview", label: "Market Overview", icon: Globe, id: "overview" },
  { to: "/settings", label: "Settings", icon: Settings, id: "settings" },
];

export function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [overview, setOverview] = useState(null);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    api.get("/market/overview").then((r) => setOverview(r.data)).catch(() => {});
    api.get("/alerts").then((r) => setAlerts(r.data.alerts || [])).catch(() => {});
  }, []);

  const doLogout = async () => {
    await logout();
    navigate("/login");
  };

  const regime = overview?.regime?.regime || "NEUTRAL";
  const unread = alerts.filter((a) => !a.read).length;

  return (
    <div className="min-h-screen bg-[#0B0F17] text-slate-100">
      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 border-r border-slate-800 bg-[#0B0F17] transition-transform duration-200 lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
        data-testid="sidebar"
      >
        <div className="flex h-16 items-center gap-2 border-b border-slate-800 px-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-blue-600">
            <TrendingUp className="h-5 w-5 text-white" />
          </div>
          <span className="font-display text-lg font-extrabold tracking-tight">MarketPilot</span>
        </div>
        <nav className="flex flex-col gap-1 p-3">
          {NAV.map((n) => (
            <NavLink
              key={n.id}
              to={n.to}
              end={n.to === "/"}
              onClick={() => setOpen(false)}
              data-testid={`nav-${n.id}-link`}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive ? "bg-blue-600/15 text-blue-400" : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-100"
                }`
              }
            >
              <n.icon className="h-4.5 w-4.5" style={{ width: 18, height: 18 }} />
              {n.label}
            </NavLink>
          ))}
          {/* F&O Coming Soon */}
          <NavLink
            to="/fo"
            onClick={() => setOpen(false)}
            data-testid="nav-fo-link"
            className="mt-1 flex items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium text-slate-500 hover:bg-slate-800/40"
          >
            <span className="flex items-center gap-3">
              <Zap style={{ width: 18, height: 18 }} />
              F&amp;O
            </span>
            <Badge className="border-amber-500/30 bg-amber-500/10 text-[10px] text-amber-400">SOON</Badge>
          </NavLink>
        </nav>
        <div className="absolute bottom-0 w-full border-t border-slate-800 p-3">
          <div className="mb-2 rounded-lg bg-slate-900/60 px-3 py-2">
            <div className="truncate text-xs text-slate-400" data-testid="sidebar-user-email">{user?.email}</div>
            <div className="text-[11px] uppercase tracking-wider text-slate-600">{user?.role}</div>
          </div>
          <button
            onClick={doLogout}
            data-testid="logout-button"
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-400 hover:bg-slate-800 hover:text-rose-400"
          >
            <LogOut style={{ width: 16, height: 16 }} /> Sign out
          </button>
        </div>
      </aside>

      {open && <div className="fixed inset-0 z-30 bg-black/50 lg:hidden" onClick={() => setOpen(false)} />}

      {/* Main */}
      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-800 bg-[#0B0F17]/80 px-4 backdrop-blur-md sm:px-6">
          <div className="flex items-center gap-3">
            <button className="lg:hidden" onClick={() => setOpen(!open)} data-testid="menu-toggle">
              {open ? <X /> : <Menu />}
            </button>
            {overview && (
              <div className="hidden items-center gap-3 sm:flex">
                <Badge className={`border ${regimeStyle(regime)} font-num text-xs`} data-testid="header-regime-badge">
                  NIFTY {regime}
                </Badge>
                <div className="font-num text-sm">
                  <span className="text-slate-400">NIFTY </span>
                  <span className="font-semibold text-slate-100">{overview.nifty.value.toLocaleString("en-IN")}</span>
                  <span className={overview.nifty.change_pct >= 0 ? "ml-1 text-emerald-400" : "ml-1 text-rose-400"}>
                    {fmtPct(overview.nifty.change_pct)}
                  </span>
                </div>
              </div>
            )}
          </div>
          <NavLink to="/monitoring" className="relative" data-testid="header-alerts-button">
            <Bell className="text-slate-400 hover:text-slate-100" style={{ width: 20, height: 20 }} />
            {unread > 0 && (
              <span className="absolute -right-1.5 -top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white">
                {unread}
              </span>
            )}
          </NavLink>
        </header>
        <main className="mx-auto max-w-[1400px] p-4 sm:p-6">{children}</main>
      </div>
    </div>
  );
}
