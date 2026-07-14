import type { Metadata } from "next";

const baseUrl = process.env.NEXT_PUBLIC_API_URL
  ? process.env.NEXT_PUBLIC_API_URL.replace("://localhost:", "://")
  : undefined;
const siteUrl = process.env.NEXTAUTH_URL || "https://getweave.io";

type PageSeo = {
  title: string;
  description: string;
  path?: string;
  noIndex?: boolean;
  ogImage?: string;
};

export function constructMetadata({
  title,
  description,
  path = "",
  noIndex = false,
  ogImage,
}: PageSeo): Metadata {
  const url = `${siteUrl}${path}`;
  const image = ogImage || `${siteUrl}/og-image.svg`;

  return {
    title,
    description,
    metadataBase: new URL(siteUrl),
    alternates: { canonical: url },
    openGraph: {
      title,
      description,
      url,
      siteName: "Weave",
      type: "website",
      locale: "en_US",
      images: [{ url: image, width: 1200, height: 630 }],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [image],
    },
    robots: noIndex ? { index: false, follow: false } : undefined,
    icons: { icon: "/favicon.svg" },
  };
}
