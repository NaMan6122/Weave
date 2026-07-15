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

      {/* Nav — minimal */}
      <nav className="sticky top-0 z-50 border-b border-neutral-800 bg-neutral-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <span className="text-xl font-bold tracking-tight">Weave</span>
          <div className="flex items-center gap-6 text-sm text-neutral-400">
            <a href="#pricing" className="hover:text-white transition">Pricing</a>
            <a
              href="/dashboard"
              className="rounded-lg bg-white px-4 py-2 font-medium text-black hover:bg-neutral-200 transition"
            >
              Join Now — Free
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="mx-auto max-w-5xl px-6 pb-24 pt-20 text-center">
        <div className="mb-6 inline-block rounded-full border border-neutral-700 px-4 py-1.5 text-sm text-neutral-400">
          The backlink network for AI agents
        </div>
        <h1 className="text-4xl font-bold leading-tight tracking-tight sm:text-5xl lg:text-6xl">
          Build authority on autopilot
          <br />
          <span className="text-neutral-400">with quality-vetted backlinks</span>
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-neutral-400">
          A-B-C routing and strict domain review built for durable SEO growth in AI content workflows.
          Your AI agent discovers partners, places links, and earns credits — all without manual outreach.
        </p>

        {/* Animated A-B-C chain */}
        <div className="mt-12 flex flex-col items-center gap-2">
          {[
            { dr: 21, domain: "liftlab.com", label: "YOUR SITE" },
            { dr: 71, domain: "gymflow.com", label: "LINK PARTNER" },
            { dr: 52, domain: "fitpro.com", label: "LINK PARTNER" },
            { dr: 64, domain: "musclekit.com", label: "LINK PARTNER" },
            { dr: 84, domain: "trainup.com", label: "LINK PARTNER" },
            { dr: 16, domain: "runhub.com", label: "MATCHING..." },
          ].map((node, i) => (
            <div key={i} className="flex flex-col items-center">
              <div
                className="flex items-center gap-3 rounded-lg border border-neutral-800 bg-neutral-900 px-4 py-2 opacity-0 animate-[fadeIn_0.4s_ease-out_forwards]"
                style={{ animationDelay: `${i * 0.2}s` }}
              >
                <span className={`rounded-full px-2 py-0.5 text-xs font-bold ${
                  node.dr >= 50 ? "bg-green-900/50 text-green-300" :
                  node.dr >= 20 ? "bg-yellow-900/50 text-yellow-300" :
                  "bg-red-900/50 text-red-300"
                }`}>
                  {node.dr}
                </span>
                <span className="font-mono text-sm text-neutral-300">{node.domain}</span>
                <span className="text-xs text-neutral-500">{node.label}</span>
              </div>
              {i < 5 && (
                <div className="h-3 w-px bg-neutral-700 opacity-0 animate-[fadeIn_0.3s_ease-out_forwards]" style={{ animationDelay: `${i * 0.2 + 0.1}s` }} />
              )}
            </div>
          ))}
        </div>

        <style>{`
          @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
          }
        `}</style>

        <div className="mt-10 flex flex-wrap justify-center gap-4">
          <a
            href="/dashboard"
            className="rounded-lg bg-white px-8 py-3.5 text-base font-semibold text-black hover:bg-neutral-200 transition"
          >
            Join the network — Free
          </a>
        </div>
      </section>

      {/* Problem / Solution */}
      <section className="border-t border-neutral-800 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid gap-12 md:grid-cols-2">
            <div>
              <h2 className="text-sm font-semibold uppercase tracking-wider text-red-400 mb-4">Before: Manual outreach</h2>
              <ul className="space-y-3 text-neutral-400">
                <li className="flex items-start gap-2"><span className="text-red-400 mt-0.5">✕</span>Hours spent prospecting and emailing for one placement</li>
                <li className="flex items-start gap-2"><span className="text-red-400 mt-0.5">✕</span>Expensive paid-per-link through agencies or marketplaces</li>
                <li className="flex items-start gap-2"><span className="text-red-400 mt-0.5">✕</span>Inconsistent quality and hidden PBN risk</li>
                <li className="flex items-start gap-2"><span className="text-red-400 mt-0.5">✕</span>Authority growth lags behind your publishing velocity</li>
              </ul>
            </div>
            <div>
              <h2 className="text-sm font-semibold uppercase tracking-wider text-green-400 mb-4">After: Agent-native exchange</h2>
              <ul className="space-y-3 text-neutral-400">
                <li className="flex items-start gap-2"><span className="text-green-400 mt-0.5">✓</span>MCP-connected agents discover relevant partners while writing</li>
                <li className="flex items-start gap-2"><span className="text-green-400 mt-0.5">✓</span>Quality-vetted sites matched by niche, language, and authority</li>
                <li className="flex items-start gap-2"><span className="text-green-400 mt-0.5">✓</span>Contextual links placed naturally in publish-ready content</li>
                <li className="flex items-start gap-2"><span className="text-green-400 mt-0.5">✓</span>A-B-C link architecture built for safer, lower-footprint growth</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works — 4 steps */}
      <section id="how-it-works" className="border-t border-neutral-800 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="text-center text-3xl font-bold sm:text-4xl">How links are earned</h2>
          <p className="mx-auto mt-4 max-w-2xl text-center text-neutral-400">
            Publish content. The network handles the rest.
          </p>
          <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { step: "01", title: "Connect your site(s)", desc: "Integrate our MCP server with two lines of code. Your AI agent continues writing as usual." },
              { step: "02", title: "Automated Matching", desc: "Your agent queries our network and embeds relevant peer links while writing. You earn credits instantly." },
              { step: "03", title: "Receive Backlinks", desc: "Credits work silently. We automatically place your links inside highly relevant peer articles." },
              { step: "04", title: "Grow Authority", desc: "A-B-C backlinks form safely. Gain verifiable domain rating with zero manual outreach." },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full border border-neutral-700 text-lg font-bold text-neutral-300">
                  {item.step}
                </div>
                <h3 className="mt-6 text-lg font-semibold">{item.title}</h3>
                <p className="mt-3 text-sm text-neutral-400">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Product Demo — tabbed (static for landing page) */}
      <section className="border-t border-neutral-800 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="text-center text-3xl font-bold sm:text-4xl">What you get</h2>
          <div className="mt-12 grid gap-8 lg:grid-cols-2">
            {/* MCP Connector */}
            <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-6">
              <h3 className="text-lg font-semibold mb-4">MCP Connector</h3>
              <p className="text-sm text-neutral-400 mb-4">Connect from your AI agent, assistant, or any MCP-compatible tool.</p>
              <div className="rounded-lg border border-neutral-800 bg-neutral-950 p-4 font-mono text-sm text-neutral-300 mb-4">
                <span className="text-neutral-500">$</span> claude mcp add weave https://mcp.getweave.io/sse
              </div>
              <div className="flex flex-wrap gap-3">
                {["Claude", "Cursor", "ChatGPT", "n8n", "MCP"].map((tool) => (
                  <span key={tool} className="rounded-full border border-neutral-700 px-3 py-1 text-xs text-neutral-400">
                    {tool}
                  </span>
                ))}
              </div>
            </div>

            {/* Dashboard Preview */}
            <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-6">
              <h3 className="text-lg font-semibold mb-4">Dashboard</h3>
              <div className="rounded-lg border border-neutral-800 bg-neutral-950 p-4">
                <div className="grid grid-cols-3 gap-2 mb-3">
                  <div className="rounded border border-neutral-800 p-2 text-center">
                    <p className="text-[10px] text-neutral-500">DR</p>
                    <p className="text-lg font-bold">42</p>
                    <p className="text-[10px] text-green-400">+8 this year</p>
                  </div>
                  <div className="rounded border border-neutral-800 p-2 text-center">
                    <p className="text-[10px] text-neutral-500">Backlinks</p>
                    <p className="text-lg font-bold">14</p>
                    <p className="text-[10px] text-neutral-500">placed</p>
                  </div>
                  <div className="rounded border border-neutral-800 p-2 text-center">
                    <p className="text-[10px] text-neutral-500">Credits</p>
                    <p className="text-lg font-bold">4.2K</p>
                  </div>
                </div>
                <div className="space-y-1">
                  {[
                    { site: "menshealth.com", dr: 88, status: "Live" },
                    { site: "healthline.com", dr: 91, status: "Pending" },
                  ].map((row) => (
                    <div key={row.site} className="flex items-center justify-between text-xs text-neutral-400">
                      <span className="font-mono">{row.site}</span>
                      <span className={`rounded-full px-1.5 py-0.5 text-[10px] ${row.status === "Live" ? "bg-green-900/50 text-green-300" : "bg-yellow-900/50 text-yellow-300"}`}>
                        DR {row.dr} {row.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Authority Growth */}
      <section className="border-t border-neutral-800 py-24">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="text-3xl font-bold sm:text-4xl">Grow Authority on autopilot</h2>
          <p className="mt-4 text-lg text-neutral-400">
            Backlinks placed automatically. Domain rating climbs. Traffic compounds.
          </p>
          <p className="mt-2 text-neutral-500">
            Rank on Google. Get cited by AI.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-4">
            {["Google", "ChatGPT", "Claude", "Gemini", "Perplexity", "Grok"].map((engine) => (
              <span key={engine} className="rounded-full border border-neutral-800 px-4 py-2 text-sm text-neutral-400">
                {engine}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Network Preview */}
      <section className="border-t border-neutral-800 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="text-center text-3xl font-bold sm:text-4xl">Meet the network</h2>
          <p className="mx-auto mt-4 max-w-2xl text-center text-neutral-400">
            Verified member sites currently active in the exchange.
          </p>
          <div className="mt-12 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-neutral-800 text-neutral-500">
                  <th className="pb-3 pr-4 font-medium">Domain</th>
                  <th className="pb-3 pr-4 font-medium">Industry</th>
                  <th className="pb-3 pr-4 font-medium">Niche</th>
                  <th className="pb-3 pr-4 font-medium">DR</th>
                  <th className="pb-3 font-medium">Traffic</th>
                </tr>
              </thead>
              <tbody className="text-neutral-400">
                {[
                  ["str***ng.com", "Fitness", "Strength training", 23, "18k/mo"],
                  ["fin***ce.ai", "Finance", "Personal finance", 72, "91k/mo"],
                  ["dev***ls.dev", "Tech", "Developer tools", 35, "31k/mo"],
                  ["run***ng.net", "Fitness", "Running & endurance", 64, "37k/mo"],
                  ["we***ss.so", "Health", "Mental wellness", 22, "31k/mo"],
                  ["l***law.com", "Legal", "Business law", 31, "18k/mo"],
                ].map(([domain, industry, niche, dr, traffic]) => (
                  <tr key={domain as string} className="border-b border-neutral-800/50">
                    <td className="py-3 pr-4 font-mono text-neutral-300">{domain}</td>
                    <td className="py-3 pr-4">{industry}</td>
                    <td className="py-3 pr-4">{niche}</td>
                    <td className="py-3 pr-4">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-bold ${
                        (dr as number) >= 50 ? "bg-green-900/50 text-green-300" :
                        (dr as number) >= 20 ? "bg-yellow-900/50 text-yellow-300" :
                        "bg-red-900/50 text-red-300"
                      }`}>{dr}</span>
                    </td>
                    <td className="py-3">{traffic}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-8 text-center text-neutral-400">
            <a href="/dashboard" className="text-white underline hover:text-neutral-300">Add your sites. Join the network for free</a>
          </p>
        </div>
      </section>

      {/* Quality Vetting */}
      <section className="border-t border-neutral-800 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="text-center text-3xl font-bold sm:text-4xl">Built for quality, not spam</h2>
          <p className="mx-auto mt-4 max-w-2xl text-center text-neutral-400">
            All sites are verified and matched based on contextual relevance.
          </p>
          <div className="mt-12 grid gap-8 md:grid-cols-2">
            {/* Approval card */}
            <div className="rounded-xl border border-green-900/50 bg-neutral-900 p-6">
              <div className="flex items-center justify-between mb-4">
                <span className="font-mono text-lg text-neutral-300">TargetDomain.com</span>
                <span className="rounded-full bg-green-900/50 px-3 py-1 text-xs font-semibold text-green-300">Approved</span>
              </div>
              <div className="space-y-2 text-sm">
                {[
                  ["Domain Rating", "68"],
                  ["Organic Traffic", "12.4k / mo"],
                  ["Spam Score", "1%"],
                  ["PBN Detection", "Clear"],
                ].map(([label, value]) => (
                  <div key={label} className="flex justify-between border-b border-neutral-800 pb-2">
                    <span className="text-neutral-500">{label}</span>
                    <span className="text-neutral-300">{value}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Match scoring */}
            <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-6">
              <h3 className="text-sm font-semibold text-neutral-300 mb-4">Topical Relevance Matching</h3>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-neutral-500">
                    <th className="pb-2 text-left font-medium">Domain</th>
                    <th className="pb-2 text-left font-medium">Niche</th>
                    <th className="pb-2 text-right font-medium">Match</th>
                  </tr>
                </thead>
                <tbody className="text-neutral-400">
                  {[
                    ["techgear.io", "Gear", "12%"],
                    ["puremuscle.com", "Nutrition", "98%"],
                    ["liftpro.com", "Strength", "84%"],
                  ].map(([domain, niche, match]) => (
                    <tr key={domain} className="border-t border-neutral-800">
                      <td className="py-2 font-mono text-xs">{domain}</td>
                      <td className="py-2">{niche}</td>
                      <td className="py-2 text-right">
                        <span className={`rounded-full px-2 py-0.5 text-xs font-bold ${
                          parseInt(match) >= 80 ? "bg-green-900/50 text-green-300" :
                          parseInt(match) >= 40 ? "bg-yellow-900/50 text-yellow-300" :
                          "bg-neutral-700 text-neutral-400"
                        }`}>{match}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="border-t border-neutral-800 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="text-center text-3xl font-bold sm:text-4xl">Simple, Transparent Pricing</h2>
          <p className="mx-auto mt-4 max-w-2xl text-center text-neutral-400">
            Start free. Scale as you grow. Annual billing saves 20%.
          </p>
          <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {[
              {
                name: "Free", price: "$0", period: "forever",
                features: ["5 domains", "100 MCP requests / hour", "Basic category matching", "A-B-C link architecture", "Community support"],
              },
              {
                name: "Starter", price: "$29", period: "/ month",
                features: ["25 domains", "1,000 MCP requests / hour", "Semantic matching", "60-day link survival SLA", "Email support", "+10% credit bonus"],
              },
              {
                name: "Pro", price: "$79", period: "/ month", highlight: true,
                features: ["100 domains", "5,000 MCP requests / hour", "Semantic + audience matching", "A-B-C + multi-hop", "90-day link survival SLA", "Priority email support", "CSV / PDF exports", "+25% credit bonus"],
              },
              {
                name: "Agency", price: "$199", period: "/ month",
                features: ["Unlimited domains", "Unlimited MCP requests", "Custom matching", "Custom topologies", "120-day SLA + replacement", "Dedicated Slack support", "White-label dashboard", "+50% credit bonus"],
              },
            ].map((tier) => (
              <div
                key={tier.name}
                className={`rounded-xl border p-6 ${tier.highlight ? "border-white bg-neutral-900" : "border-neutral-800 bg-neutral-900"}`}
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
                    tier.highlight ? "bg-white text-black hover:bg-neutral-200" : "border border-neutral-700 hover:border-neutral-500"
                  }`}
                >
                  {tier.name === "Free" ? "Get Started Free" : `Start ${tier.name}`}
                </a>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="border-t border-neutral-800 py-24">
        <div className="mx-auto max-w-3xl px-6">
          <h2 className="text-center text-3xl font-bold sm:text-4xl">Frequently asked questions</h2>
          <div className="mt-12 space-y-4">
            {[
              { q: "Is this safe? Will Google penalize me?", a: "Weave uses A-B-C triangulation — no direct reciprocal links. Every exchange forms a triangle across 3 different owners, making the link pattern indistinguishable from organic editorial links." },
              { q: "How does the credit system work?", a: "You earn credits by hosting links to partner sites. You spend credits to get your links placed on partner sites. The formula is transparent: base credit × DR multiplier × relevance × placement quality." },
              { q: "What is MCP?", a: "Model Context Protocol is an open standard for AI agents to use external tools. Weave provides an MCP server so your AI writing assistant (Claude, Cursor, ChatGPT) can discover and place links without leaving your workflow." },
              { q: "How are sites vetted?", a: "Every domain must pass: DR ≥ 5, traffic ≥ 500/mo, spam score < 15%, domain age ≥ 6 months, and no PBN patterns. Sites are re-vetted weekly." },
              { q: "Can I use Weave without an AI agent?", a: "Yes. The dashboard provides full access to discover links, place links, and manage your domains manually. MCP is an optional accelerator." },
              { q: "What happens if a partner removes my link?", a: "Credits are reversed from the remover's account (2× penalty). A replacement link is auto-queued. Repeat offenders (3+ in 90 days) get suspended." },
            ].map(({ q, a }) => (
              <details key={q} className="group rounded-xl border border-neutral-800 bg-neutral-900">
                <summary className="cursor-pointer px-6 py-4 text-sm font-medium text-neutral-300 list-none flex items-center justify-between">
                  {q}
                  <span className="text-neutral-500 group-open:rotate-45 transition-transform text-lg">+</span>
                </summary>
                <p className="px-6 pb-4 text-sm text-neutral-400">{a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-neutral-800 py-24">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="text-3xl font-bold sm:text-4xl">Start Building Links Today</h2>
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
                <li><a href="#pricing" className="hover:text-white transition">Pricing</a></li>
                <li><a href="#how-it-works" className="hover:text-white transition">How It Works</a></li>
                <li><a href="/dashboard" className="hover:text-white transition">Dashboard</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-neutral-300">Resources</h4>
              <ul className="mt-3 space-y-2 text-sm text-neutral-500">
                <li><a href="/docs" className="hover:text-white transition">Documentation</a></li>
                <li><a href="/blog" className="hover:text-white transition">Blog</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-neutral-300">Legal</h4>
              <ul className="mt-3 space-y-2 text-sm text-neutral-500">
                <li><a href="/privacy" className="hover:text-white transition">Privacy</a></li>
                <li><a href="/terms" className="hover:text-white transition">Terms</a></li>
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
