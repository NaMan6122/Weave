"use client";

import { useState, useEffect } from "react";
import { WeaveClient } from "@/lib/api-client";

export default function ApiKeysContent() {
  const [hasKey, setHasKey] = useState(false);
  const [maskedKey, setMaskedKey] = useState("");
  const [rawKey, setRawKey] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [revoking, setRevoking] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  async function getClient() {
    const res = await fetch("/api/auth/session");
    const session = await res.json();
    const token = session?.backendToken;
    if (!token) throw new Error("Not authenticated");
    return WeaveClient.authenticated(token);
  }

  useEffect(() => {
    (async () => {
      try {
        const client = await getClient();
        const info = await client.getApiKeyInfo();
        setHasKey(info.has_key);
        setMaskedKey(info.masked_key || "");
      } catch {
        // API not available
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function handleGenerate() {
    setGenerating(true);
    setError("");
    try {
      const client = await getClient();
      const result = await client.generateApiKey();
      setRawKey(result.key);
      setHasKey(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate key");
    } finally {
      setGenerating(false);
    }
  }

  async function handleRevoke() {
    setRevoking(true);
    setError("");
    try {
      const client = await getClient();
      await client.revokeApiKey();
      setHasKey(false);
      setMaskedKey("");
      setRawKey(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to revoke key");
    } finally {
      setRevoking(false);
    }
  }

  async function handleCopy() {
    if (rawKey) {
      await navigator.clipboard.writeText(rawKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  if (loading) {
    return (
      <div className="text-center py-12 text-neutral-500">Loading...</div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">API Keys</h1>
        {!hasKey && (
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="rounded-lg bg-white text-black px-4 py-2 text-sm font-medium hover:bg-neutral-200 disabled:opacity-50"
          >
            {generating ? "Generating..." : "Generate New Key"}
          </button>
        )}
      </div>

      {error && (
        <div className="rounded-lg bg-red-900/30 border border-red-800 px-4 py-3 text-sm text-red-300 mb-6">
          {error}
        </div>
      )}

      {rawKey && (
        <div className="rounded-xl border border-green-800 bg-green-900/20 p-5 mb-6">
          <p className="text-sm text-green-300 font-semibold mb-2">
            Your API key (shown only once):
          </p>
          <div className="flex items-center gap-2">
            <code className="flex-1 bg-neutral-900 border border-neutral-800 rounded-lg px-3 py-2 text-xs text-neutral-300 font-mono break-all">
              {rawKey}
            </code>
            <button
              onClick={handleCopy}
              className="rounded-lg border border-neutral-700 px-3 py-2 text-xs font-medium hover:bg-neutral-800"
            >
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>
        </div>
      )}

      <div className="rounded-xl border border-neutral-800 overflow-hidden mb-6">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-800 text-neutral-400 text-left">
              <th className="px-4 py-3 font-medium">Key</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {!hasKey ? (
              <tr>
                <td
                  colSpan={2}
                  className="px-4 py-8 text-center text-neutral-500"
                >
                  No API keys yet.
                </td>
              </tr>
            ) : (
              <tr className="border-b border-neutral-800 hover:bg-neutral-900">
                <td className="px-4 py-3 font-mono text-xs">
                  {rawKey || maskedKey || "********"}
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={handleRevoke}
                    disabled={revoking}
                    className="text-xs border border-red-800 text-red-400 rounded px-2 py-1 hover:bg-red-900/30 disabled:opacity-50"
                  >
                    {revoking ? "Revoking..." : "Revoke"}
                  </button>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="rounded-xl border border-neutral-800 p-6">
        <h2 className="text-sm font-semibold text-neutral-300 mb-2">
          Using with MCP
        </h2>
        <p className="text-sm text-neutral-400 mb-3">
          Connect Weave to Claude Code using the MCP server:
        </p>
        <pre className="rounded-lg bg-neutral-900 border border-neutral-800 p-3 text-xs text-neutral-300 overflow-x-auto">
          claude mcp add weave -- npx @weave/mcp-server --api-key {rawKey || "YOUR_KEY"}
        </pre>
      </div>
    </div>
  );
}
