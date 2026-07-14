import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import { AuthProvider } from "@/components/auth-provider";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

const siteUrl = process.env.NEXTAUTH_URL || "https://getweave.io";

export const metadata: Metadata = {
  title: {
    default: "Weave — AI-Native Backlink Exchange",
    template: "%s | Weave",
  },
  description:
    "Automated backlink exchange platform that integrates directly into AI content workflows via MCP.",
  metadataBase: new URL(siteUrl),
  openGraph: {
    title: "Weave — AI-Native Backlink Exchange",
    description:
      "Automated backlink exchange platform that integrates directly into AI content workflows via MCP.",
    url: siteUrl,
    siteName: "Weave",
    type: "website",
    locale: "en_US",
    images: [{ url: "/og-image.svg", width: 1200, height: 630 }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Weave — AI-Native Backlink Exchange",
    description:
      "Automated backlink exchange platform that integrates directly into AI content workflows via MCP.",
    images: ["/og-image.svg"],
  },
  icons: { icon: "/favicon.svg" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0a0a0a",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
