"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { WeaveClient } from "@/lib/api-client";

export function VerifyButtons({
  domainId,
  method,
}: {
  domainId: string;
  method: "dns" | "meta" | "file";
}) {
  const router = useRouter();
  const [verifying, setVerifying] = useState(false);
  const [error, setError] = useState("");

  async function handleVerify() {
    setVerifying(true);
    setError("");
    try {
      const res = await fetch("/api/auth/session");
      const session = await res.json();
      const token = session?.backendToken;
      if (!token) throw new Error("Not authenticated");

      const client = WeaveClient.authenticated(token);
      await client.verifyDomain(domainId, method);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed");
    } finally {
      setVerifying(false);
    }
  }

  return (
    <div className="flex items-center gap-2">
      {error && <span className="text-xs text-red-400">{error}</span>}
      <button
        onClick={handleVerify}
        disabled={verifying}
        className="rounded-lg border border-neutral-700 px-3 py-1.5 text-xs font-medium hover:bg-neutral-800 disabled:opacity-50"
      >
        {verifying ? "Verifying..." : "Verify"}
      </button>
    </div>
  );
}
