import { Inbox } from "lucide-react";

export default function EmptyState({
  icon: Icon = Inbox,
  title,
  message,
  action,
}) {
  return (
    <div className="bg-surface-card border border-surface-border rounded-2xl p-12 text-center">
      <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mx-auto mb-4">
        <Icon className="w-8 h-8 text-gray-600" />
      </div>
      {title && <h3 className="font-bold text-white text-lg">{title}</h3>}
      {message && (
        <p className="text-gray-400 text-sm mt-1 max-w-sm mx-auto">{message}</p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}