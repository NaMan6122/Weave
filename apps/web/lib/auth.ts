import { auth } from "@/auth";

export async function getSession() {
  return auth();
}

export async function getBackendToken(): Promise<string | null> {
  const session = await auth();
  return session?.backendToken ?? null;
}
