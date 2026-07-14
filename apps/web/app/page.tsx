import type { Metadata } from "next";
import { OrganizationSchema, WebApplicationSchema } from "@/components/json-ld";

export const metadata: Metadata = {
  title: "AI-Native Backlink Exchange Platform — MCP-Powered Link Building",
  description:
    "Weave is an AI-native backlink exchange platform that integrates directly into Claude, ChatGPT, and MCP-compatible workflows. Automatically discover, place, and earn contextual backlinks with transparent credit scoring.",
  openGraph: {
    title: "Weave — AI-Native Backlink Exchange | MCP-Powered Link Building",
    description:
      "Automatically discover, place, and earn contextual backlinks through your AI agent. No manual outreach, no opaque pricing.",
  },
};

export default function Home() {
  return (
    <main className="min-h-screen bg-neutral-950 text-white">
      <OrganizationSchema />
      <WebApplicationSchema />
      {/* Nav */}
      <nav className="border-b border-neutral-800">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <span className="text-xl font-bold tracking-tight">Weave</span>
          <div className="flex items-center gap-6 text-sm text-neutral-400">
            <a href="#how-it-works" className="hover:text-white transition">
              How It Works
            </a>
            <a href="#features" className="hover:text-white transition">
              Features
            </a>
            <a href="#pricing" className="hover:text-white transition">
              Pricing
            </a>
            <a href="/docs" className="hover:text-white transition">
              Docs
            </a>
            <a
              href="/dashboard"
              className="rounded-lg bg-white px-4 py-2 font-medium text-black hover:bg-neutral-200 transition"
            >
              Dashboard
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="mx-auto max-w-4xl px-6 pb-24 pt-32 text-center">
        <div className="mb-6 inline-block rounded-full border border-neutral-700 px-4 py-1.5 text-sm text-neutral-400">
          Now in public beta — join 500+ domains
        </div>
        <h1 className="text-5xl font-bold leading-tight tracking-tight sm:text-6xl lg:text-7xl">
          AI-Native Backlink Exchange
          <br />
          <span className="text-neutral-400">
            for Automated Link Building
          </span>
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-neutral-400 sm:text-xl">
          Weave is the first backlink exchange platform that integrates directly
          into your AI writing workflow via MCP. Your AI agent discovers relevant
          link partners, places contextual backlinks, and earns you credits —
          all without manual outreach or agency fees.
        </p>
        <div className="mt-10 flex flex-wrap justify-center gap-4">
          <a
            href="/dashboard"
            className="rounded-lg bg-white px-8 py-3.5 text-base font-semibold text-black hover:bg-neutral-200 transition"
          >
            Get Started
          </a>
          <a
            href="/docs"
            className="rounded-lg border border-neutral-700 px-8 py-3.5 text-base font-semibold hover:border-neutral-500 transition"
          >
            View Docs
          </a>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="border-t border-neutral-800 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="text-center text-3xl font-bold sm:text-4xl">
            How It Works
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-center text-neutral-400">
            Three steps to automated, high-quality backlinks.
          </p>
          <div className="mt-16 grid gap-12 sm:grid-cols-3">
            {[
              {
                step: "1",
                title: "Register Your Domain",
                description:
                  "Add your site and verify ownership via DNS, meta tag, or file upload. Automated vetting ensures network quality.",
              },
              {
                step: "2",
                title: "AI Discovers Matches",
                description:
                  "Our semantic matching engine finds contextually relevant link opportunities ranked by relevance, DR, and audience overlap.",
              },
              {
                step: "3",
                title: "Links Placed Automatically",
                description:
                  "Your AI agent places outbound links during content creation, earns credits, and receives quality inbound links in return.",
              },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full border border-neutral-700 text-lg font-bold">
                  {item.step}
                </div>
                <h3 className="mt-6 text-xl font-semibold">{item.title}</h3>
                <p className="mt-3 text-neutral-400">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="border-t border-neutral-800 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="text-center text-3xl font-bold sm:text-4xl">
            Built for Modern Link Building
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-center text-neutral-400">
            Every feature designed to make backlink acquisition effortless,
            transparent, and effective.
          </p>
          <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                title: "Semantic Matching",
                description:
                  "Embedding-based relevance scoring finds contextually perfect link partners — not just category matches.",
              },
              {
                title: "Credit System",
                description:
                  "Fully transparent formula. Earn credits by placing outbound links, spend them on quality inbound links. No hidden costs.",
              },
              {
                title: "A-B-C Triangulation",
                description:
                  "No direct reciprocal links. Weave forms multi-site triangles so every exchange looks natural to search engines.",
              },
              {
                title: "MCP Integration",
                description:
                  "Works inside Claude, Cursor, and any MCP-compatible AI. Discover and place links without leaving your writing flow.",
              },
              {
                title: "Link Health Monitoring",
                description:
                  "24-hour crawl cycle checks every placed link. Auto-replacement SLA ensures you never lose link equity.",
              },
              {
                title: "Transparent Scoring",
                description:
                  "Every match shows a detailed quality breakdown: semantic relevance, DR proximity, audience overlap, and freshness.",
              },
            ].map((feature) => (
              <div
                key={feature.title}
                className="rounded-xl border border-neutral-800 bg-neutral-900 p-6"
              >
                <h3 className="text-lg font-semibold">{feature.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-neutral-400">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Comparison Table */}
      <section className="border-t border-neutral-800 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="text-center text-3xl font-bold sm:text-4xl">
            Why Weave?
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-center text-neutral-400">
            See how Weave compares to traditional methods and competitors.
          </p>
          <div className="mt-16 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-neutral-800 text-neutral-400">
                  <th className="pb-4 pr-6 font-medium">Feature</th>
                  <th className="pb-4 pr-6 font-medium">Traditional Outreach</th>
                  <th className="pb-4 pr-6 font-medium">Competitors</th>
                  <th className="pb-4 font-medium text-white">Weave</th>
                </tr>
              </thead>
              <tbody className="text-neutral-400">
                {[
                  ["Cost per link", "$100 — $500", "$59/mo (opaque)", "From $0 (transparent credits)"],
                  ["Matching quality", "Manual research", "Category-based", "Semantic embeddings + audience overlap"],
                  ["Link architecture", "Direct reciprocal", "A-B-C only", "A-B-C + configurable multi-hop"],
                  ["Automation", "Fully manual", "Semi-automated", "Fully automated via MCP"],
                  ["Transparency", "Varies by agency", "Minimal", "Open credit formula, full audit trail"],
                  ["Link monitoring", "None", "Basic dashboard", "24h crawl cycle, auto-replacement SLA"],
                  ["Time to first link", "2 — 4 weeks", "1 — 2 weeks", "Same day"],
                ].map(([feature, traditional, competitor, weave]) => (
                  <tr key={feature} className="border-b border-neutral-800/50">
                    <td className="py-4 pr-6 font-medium text-white">{feature}</td>
                    <td className="py-4 pr-6">{traditional}</td>
                    <td className="py-4 pr-6">{competitor}</td>
                    <td className="py-4 font-medium text-white">{weave}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="border-t border-neutral-800 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="text-center text-3xl font-bold sm:text-4xl">
            Simple, Transparent Pricing
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-center text-neutral-400">
            Start free. Scale as you grow. Annual billing saves 20%.
          </p>
          <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {[
              {
                name: "Free",
                price: "$0",
                period: "forever",
                features: [
                  "1 domain",
                  "10 credits / month",
                  "100 MCP requests / hour",
                  "Basic category matching",
                  "A-B-C link architecture",
                  "Community support",
                ],
              },
              {
                name: "Starter",
                price: "$29",
                period: "/ month",
                features: [
                  "5 domains",
                  "100 credits / month",
                  "1,000 MCP requests / hour",
                  "Semantic matching",
                  "A-B-C link architecture",
                  "60-day link survival SLA",
                  "Email support",
                  "+10% credit bonus",
                ],
              },
              {
                name: "Pro",
                price: "$79",
                period: "/ month",
                highlight: true,
                features: [
                  "25 domains",
                  "500 credits / month",
                  "5,000 MCP requests / hour",
                  "Semantic + audience matching",
                  "A-B-C + multi-hop",
                  "90-day link survival SLA",
                  "Priority email support",
                  "CSV / PDF exports",
                  "+25% credit bonus",
                ],
              },
              {
                name: "Agency",
                price: "$199",
                period: "/ month",
                features: [
                  "Unlimited domains",
                  "2,000 credits / month",
                  "Unlimited MCP requests",
                  "Semantic + audience + custom",
                  "Custom topologies",
                  "120-day SLA + replacement",
                  "Dedicated Slack support",
                  "White-label dashboard",
                  "Bulk operations API",
                  "+50% credit bonus",
                ],
              },
            ].map((tier) => (
              <div
                key={tier.name}
                className={`rounded-xl border p-6 ${
                  tier.highlight
                    ? "border-white bg-neutral-900"
                    : "border-neutral-800 bg-neutral-900"
                }`}
              >
                {tier.highlight && (
                  <div className="mb-4 inline-block rounded-full bg-white px-3 py-1 text-xs font-semibold text-black">
                    Most Popular
                  </div>
                )}
                <h3 className="text-lg font-semibold">{tier.name}</h3>
                <div className="mt-2">
                  <span className="text-4xl font-bold">{tier.price}</span>
                  <span className="ml-1 text-neutral-400">{tier.period}</span>
                </div>
                <ul className="mt-6 space-y-3 text-sm text-neutral-400">
                  {tier.features.map((f) => (
                    <li key={f} className="flex items-start gap-2">
                      <span className="mt-0.5 text-neutral-500">&#10003;</span>
                      {f}
                    </li>
                  ))}
                </ul>
                <a
                  href="/dashboard"
                  className={`mt-8 block rounded-lg py-2.5 text-center text-sm font-semibold transition ${
                    tier.highlight
                      ? "bg-white text-black hover:bg-neutral-200"
                      : "border border-neutral-700 hover:border-neutral-500"
                  }`}
                >
                  {tier.name === "Free" ? "Get Started Free" : `Start ${tier.name}`}
                </a>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* MCP Setup */}
      <section className="border-t border-neutral-800 py-24">
        <div className="mx-auto max-w-3xl px-6">
          <h2 className="text-center text-3xl font-bold sm:text-4xl">
            Set Up in 30 Seconds
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-center text-neutral-400">
            Add Weave to your Claude Desktop config and start earning backlinks
            immediately.
          </p>
          <div className="mt-12 overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900">
            <div className="flex items-center gap-2 border-b border-neutral-800 px-4 py-3 text-sm text-neutral-400">
              <span className="font-mono">claude_desktop_config.json</span>
            </div>
            <pre className="overflow-x-auto p-6 text-sm leading-relaxed text-neutral-300">
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
          <p className="mt-6 text-center text-sm text-neutral-500">
            Get your API key from the{" "}
            <a href="/dashboard" className="text-neutral-300 underline hover:text-white">
              dashboard
            </a>{" "}
            after signing up.
          </p>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-neutral-800 py-24">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="text-3xl font-bold sm:text-4xl">
            Start Building Links Today
          </h2>
          <p className="mt-4 text-lg text-neutral-400">
            Join the network. No credit card required for the free tier.
          </p>
          <a
            href="/dashboard"
            className="mt-8 inline-block rounded-lg bg-white px-8 py-3.5 text-base font-semibold text-black hover:bg-neutral-200 transition"
          >
            Get Started Free
          </a>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-neutral-800 py-12">
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid gap-8 sm:grid-cols-4">
            <div>
              <span className="text-lg font-bold">Weave</span>
              <p className="mt-3 text-sm text-neutral-500">
                AI-native backlink exchange. Build authority while you write.
              </p>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-neutral-300">Product</h4>
              <ul className="mt-3 space-y-2 text-sm text-neutral-500">
                <li><a href="#features" className="hover:text-white transition">Features</a></li>
                <li><a href="#pricing" className="hover:text-white transition">Pricing</a></li>
                <li><a href="/docs" className="hover:text-white transition">Documentation</a></li>
                <li><a href="/docs#api-reference" className="hover:text-white transition">API Reference</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-neutral-300">Company</h4>
              <ul className="mt-3 space-y-2 text-sm text-neutral-500">
                <li><a href="/blog" className="hover:text-white transition">Blog</a></li>
                <li><a href="/changelog" className="hover:text-white transition">Changelog</a></li>
                <li><a href="/about" className="hover:text-white transition">About</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-neutral-300">Legal</h4>
              <ul className="mt-3 space-y-2 text-sm text-neutral-500">
                <li><a href="/privacy" className="hover:text-white transition">Privacy Policy</a></li>
                <li><a href="/terms" className="hover:text-white transition">Terms of Service</a></li>
              </ul>
            </div>
          </div>
          <div className="mt-12 border-t border-neutral-800 pt-8 text-center text-sm text-neutral-600">
            &copy; {new Date().getFullYear()} Weave. All rights reserved.
          </div>
        </div>
      </footer>
    </main>
  );
}
