"use client";

import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Domain, WeaveClient } from "@/lib/api-client";

interface DomainContextValue {
  domains: Domain[];
  selectedDomainId: string | null;
  selectedDomain: Domain | null;
  selectDomain: (id: string | null) => void;
  loading: boolean;
}

const DomainContext = createContext<DomainContextValue>({
  domains: [],
  selectedDomainId: null,
  selectedDomain: null,
  selectDomain: () => {},
  loading: true,
});

export function useDomainContext() {
  return useContext(DomainContext);
}

export function DomainProvider({ children, token }: { children: ReactNode; token: string }) {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [selectedDomainId, setSelectedDomainId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const client = WeaveClient.authenticated(token);
    client.listDomains()
      .then((res) => {
        setDomains(res.domains);
        const urlDomain = searchParams.get("domain");
        if (urlDomain && res.domains.some((d) => d.id === urlDomain)) {
          setSelectedDomainId(urlDomain);
        } else if (res.domains.length > 0) {
          setSelectedDomainId(res.domains[0].id);
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [token]);

  const selectDomain = useCallback((id: string | null) => {
    setSelectedDomainId(id);
    const params = new URLSearchParams(searchParams.toString());
    if (id) {
      params.set("domain", id);
    } else {
      params.delete("domain");
    }
    router.push(`?${params.toString()}`, { scroll: false });
  }, [router, searchParams]);

  const selectedDomain = domains.find((d) => d.id === selectedDomainId) || null;

  return (
    <DomainContext.Provider value={{ domains, selectedDomainId, selectedDomain, selectDomain, loading }}>
      {children}
    </DomainContext.Provider>
  );
}
