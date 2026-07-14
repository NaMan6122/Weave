"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { WeaveClient } from "@/lib/api-client";

const languages = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "de", label: "German" },
  { value: "fr", label: "French" },
  { value: "pt", label: "Portuguese" },
  { value: "it", label: "Italian" },
  { value: "nl", label: "Dutch" },
  { value: "ja", label: "Japanese" },
  { value: "zh", label: "Chinese" },
  { value: "ko", label: "Korean" },
];

export default function AddDomainContent() {
  const router = useRouter();
  const [domain, setDomain] = useState("");
  const [niche, setNiche] = useState("");
  const [language, setLanguage] = useState("en");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      const res = await fetch("/api/auth/session");
      const session = await res.json();
      const token = session?.backendToken;
      if (!token) throw new Error("Not authenticated");

      const client = WeaveClient.authenticated(token);
      const created = await client.createDomain({
        domain,
        niche: niche || undefined,
        language,
      });
      router.push(`/dashboard/domains/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-bold mb-6">Add Domain</h1>

      <form onSubmit={handleSubmit} className="space-y-5">
        {error && (
          <div className="rounded-lg bg-red-900/30 border border-red-800 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-neutral-300 mb-1">
            Domain
          </label>
          <input
            type="text"
            required
            placeholder="example.com"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-neutral-300 mb-1">
            Niche{" "}
            <span className="text-neutral-500 font-normal">(optional)</span>
          </label>
          <input
            type="text"
            placeholder="e.g. technology, health, finance"
            value={niche}
            onChange={(e) => setNiche(e.target.value)}
            className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-neutral-300 mb-1">
            Language
          </label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-white focus:outline-none focus:border-neutral-500"
          >
            {languages.map((l) => (
              <option key={l.value} value={l.value}>
                {l.label}
              </option>
            ))}
          </select>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="rounded-lg bg-white text-black px-4 py-2 text-sm font-medium hover:bg-neutral-200 disabled:opacity-50"
        >
          {submitting ? "Adding..." : "Add Domain"}
        </button>

        <p className="text-sm text-neutral-500 mt-4">
          After adding, you&apos;ll need to verify ownership using DNS, meta
          tag, or file upload.
        </p>
      </form>
    </div>
  );
}
