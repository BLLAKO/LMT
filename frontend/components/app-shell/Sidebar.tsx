"use client";

import Image from "next/image";
import type { Conversation } from "@/lib/types";

export default function Sidebar({
  conversations,
  activeId,
  onSelect,
  onNewSession,
}: {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNewSession: () => void;
}) {
  return (
    <aside className="flex h-screen w-64 shrink-0 flex-col border-r border-border bg-subtle">
      <div className="flex items-center px-4 py-4">
        <Image src="/logo.png" alt="ZeroDelay" width={71} height={20} />
      </div>

      <div className="px-3">
        <button
          onClick={onNewSession}
          className="w-full rounded-lg bg-accent-500 px-3 py-2 text-left text-sm font-medium text-white transition-colors hover:bg-accent-600"
        >
          + New
        </button>
      </div>

      <div className="mt-4 flex-1 overflow-y-auto px-3 pb-4">
        <p className="mb-2 px-1 text-xs font-medium uppercase tracking-wide text-muted">
          Past discussions
        </p>
        {conversations.length === 0 ? (
          <p className="px-1 text-sm text-muted">No discussions yet.</p>
        ) : (
          <div className="space-y-1">
            {conversations.map((c) => (
              <button
                key={c.id}
                onClick={() => onSelect(c.id)}
                className={`w-full rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                  c.id === activeId
                    ? "border border-border-strong bg-card font-medium text-primary"
                    : "text-secondary hover:bg-card/60"
                }`}
              >
                <p className="truncate">{c.title}</p>
                <p className="mt-0.5 text-xs text-muted">{c.updatedAt}</p>
              </button>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}
