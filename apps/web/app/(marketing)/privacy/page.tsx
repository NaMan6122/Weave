import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "Weave privacy policy — how we collect, use, and protect your data.",
};

export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-neutral-950 text-white">
      <div className="mx-auto max-w-3xl px-6 py-24">
        <h1 className="text-4xl font-bold mb-8">Privacy Policy</h1>
        <p className="text-neutral-400 mb-8">Last updated: July 2026</p>

        <section className="space-y-6 text-neutral-300 leading-relaxed">
          <h2 className="text-xl font-semibold text-white mt-10">
            1. Information We Collect
          </h2>
          <p>
            We collect information you provide when creating an account: email
            address, name, and avatar (if using OAuth). When you register a
            domain, we collect the domain name and associated metadata for
            vetting and matching purposes.
          </p>
          <p>
            We automatically collect usage data: API request logs, page views,
            and feature interactions to improve our service.
          </p>

          <h2 className="text-xl font-semibold text-white mt-10">
            2. How We Use Your Information
          </h2>
          <p>
            Your information is used to operate and improve Weave: authenticate
            you, process domain verification, facilitate link matching, display
            analytics, and communicate service updates.
          </p>
          <p>
            We do not sell your personal information to third parties. Domain
            and link placement data shared within the network is limited to what
            is necessary for the exchange to function.
          </p>

          <h2 className="text-xl font-semibold text-white mt-10">
            3. Data Retention
          </h2>
          <p>
            We retain your account data for as long as your account is active.
            Link placement records are retained for 2 years minimum per our
            SLA requirements. You may request deletion of your data at any time.
          </p>

          <h2 className="text-xl font-semibold text-white mt-10">
            4. Third-Party Services
          </h2>
          <p>
            We use third-party services for domain metrics (Moz, DataForSEO),
            embeddings (OpenAI), anchor text generation (Anthropic), email
            (Resend), and payment processing (Stripe). Each service processes
            data according to their own privacy policies.
          </p>

          <h2 className="text-xl font-semibold text-white mt-10">
            5. Contact
          </h2>
          <p>
            For privacy inquiries, contact us at privacy@getweave.io.
          </p>
        </section>
      </div>
    </main>
  );
}
