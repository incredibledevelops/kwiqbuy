export default function Badge({ children, color = "gray", className = "" }) {
  const colors = {
    gray: "bg-white/5 text-gray-300 border-white/10",
    blue: "bg-blue-500/10 text-blue-400 border-blue-500/30",
    green: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    amber: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    red: "bg-red-500/10 text-red-400 border-red-500/30",
    purple: "bg-brand-accent/10 text-brand-accent border-brand-accent/30",
  };
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-[10px] font-bold uppercase tracking-wide ${
        colors[color] || colors.gray
      } ${className}`}
    >
      {children}
    </span>
  );
}