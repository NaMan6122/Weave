const siteUrl = process.env.NEXTAUTH_URL || "https://getweave.io";

export function OrganizationSchema() {
  const schema = {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "Weave",
    url: siteUrl,
    description:
      "AI-native backlink exchange platform. Automatically discover, place, and earn contextual backlinks via MCP.",
    sameAs: [],
  };
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}

export function WebApplicationSchema() {
  const schema = {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    name: "Weave",
    url: siteUrl,
    description:
      "Automated backlink exchange network that integrates directly into AI content workflows via the Model Context Protocol (MCP).",
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    offers: [
      { "@type": "Offer", name: "Free", price: "0", priceCurrency: "USD" },
      { "@type": "Offer", name: "Starter", price: "29", priceCurrency: "USD" },
      { "@type": "Offer", name: "Pro", price: "79", priceCurrency: "USD" },
      { "@type": "Offer", name: "Agency", price: "199", priceCurrency: "USD" },
    ],
  };
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}
