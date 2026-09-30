import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { TrendingUp, Loader2 } from "lucide-react";
import { useAuth, formatApiErrorDetail } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(formatApiErrorDetail(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mp-grid-bg flex min-h-screen items-center justify-center bg-[#0B0F17] px-4">
      <div className="mp-fade-up w-full max-w-md rounded-2xl border border-slate-800 bg-[#111827] p-8 shadow-2xl">
        <div className="mb-6 flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-blue-600">
            <TrendingUp className="h-5 w-5 text-white" />
          </div>
          <span className="font-display text-xl font-extrabold">MarketPilot</span>
        </div>
        <h1 className="font-display text-2xl font-bold">Sign in</h1>
        <p className="mb-6 mt-1 text-sm text-slate-400">Research-driven Indian equity trade ideas.</p>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-400">Email</label>
            <input
              type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
              data-testid="login-email-input"
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-400">Password</label>
            <input
              type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
              data-testid="login-password-input"
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
              placeholder="••••••••"
            />
          </div>
          {error && <div className="rounded-lg bg-rose-500/10 px-3 py-2 text-sm text-rose-400" data-testid="login-error">{error}</div>}
          <button
            type="submit" disabled={loading} data-testid="login-submit-button"
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-500 disabled:opacity-60"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />} Sign in
          </button>
        </form>
        <div className="mt-4 flex items-center justify-between text-xs">
          <Link to="/forgot-password" className="text-slate-400 hover:text-blue-400" data-testid="forgot-password-link">
            Forgot password?
          </Link>
          <Link to="/register" className="text-slate-400 hover:text-blue-400" data-testid="register-link">
            Create account
          </Link>
        </div>
      </div>
    </div>
  );
}
