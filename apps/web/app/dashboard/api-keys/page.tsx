import type { Metadata } from "next";
import ApiKeysContent from "./api-keys-content";

export const metadata: Metadata = {
  title: "API Keys",
  description: "Generate and manage your Weave API keys for MCP integration.",
  robots: { index: false, follow: false },
};

export default function ApiKeysPage() {
  return <ApiKeysContent />;
}
