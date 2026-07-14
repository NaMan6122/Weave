export class WeaveApiClient {
  private baseUrl: string;
  private apiKey: string;

  constructor(baseUrl: string, apiKey: string) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.apiKey = apiKey;
  }

  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.apiKey}`,
        ...options?.headers,
      },
    });
    if (!res.ok) {
      let detail = "";
      try {
        const body = await res.json();
        detail = body.detail ?? body.message ?? JSON.stringify(body);
      } catch {
        detail = res.statusText;
      }
      throw new Error(`Weave API error ${res.status}: ${detail}`);
    }
    return res.json() as Promise<T>;
  }

  async discoverLinks(params: {
    content: string;
    url: string;
    max_results?: number;
    niche_strict?: boolean;
    min_dr?: number;
    exclude_domains?: string[];
  }): Promise<unknown> {
    return this.request("/api/v1/matching/discover", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async placeLink(params: {
    source_url: string;
    target_url: string;
    anchor_text: string;
    placement_type?: string;
  }): Promise<unknown> {
    return this.request("/api/v1/matching/place", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async checkBalance(domain: string): Promise<unknown> {
    return this.request(`/api/v1/credits/balance/by-name/${encodeURIComponent(domain)}`);
  }

  async domainStatus(domain: string): Promise<unknown> {
    return this.request(`/api/v1/domains/by-name/${encodeURIComponent(domain)}/status`);
  }

  async linkHealth(domain: string, statusFilter: string): Promise<unknown> {
    return this.request(
      `/api/v1/links/health?domain=${encodeURIComponent(domain)}&status=${statusFilter}`,
    );
  }

  async browseNetwork(params: {
    niche?: string;
    min_dr?: number;
    max_dr?: number;
    language?: string;
    min_traffic?: number;
  }): Promise<unknown> {
    const query = new URLSearchParams();
    if (params.niche) query.set("niche", params.niche);
    if (params.min_dr != null) query.set("min_dr", String(params.min_dr));
    if (params.max_dr != null) query.set("max_dr", String(params.max_dr));
    if (params.language) query.set("language", params.language);
    if (params.min_traffic != null) query.set("min_traffic", String(params.min_traffic));
    const qs = query.toString();
    return this.request(`/api/v1/network/${qs ? `?${qs}` : ""}`);
  }
}
