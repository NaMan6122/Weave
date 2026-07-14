import type { Metadata } from "next";
import LoginForm from "./login-form";

export const metadata: Metadata = {
  title: "Sign In",
  description: "Sign in to your Weave account to manage domains, credits, and backlinks.",
  robots: { index: false, follow: false },
};

export default function LoginPage() {
  return <LoginForm />;
}
