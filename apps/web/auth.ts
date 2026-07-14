import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import GitHub from "next-auth/providers/github";
import Credentials from "next-auth/providers/credentials";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    GitHub({
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
    }),
    Credentials({
      name: "Email",
      credentials: {
        email: { label: "Email", type: "email" },
      },
      async authorize(credentials) {
        const email = credentials?.email as string;
        if (!email) return null;

        try {
          const res = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email }),
          });

          if (!res.ok) return null;

          const data = await res.json();
          return {
            id: data.user.id,
            email: data.user.email,
            name: data.user.name,
            image: data.user.avatar_url,
            backendToken: data.token,
          };
        } catch {
          return null;
        }
      },
    }),
  ],
  session: { strategy: "jwt" },
  pages: { signIn: "/login" },
  secret: process.env.NEXTAUTH_SECRET,
  callbacks: {
    async jwt({ token, user, account }) {
      // On initial sign-in
      if (user) {
        // Credentials provider already has the backend token
        if ((user as any).backendToken) {
          token.backendToken = (user as any).backendToken;
          token.userId = user.id;
          return token;
        }

        // OAuth providers: call backend to register/login
        if (account && (account.provider === "google" || account.provider === "github")) {
          try {
            const res = await fetch(
              `${BACKEND_URL}/api/v1/auth/oauth/callback`,
              {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  email: user.email,
                  name: user.name,
                  avatar_url: user.image,
                  provider: account.provider,
                }),
              },
            );

            if (res.ok) {
              const data = await res.json();
              token.backendToken = data.token;
              token.userId = data.user.id;
            }
          } catch {
            // Backend unavailable — session will lack a backend token
          }
        }
      }
      return token;
    },
    async session({ session, token }) {
      session.backendToken = token.backendToken as string;
      session.user.id = token.userId as string;
      return session;
    },
  },
});
