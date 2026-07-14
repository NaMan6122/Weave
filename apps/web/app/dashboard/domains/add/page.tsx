import type { Metadata } from "next";
import AddDomainContent from "./add-domain-content";

export const metadata: Metadata = {
  title: "Add Domain",
  description: "Register a new domain for the Weave backlink exchange network.",
  robots: { index: false, follow: false },
};

export default function AddDomainPage() {
  return <AddDomainContent />;
}
