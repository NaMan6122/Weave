"use client";

import { signIn } from "next-auth/react";
import { useSearchParams } from "next/navigation";
import { useState, Suspense } from "react";

function LoginFormInner() {
  const searchParams = useSearchParams();
  const error = searchParams.get("error");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);

  const handleEmailSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setLoading(true);
    await signIn("credentials", { email, callbackUrl: "/dashboard" });
    setLoading(false);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-950 text-white">
      <div className="w-full max-w-sm rounded-xl border border-neutral-800 p-8">
        <h1 className="text-2xl font-bold mb-6 text-center">
          Sign in to Weave
        </h1>

        {error && (
          <div className="mb-4 rounded-lg bg-red-900/50 border border-red-700 px-4 py-2 text-sm text-red-200">
            {error === "CredentialsSignin"
              ? "Invalid email address. Please try again."
              : "Something went wrong. Please try again."}
          </div>
        )}

        <div className="flex flex-col gap-3">
          <button
            onClick={() => signIn("google", { callbackUrl: "/dashboard" })}
            className="w-full rounded-lg bg-white text-black py-3 font-medium hover:bg-neutral-200 transition"
          >
            Continue with Google
          </button>
          <button
            onClick={() => signIn("github", { callbackUrl: "/dashboard" })}
            className="w-full rounded-lg border border-neutral-700 py-3 font-medium hover:border-neutral-500 transition"
          >
            Continue with GitHub
          </button>
        </div>

        <div className="my-6 flex items-center gap-3">
          <div className="h-px flex-1 bg-neutral-800" />
          <span className="text-xs text-neutral-500 uppercase">or</span>
          <div className="h-px flex-1 bg-neutral-800" />
        </div>

        <form onSubmit={handleEmailSignIn} className="flex flex-col gap-3">
          <input
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-4 py-3 text-sm placeholder:text-neutral-500 focus:border-neutral-500 focus:outline-none"
            required
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 py-3 font-medium hover:bg-blue-500 transition disabled:opacity-50"
          >
            {loading ? "Signing in..." : "Sign in with email"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function LoginForm() {
  return (
    <Suspense>
      <LoginFormInner />
    </Suspense>
  );
}
