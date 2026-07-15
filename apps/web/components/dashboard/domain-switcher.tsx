"use client";

import { useDomainContext } from "@/lib/domain-context";

function drColor(dr: number): string {
  if (dr >= 50) return "bg-green-900/50 text-green-300";
  if (dr >= 20) return "bg-yellow-900/50 text-yellow-300";
  return "bg-red-900/50 text-red-300";
}

export function DomainSwitcher() {
  const { domains, selectedDomainId, selectDomain, loading } = useDomainContext();

  if (loading) {
    return (
      <div className="mb-4 px-1">
        <div className="h-8 rounded-lg bg-neutral-900 animate-pulse" />
      </div>
    );
  }

  if (domains.length === 0) {
    return (
      <div className="mb-4 px-1">
        <p className="text-xs text-neutral-500 mb-2">No domains yet</p>
        <a
          href="/dashboard/domains/add"
          className="text-sm text-neutral-400 hover:text-white transition"
        >
          + Add Domain
        </a>
      </div>
    );
  }

  return (
    <div className="mb-4">
      <p className="text-xs font-medium text-neutral-500 uppercase tracking-wider mb-2 px-1">
        Domains
      </p>
      <div className="flex flex-col gap-0.5">
        {domains.map((domain) => (
          <button
            key={domain.id}
            onClick={() => selectDomain(domain.id)}
            className={`flex items-center justify-between px-2 py-1.5 rounded-md text-left text-sm transition ${
              domain.id === selectedDomainId
                ? "bg-neutral-800 text-white"
                : "text-neutral-400 hover:bg-neutral-800/50 hover:text-neutral-200"
            }`}
          >
            <span className="truncate font-mono text-xs">{domain.domain}</span>
            {domain.dr != null && (
              <span className={`ml-2 shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-bold ${drColor(domain.dr)}`}>
                {Math.round(domain.dr)}
              </span>
            )}
          </button>
        ))}
        <a
          href="/dashboard/domains/add"
          className="px-2 py-1.5 text-xs text-neutral-500 hover:text-neutral-300 transition"
        >
          + Add Domain
        </a>
      </div>
    </div>
  );
}
