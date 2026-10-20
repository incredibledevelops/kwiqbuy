export default function StatCard({ label, value, hint, icon: Icon, accent = "primary" }) {
  const accents = {
    primary: "text-brand-primary bg-brand-primary/10 border-brand-primary/20",
    success: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    warning: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    accent: "text-brand-accent bg-brand-accent/10 border-brand-accent/20",
  };
  return (
    <div className="bg-surface-card border border-surface-border rounded-2xl p-5">
      <div className="flex items-start justify-between">
        <div className="text-[10px] uppercase tracking-wider font-bold text-gray-500">
          {label}
        </div>
        {Icon && (
          <div className={`w-9 h-9 rounded-xl border flex items-center justify-center ${accents[accent]}`}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>
      <div className="mt-2 text-2xl font-black text-white">{value}</div>
      {hint && <div className="text-xs text-gray-500 mt-1">{hint}</div>}
    </div>
  );
}