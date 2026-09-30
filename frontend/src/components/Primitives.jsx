export function PageHeader({ title, subtitle, right }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="font-display text-2xl font-extrabold tracking-tight sm:text-3xl">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-400">{subtitle}</p>}
      </div>
      {right}
    </div>
  );
}

export function Card({ children, className = "", ...props }) {
  return (
    <div className={`rounded-xl border border-slate-800 bg-[#111827] p-5 ${className}`} {...props}>
      {children}
    </div>
  );
}

export function Empty({ message, testId }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-800 py-16 text-center text-sm text-slate-500" data-testid={testId}>
      {message}
    </div>
  );
}
