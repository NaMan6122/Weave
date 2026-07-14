import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Documentation",
  description: "Learn how to integrate Weave into your AI workflow via MCP, set up domains, and manage credits.",
};

export default function DocsPage() {
  return (
    <main className="min-h-screen bg-neutral-950 text-white">
      <div className="mx-auto max-w-3xl px-6 py-24">
        <h1 className="text-4xl font-bold mb-4">Documentation</h1>
        <p className="text-neutral-400 mb-12 text-lg">
          Everything you need to integrate Weave into your AI content workflow.
        </p>

        <div className="grid gap-6 sm:grid-cols-2">
          <a href="/docs#getting-started" className="block rounded-xl border border-neutral-800 p-6 hover:border-neutral-600 transition">
            <h2 className="text-lg font-semibold mb-2">Getting Started</h2>
            <p className="text-sm text-neutral-400">
              Set up your account, add your first domain, and verify ownership.
            </p>
          </a>
          <a href="/docs#mcp-integration" className="block rounded-xl border border-neutral-800 p-6 hover:border-neutral-600 transition">
            <h2 className="text-lg font-semibold mb-2">MCP Integration</h2>
            <p className="text-sm text-neutral-400">
              Connect Claude, Cursor, and other MCP-compatible AI tools.
            </p>
          </a>
          <a href="/docs#api-reference" className="block rounded-xl border border-neutral-800 p-6 hover:border-neutral-600 transition">
            <h2 className="text-lg font-semibold mb-2">API Reference</h2>
            <p className="text-sm text-neutral-400">
              Full REST API documentation for programmatic access.
            </p>
          </a>
          <a href="/docs#credit-system" className="block rounded-xl border border-neutral-800 p-6 hover:border-neutral-600 transition">
            <h2 className="text-lg font-semibold mb-2">Credit System</h2>
            <p className="text-sm text-neutral-400">
              Understand how credits are earned, spent, and calculated.
            </p>
          </a>
          <a href="/docs#link-matching" className="block rounded-xl border border-neutral-800 p-6 hover:border-neutral-600 transition">
            <h2 className="text-lg font-semibold mb-2">Link Matching</h2>
            <p className="text-sm text-neutral-400">
              How semantic matching, A-B-C triangulation, and scoring work.
            </p>
          </a>
          <a href="/docs#domain-vetting" className="block rounded-xl border border-neutral-800 p-6 hover:border-neutral-600 transition">
            <h2 className="text-lg font-semibold mb-2">Domain Vetting</h2>
            <p className="text-sm text-neutral-400">
              Understanding the Weave Trust Score and vetting criteria.
            </p>
          </a>
        </div>

        <section id="mcp-integration" className="mt-20">
          <h2 className="text-2xl font-bold mb-6">MCP Integration</h2>
          <p className="text-neutral-400 mb-6">
            Add Weave to your Claude Desktop configuration to start discovering
            and placing backlinks during content creation.
          </p>
          <div className="rounded-xl border border-neutral-800 bg-neutral-900 overflow-hidden">
            <div className="border-b border-neutral-800 px-4 py-3 text-sm text-neutral-400">
              claude_desktop_config.json
            </div>
            <pre className="overflow-x-auto p-6 text-sm text-neutral-300">
              <code>{`{
  "mcpServers": {
    "weave": {
      "command": "npx",
      "args": ["-y", "@anthropic/weave-mcp"],
      "env": {
        "WEAVE_API_KEY": "your-api-key-here"
      }
    }
  }
}`}</code>
            </pre>
          </div>
        </section>

        <section id="credit-system" className="mt-20">
          <h2 className="text-2xl font-bold mb-6">Credit System</h2>
          <p className="text-neutral-400 mb-6">
            Credits are earned by placing outbound links and spent to receive
            inbound links. The formula is transparent and publicly verifiable.
          </p>
          <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-6">
            <h3 className="font-semibold mb-2">Earning Credits</h3>
            <pre className="text-sm text-neutral-400">
credits = 10 &times; (your_DR / 50) &times; (match_score / 100) &times; placement_multiplier
            </pre>
            <p className="text-sm text-neutral-500 mt-2">
              placement_multiplier: body (1.0), sidebar (0.5), footer (0.3)
            </p>
          </div>
          <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-6 mt-4">
            <h3 className="font-semibold mb-2">Spending Credits</h3>
            <pre className="text-sm text-neutral-400">
cost = 10 &times; DR_tier_multiplier

DR 0-20:  &times;0.5    DR 21-40:  &times;1.0
DR 41-60: &times;2.0    DR 61-80:  &times;4.0
DR 81+:   &times;8.0
            </pre>
          </div>
        </section>

        <section id="link-matching" className="mt-20">
          <h2 className="text-2xl font-bold mb-6">Link Matching</h2>
          <p className="text-neutral-400 mb-6">
            Weave uses embedding-based semantic matching to find the most
            relevant link partners for your content. Match scores are
            calculated using four weighted factors:
          </p>
          <ul className="space-y-3 text-neutral-400">
            <li className="flex items-start gap-2">
              <span className="text-white font-semibold shrink-0">60%</span>
              <span>Semantic relevance — cosine similarity of content embeddings</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-white font-semibold shrink-0">25%</span>
              <span>DR proximity — how close your domain ratings are</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-white font-semibold shrink-0">15%</span>
              <span>Traffic freshness — recently published content preferred</span>
            </li>
          </ul>
          <p className="text-neutral-500 mt-6 text-sm">
            All links use A-B-C triangulation architecture to avoid direct
            reciprocal patterns that search engines penalize.
          </p>
        </section>
      </div>
    </main>
  );
}
