import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms of Service",
  description: "Weave terms of service — rules and guidelines for using the platform.",
};

export default function TermsPage() {
  return (
    <main className="min-h-screen bg-neutral-950 text-white">
      <div className="mx-auto max-w-3xl px-6 py-24">
        <h1 className="text-4xl font-bold mb-8">Terms of Service</h1>
        <p className="text-neutral-400 mb-8">Last updated: July 2026</p>

        <section className="space-y-6 text-neutral-300 leading-relaxed">
          <h2 className="text-xl font-semibold text-white mt-10">
            1. Acceptance of Terms
          </h2>
          <p>
            By using Weave, you agree to these terms. If you do not agree, do
            not use the service.
          </p>

          <h2 className="text-xl font-semibold text-white mt-10">
            2. Account Registration
          </h2>
          <p>
            You must provide accurate information when registering. You are
            responsible for maintaining the confidentiality of your account
            credentials and API keys.
          </p>

          <h2 className="text-xl font-semibold text-white mt-10">
            3. Domain Requirements
          </h2>
          <p>
            All domains must pass our automated vetting process. Domains must
            have a minimum DR of 5, monthly traffic of 500+, spam score below
            15%, and be at least 6 months old. PBNs and spam sites are
            prohibited.
          </p>

          <h2 className="text-xl font-semibold text-white mt-10">
            4. Link Placement Standards
          </h2>
          <p>
            Outbound links must be placed in relevant, contextual content.
            Links must use natural anchor text variation. Footer, sidebar, and
            author bio links are depreciated in scoring. Direct reciprocal
            linking schemes are prohibited.
          </p>

          <h2 className="text-xl font-semibold text-white mt-10">
            5. Credit System
          </h2>
          <p>
            Credits are earned by hosting outbound links and spent to receive
            inbound links. Credits expire 180 days after issuance. Negative
            balances are not permitted. We reserve the right to reverse credits
            for policy violations.
          </p>

          <h2 className="text-xl font-semibold text-white mt-10">
            6. Termination
          </h2>
          <p>
            We may suspend or terminate accounts that violate these terms,
            including three-strikes enforcement for link removals within 90 days.
            Termination results in forfeiture of remaining credits.
          </p>

          <h2 className="text-xl font-semibold text-white mt-10">
            7. Limitation of Liability
          </h2>
          <p>
            Weave is provided &ldquo;as is&rdquo; without warranty. We are not
            liable for damages arising from use of the service, including but
            not limited to search engine penalties or loss of link equity.
          </p>

          <h2 className="text-xl font-semibold text-white mt-10">
            8. Contact
          </h2>
          <p>
            For questions about these terms, contact legal@getweave.io.
          </p>
        </section>
      </div>
    </main>
  );
}
