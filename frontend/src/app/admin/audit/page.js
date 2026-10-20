"use client";

import { useEffect, useState } from "react";
import { Loader2, Search, History } from "lucide-react";
import EmptyState from "@/components/ui/EmptyState";
import { adminApi } from "@/lib/adminApi";
import { formatDateTime } from "@/lib/utils";

export default function AdminAuditPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [action, setAction] = useState("");
  const [actorId, setActorId] = useState("");
  const [targetId, setTargetId] = useState("");
  const [expanded, setExpanded] = useState(null);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (action.trim()) params.set("action", action.trim());
      if (actorId.trim()) params.set("actor_id", actorId.trim());
      if (targetId.trim()) params.set("target_id", targetId.trim());
      params.set("limit", "300");
      const data = await adminApi.get(`/api/v1/admin/audit?${params.toString()}`);
      setLogs(Array.isArray(data?.items) ? data.items : []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const t = setTimeout(load, 300);
    return () => clearTimeout(t);
  }, [action, actorId, targetId]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-black text-white">Audit log</h1>
        <p className="text-sm text-gray-400 mt-1">
          Every important action, in order.
        </p>
      </div>

      <div className="grid sm:grid-cols-3 gap-3">
        <input
          value={action}
          onChange={(e) => setAction(e.target.value)}
          placeholder="Filter by action (e.g. vendor.updated)"
          className="px-3 py-2.5 rounded-xl bg-surface-card border border-surface-border text-white text-sm focus:border-brand-primary outline-none"
        />
        <input
          value={actorId}
          onChange={(e) => setActorId(e.target.value)}
          placeholder="Filter by actor ID"
          className="px-3 py-2.5 rounded-xl bg-surface-card border border-surface-border text-white text-sm focus:border-brand-primary outline-none"
        />
        <input
          value={targetId}
          onChange={(e) => setTargetId(e.target.value)}
          placeholder="Filter by target ID"
          className="px-3 py-2.5 rounded-xl bg-surface-card border border-surface-border text-white text-sm focus:border-brand-primary outline-none"
        />
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="py-16 text-center">
          <Loader2 className="w-8 h-8 text-brand-primary animate-spin mx-auto" />
        </div>
      ) : logs.length === 0 ? (
        <EmptyState
          icon={History}
          title="No matching logs"
          message="Try a different filter."
        />
      ) : (
        <div className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden">
          <ul className="divide-y divide-surface-border">
            {logs.map((log) => {
              const isOpen = expanded === log.id;
              return (
                <li key={log.id} className="px-5 py-3">
                  <button
                    onClick={() => setExpanded(isOpen ? null : log.id)}
                    className="w-full text-left"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <div className="font-mono text-xs text-brand-primary">
                          {log.action}
                        </div>
                        <div className="text-sm text-white mt-0.5">
                          {log.actor_email || log.actor_id || log.actor_type}
                        </div>
                        <div className="text-[11px] text-gray-500 mt-0.5">
                          {formatDateTime(log.at)}
                          {log.target_type && ` · ${log.target_type}`}
                          {log.target_id && ` ${log.target_id.slice(0, 8)}`}
                        </div>
                      </div>
                      <span className="text-[10px] text-gray-500 uppercase tracking-wider">
                        {isOpen ? "Hide" : "Details"}
                      </span>
                    </div>
                  </button>
                  {isOpen && (
                    <div className="mt-3 pt-3 border-t border-surface-border space-y-2 text-xs">
                      {log.before && (
                        <div>
                          <div className="text-gray-500 mb-1 font-bold">
                            Before
                          </div>
                          <pre className="p-2 rounded-lg bg-surface-dark border border-surface-border text-gray-300 overflow-auto whitespace-pre-wrap break-all">
                            {JSON.stringify(log.before, null, 2)}
                          </pre>
                        </div>
                      )}
                      {log.after && (
                        <div>
                          <div className="text-gray-500 mb-1 font-bold">
                            After
                          </div>
                          <pre className="p-2 rounded-lg bg-surface-dark border border-surface-border text-gray-300 overflow-auto whitespace-pre-wrap break-all">
                            {JSON.stringify(log.after, null, 2)}
                          </pre>
                        </div>
                      )}
                      {log.metadata && (
                        <div>
                          <div className="text-gray-500 mb-1 font-bold">
                            Metadata
                          </div>
                          <pre className="p-2 rounded-lg bg-surface-dark border border-surface-border text-gray-300 overflow-auto whitespace-pre-wrap break-all">
                            {JSON.stringify(log.metadata, null, 2)}
                          </pre>
                        </div>
                      )}
                      {log.ip && (
                        <div className="text-gray-500">
                          IP: <span className="text-gray-300">{log.ip}</span>
                        </div>
                      )}
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}