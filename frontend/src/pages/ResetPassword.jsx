import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Loader2 } from "lucide-react";
import api, { formatApiErrorDetail } from "../lib/api";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/auth/reset-password", { token, password });
      navigate("/login");
    } catch (err) {
      setError(formatApiErrorDetail(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mp-grid-bg flex min-h-screen items-center justify-center bg-[#0B0F17] px-4">
      <div className="mp-fade-up w-full max-w-md rounded-2xl border border-slate-800 bg-[#111827] p-8 shadow-2xl">
        <h1 className="font-display text-2xl font-bold">Set a new password</h1>
        <form onSubmit={submit} className="mt-6 space-y-4">
          <input
            type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} data-testid="reset-password-input"
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
            placeholder="New password (min 8 chars)"
          />
          {error && <div className="rounded-lg bg-rose-500/10 px-3 py-2 text-sm text-rose-400">{error}</div>}
          <button
            type="submit" disabled={loading || !token} data-testid="reset-submit-button"
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-60"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />} Reset password
          </button>
          {!token && <p className="text-xs text-rose-400">Missing or invalid reset token.</p>}
        </form>
        <div className="mt-4 text-center text-xs">
          <Link to="/login" className="text-slate-400 hover:text-blue-400">Back to sign in</Link>
        </div>
      </div>
    </div>
  );
}
