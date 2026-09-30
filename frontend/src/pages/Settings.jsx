import { useEffect, useState } from "react";
import { toast } from "sonner";
import { ShieldCheck, Bell, Send, Link2 } from "lucide-react";
import api from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { PageHeader, Card } from "../components/Primitives";

export default function Settings() {
  const { user } = useAuth();
  const [s, setS] = useState(null);
  const [status, setStatus] = useState(null);

  useEffect(() => {
    api.get("/settings").then((r) => setS(r.data)).catch(() => {});
    api.get("/system/status").then((r) => setStatus(r.data)).catch(() => {});
  }, []);

  const save = async () => {
    try { const { data } = await api.put("/settings", s); setS(data); toast.success("Settings saved"); }
    catch { toast.error("Save failed"); }
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
            <input type="checkbox" checked={s.in_app_notifications} onChange={(e) => setS({ ...s, in_app_notifications: e.target.checked })} className="h-4 w-4 accent-blue-500" />
          </label>
          <label className="flex items-center justify-between py-2 text-sm">
            <span className="flex items-center gap-2 text-slate-300"><Send size={14} /> Telegram alerts</span>
            <input type="checkbox" checked={s.telegram_enabled} onChange={(e) => setS({ ...s, telegram_enabled: e.target.checked })} className="h-4 w-4 accent-blue-500" data-testid="settings-telegram-toggle" />
          </label>
          {s.telegram_enabled && (
            <input placeholder="Telegram Chat ID" value={s.telegram_chat_id || ""} onChange={(e) => setS({ ...s, telegram_chat_id: e.target.value })} className={`${input} mt-2`} />
          )}
          <p className="mt-2 text-[11px] text-slate-600">Telegram sending is config-ready in V1; delivery activates in a later milestone.</p>
        </Card>

        <Card>
          <div className="mb-3 flex items-center gap-2"><Link2 size={16} className="text-cyan-400" /><h2 className="font-display text-lg font-bold">Broker Connection</h2></div>
          <div className="rounded-lg bg-slate-900/60 p-3">
            <div className="flex items-center justify-between">
              <span className="font-semibold">Kotak Neo</span>
              <span className="rounded-md border border-slate-600 bg-slate-800 px-2 py-0.5 text-[10px] text-slate-400">
                {status?.broker?.configured ? "Configured" : "Not connected"}
              </span>
            </div>
            <p className="mt-2 text-[11px] text-slate-500">Read-only adapter. Order execution is disabled — MarketPilot never places trades. Credentials are stored server-side via environment variables and never exposed here.</p>
          </div>
        </Card>
      </div>

      <button onClick={save} className="mt-6 rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-blue-500" data-testid="settings-save-button">Save Settings</button>
    </div>
  );
}
