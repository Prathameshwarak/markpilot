import { useState } from "react";
import { Link } from "react-router-dom";
import { Loader2 } from "lucide-react";
import api, { formatApiErrorDetail } from "../lib/api";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/auth/forgot-password", { email });
      setDone(true);
    } catch (err) {
      setError(formatApiErrorDetail(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mp-grid-bg flex min-h-screen items-center justify-center bg-[#0B0F17] px-4">
      <div className="mp-fade-up w-full max-w-md rounded-2xl border border-slate-800 bg-[#111827] p-8 shadow-2xl">
        <h1 className="font-display text-2xl font-bold">Reset password</h1>
        {done ? (
          <p className="mt-4 rounded-lg bg-slate-800/60 px-4 py-3 text-sm text-slate-300" data-testid="forgot-confirmation">
            If that email is registered, a reset link has been sent. Check your inbox.
          </p>
        ) : (
          <form onSubmit={submit} className="mt-6 space-y-4">
            <p className="text-sm text-slate-400">Enter your email and we'll send a reset link.</p>
            <input
              type="email" required value={email} onChange={(e) => setEmail(e.target.value)} data-testid="forgot-email-input"
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
              placeholder="you@example.com"
            />
            {error && <div className="rounded-lg bg-rose-500/10 px-3 py-2 text-sm text-rose-400">{error}</div>}
            <button
              type="submit" disabled={loading} data-testid="forgot-submit-button"
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-60"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />} Send reset link
            </button>
          </form>
        )}
        <div className="mt-4 text-center text-xs">
          <Link to="/login" className="text-slate-400 hover:text-blue-400" data-testid="back-to-signin-link">Back to sign in</Link>
        </div>
      </div>
    </div>
  );
}
