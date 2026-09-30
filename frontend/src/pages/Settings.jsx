import { useEffect, useState } from "react";
import { toast } from "sonner";
import { ShieldCheck, Bell, Send, Link2 } from "lucide-react";
import api from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { PageHeader, Card } from "../components/Primitives";

const KOTAK_STATUS_LABEL = (s) => ({
  NOT_CONFIGURED: "NOT CONFIGURED", CONNECTED: "CONNECTED", AUTH_FAILED: "AUTH FAILED",
  DISCONNECTED: "DISCONNECTED", TIMEOUT: "TIMEOUT", RATE_LIMITED: "RATE LIMITED", ERROR: "ERROR",
}[s] || "NOT CONFIGURED");

const KOTAK_STATUS_STYLE = (s) => ({
  CONNECTED: "border-emerald-500/40 bg-emerald-500/10 text-emerald-400",
  NOT_CONFIGURED: "border-slate-600 bg-slate-800 text-slate-400",
  AUTH_FAILED: "border-rose-500/40 bg-rose-500/10 text-rose-400",
  DISCONNECTED: "border-amber-500/40 bg-amber-500/10 text-amber-400",
}[s] || "border-slate-600 bg-slate-800 text-slate-400");

export default function Settings() {
  const { user } = useAuth();
  const [s, setS] = useState(null);
  const [status, setStatus] = useState(null);
  const [kotak, setKotak] = useState(null);
  const [testing, setTesting] = useState(false);
  const [notif, setNotif] = useState(null);
  const [testingTg, setTestingTg] = useState(false);

  const loadKotak = () => api.get("/broker/kotak/status").then((r) => setKotak(r.data)).catch(() => {});

  useEffect(() => {
    api.get("/settings").then((r) => setS(r.data)).catch(() => {});
    api.get("/system/status").then((r) => setStatus(r.data)).catch(() => {});
    api.get("/notifications/settings").then((r) => setNotif(r.data)).catch(() => {});
    loadKotak();
  }, []);

  const testConnection = async () => {
    setTesting(true);
    try {
      const { data } = await api.post("/broker/kotak/test-connection");
      if (data.connected) toast.success(data.message || "Connected");
      else toast.error(data.message || `Status: ${data.status}`);
      loadKotak();
    } catch {
      toast.error("Test connection failed");
    } finally {
      setTesting(false);
    }
  };

  const testTelegram = async () => {
    setTestingTg(true);
    try {
      const { data } = await api.post("/notifications/telegram/test", { telegram_chat_id: notif?.telegram_chat_id });
      if (data.sent) toast.success(data.message);
      else toast.error(data.message);
    } catch {
      toast.error("Telegram test failed");
    } finally {
      setTestingTg(false);
    }
  };

  const save = async () => {
    try {
      const { data } = await api.put("/settings", s);
      setS(data);
      if (notif) {
        const { telegram_bot_configured, ...payload } = notif;
        await api.put("/notifications/settings", payload);
      }
      toast.success("Settings saved");
    } catch {
      toast.error("Save failed");
    }
  };

  if (!s) return <div className="py-20 text-center text-sm text-slate-500">Loading…</div>;
  const input = "w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm outline-none focus:border-blue-500";

  return (
    <div>
      <PageHeader title="Settings" subtitle="Profile, risk, notifications & broker connection" />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <div className="mb-3 flex items-center gap-2"><ShieldCheck size={16} className="text-blue-400" /><h2 className="font-display text-lg font-bold">Profile</h2></div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between border-b border-slate-800 py-2"><span className="text-slate-400">Name</span><span>{user?.name}</span></div>
            <div className="flex justify-between border-b border-slate-800 py-2"><span className="text-slate-400">Email</span><span>{user?.email}</span></div>
            <div className="flex justify-between py-2"><span className="text-slate-400">Role</span><span className="uppercase">{user?.role}</span></div>
          </div>
        </Card>

        <Card>
          <div className="mb-3 flex items-center gap-2"><span className="text-lg">⚖️</span><h2 className="font-display text-lg font-bold">Risk Preferences</h2></div>
          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-[10px] uppercase tracking-wider text-slate-500">Max Risk % per trade</label>
              <input type="number" step="0.1" value={s.max_risk_pct} onChange={(e) => setS({ ...s, max_risk_pct: Number(e.target.value) })} className={input} data-testid="settings-risk-input" />
            </div>
            <div>
              <label className="mb-1 block text-[10px] uppercase tracking-wider text-slate-500">Stop Buffer %</label>
              <input type="number" step="0.1" value={s.stop_buffer_pct} onChange={(e) => setS({ ...s, stop_buffer_pct: Number(e.target.value) })} className={input} />
            </div>
            <div>
              <label className="mb-1 block text-[10px] uppercase tracking-wider text-slate-500">Max Open Positions</label>
              <input type="number" value={s.max_open_positions} onChange={(e) => setS({ ...s, max_open_positions: Number(e.target.value) })} className={input} />
            </div>
          </div>
        </Card>

        <Card>
          <div className="mb-3 flex items-center gap-2"><Bell size={16} className="text-amber-400" /><h2 className="font-display text-lg font-bold">Notifications</h2></div>
          <label className="flex items-center justify-between py-2 text-sm">
            <span className="text-slate-300">In-app notifications</span>
            <input type="checkbox" checked={s.in_app_notifications} onChange={(e) => setS({ ...s, in_app_notifications: e.target.checked })} className="h-4 w-4 accent-blue-500" data-testid="notif-inapp-toggle" />
          </label>

          {notif && !notif.telegram_bot_configured && (
            <div className="my-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[11px] text-amber-400" data-testid="telegram-not-configured">
              Telegram bot is not configured on this server.
            </div>
          )}

          <label className="flex items-center justify-between py-2 text-sm">
            <span className="flex items-center gap-2 text-slate-300"><Send size={14} /> Telegram notifications</span>
            <input type="checkbox" checked={notif?.telegram_enabled || false} onChange={(e) => setNotif({ ...notif, telegram_enabled: e.target.checked })} className="h-4 w-4 accent-blue-500" data-testid="settings-telegram-toggle" />
          </label>

          {notif?.telegram_enabled && (
            <>
              <input placeholder="Telegram Chat ID" value={notif.telegram_chat_id || ""} onChange={(e) => setNotif({ ...notif, telegram_chat_id: e.target.value })} className={`${input} mt-1`} data-testid="telegram-chatid-input" />
              <button onClick={testTelegram} disabled={testingTg || !notif.telegram_bot_configured} data-testid="telegram-test-button"
                className="mt-2 w-full rounded-lg border border-amber-500/30 bg-amber-500/10 py-2 text-xs font-semibold text-amber-400 hover:bg-amber-500/20 disabled:opacity-50">
                {testingTg ? "Sending…" : "Test Telegram Notification"}
              </button>

              <div className="mt-3 space-y-1 border-t border-slate-800 pt-3">
                {[
                  ["alert_entry", "Entry Alert"], ["alert_stop", "Stop Loss Alert"], ["alert_target", "Target Alert"],
                  ["alert_trailing", "Trailing Stop Alert"], ["alert_regime", "Market Regime Alert"], ["daily_summary", "Daily Summary"],
                ].map(([key, label]) => (
                  <label key={key} className="flex items-center justify-between py-1.5 text-sm">
                    <span className="text-slate-400">{label}</span>
                    <input type="checkbox" checked={notif[key]} onChange={(e) => setNotif({ ...notif, [key]: e.target.checked })} className="h-4 w-4 accent-blue-500" data-testid={`notif-${key.replace("_", "-")}-toggle`} />
                  </label>
                ))}
              </div>
            </>
          )}
          <p className="mt-2 text-[11px] text-slate-600">The Telegram bot token is stored server-side only and is never exposed here.</p>
        </Card>

        <Card>
          <div className="mb-3 flex items-center gap-2"><Link2 size={16} className="text-cyan-400" /><h2 className="font-display text-lg font-bold">Broker Connection</h2></div>
          <div className="rounded-lg bg-slate-900/60 p-3" data-testid="kotak-connection-panel">
            <div className="flex items-center justify-between">
              <span className="font-semibold">Kotak Neo <span className="ml-1 text-[10px] uppercase tracking-wider text-slate-500">read-only</span></span>
              <span className={`rounded-md border px-2 py-0.5 text-[10px] font-semibold ${KOTAK_STATUS_STYLE(kotak?.status)}`} data-testid="kotak-status-badge">
                {KOTAK_STATUS_LABEL(kotak?.status)}
              </span>
            </div>
            <div className="mt-3 space-y-1.5 text-[11px] text-slate-500">
              <div className="flex justify-between"><span>Last successful connection</span><span className="font-num text-slate-400">{kotak?.last_connection ? new Date(kotak.last_connection).toLocaleString() : "—"}</span></div>
              <div className="flex justify-between"><span>Last error</span><span className="font-num text-slate-400">{kotak?.last_error || "—"}</span></div>
              <div className="flex justify-between"><span>Last data received</span><span className="font-num text-slate-400">{kotak?.last_data_received ? new Date(kotak.last_data_received).toLocaleString() : "—"}</span></div>
              <div className="flex justify-between"><span>Order execution</span><span className="font-num text-rose-400">disabled</span></div>
            </div>
            <button
              onClick={testConnection} disabled={testing} data-testid="kotak-test-connection-button"
              className="mt-3 w-full rounded-lg border border-cyan-500/30 bg-cyan-500/10 py-2 text-xs font-semibold text-cyan-400 hover:bg-cyan-500/20 disabled:opacity-60"
            >
              {testing ? "Testing…" : "Test Connection"}
            </button>
            <p className="mt-2 text-[11px] text-slate-600">Read-only adapter — MarketPilot never places trades. Credentials are stored server-side via environment variables and never exposed here. When not configured the app runs on demo market data.</p>
          </div>
        </Card>
      </div>

      <button onClick={save} className="mt-6 rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-blue-500" data-testid="settings-save-button">Save Settings</button>
    </div>
  );
}
