"use client";

import { WeaveClient } from "@/lib/api-client";

export function ExportButton({ endpoint, label, token, plan }: {
  endpoint: string;
  label: string;
  token: string;
  plan: string;
}) {
  const isPro = plan === "pro" || plan === "agency";

  async function handleExport() {
    if (!isPro) {
      window.location.href = "/pricing";
      return;
    }
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${endpoint}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) {
        if (res.status === 403) {
          window.location.href = "/pricing";
          return;
        }
        throw new Error("Export failed");
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const disposition = res.headers.get("Content-Disposition") || "";
      const filename = disposition.split("filename=")[1]?.replace(/"/g, "") || "export.csv";
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // silent
    }
  }

  return (
    <button
      onClick={handleExport}
      className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition ${
        isPro
          ? "border-neutral-700 text-neutral-300 hover:bg-neutral-800"
          : "border-neutral-800 text-neutral-500 hover:text-neutral-300"
      }`}
    >
      {isPro ? label : "Upgrade to export"}
    </button>
  );
}
