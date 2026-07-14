import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About",
  description: "Learn about Weave — the AI-native backlink exchange platform.",
};

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-neutral-950 text-white">
      <div className="mx-auto max-w-3xl px-6 py-24">
        <h1 className="text-4xl font-bold mb-8">About Weave</h1>
        <section className="space-y-6 text-neutral-300 leading-relaxed">
          <p>
            Weave was built to solve a fundamental problem in SEO: link building
            is broken. It&apos;s expensive, manual, and opaque. Agencies charge
            hundreds per link. Automated solutions offer low-quality results.
            The status quo favors those with big budgets.
          </p>
          <p>
            We believe that with semantic matching, transparent credit scoring,
            and MCP-native AI integration, link building can be automated
            without sacrificing quality. Every link placed through Weave is
            contextually relevant, naturally anchored, and triangulated to avoid
            search engine penalties.
          </p>
          <p>
            The platform is built by SEOs and engineers who understand both the
            technical and practical sides of link acquisition. We started Weave
            because we wanted the tool ourselves.
          </p>
        </section>
      </div>
    </main>
  );
}
