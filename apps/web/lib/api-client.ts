export interface Domain {
  id: string;
  domain: string;
  status: "active" | "pending" | "rejected" | "suspended";
  wts: number;
  dr: number;
  da: number;
  spam_score: number;
  domain_age: number;
  organic_traffic: number;
  niche: string;
  language: string;
  verified: boolean;
  verification_token: string;
  created_at: string;
}

export interface Link {
  id: string;
  source_url: string;
  target_url: string;
  anchor_text: string;
  match_score: number;
  credits: number;
  status: "live" | "pending" | "removed" | "broken";
  created_at: string;
}

export interface CreditBalance {
  domain_id: string;
  balance: number;
  lifetime_earned: number;
  lifetime_spent: number;
}

export interface CreditTransaction {
  id: string;
  domain_id: string;
  type: "earned" | "spent" | "reversed" | "bonus" | "expired";
  amount: number;
  description: string;
  link_id: string | null;
  created_at: string;
}

export interface ApiKey {
  id: string;
  key_prefix: string;
  label: string;
  created_at: string;
}

export interface DiscoverLinksRequest {
  domain_id: string;
  target_url: string;
  anchor_text?: string;
  niche?: string;
}

export interface PlaceLinkRequest {
  source_domain_id: string;
  target_url: string;
  anchor_text: string;
  source_page_url: string;
}

export interface CreateDomainRequest {
  domain: string;
  niche?: string;
  language?: string;
}

export interface NetworkSite {
  domain: string;
  niche: string | null;
  dr: number;
  monthly_traffic: number;
  language: string;
  domain_age_months: number;
  wts: number;
}

export interface NetworkBrowseResponse {
  sites: NetworkSite[];
  total: number;
  page: number;
  page_size: number;
}

export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  read: boolean;
  metadata: Record<string, string>;
  created_at: string;
}

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export class WeaveClient {
  private baseUrl: string;
  private token?: string;

  constructor(baseUrl?: string, token?: string) {
    this.baseUrl =
      baseUrl ||
      process.env.NEXT_PUBLIC_API_URL ||
      "http://localhost:8000";
    this.token = token;
  }

  static authenticated(token: string, baseUrl?: string): WeaveClient {
    return new WeaveClient(baseUrl, token);
  }

  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options?.headers as Record<string, string>),
    };
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }
    const res = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers,
    });
    if (!res.ok) {
      const body = await res.text();
      let message: string;
      try {
        message = JSON.parse(body).detail || body;
      } catch {
        message = body;
      }
      throw new ApiError(res.status, message);
    }
    return res.json() as Promise<T>;
  }

  // Domains
  async listDomains(): Promise<{ domains: Domain[]; total: number }> {
    return this.request("/api/v1/domains/");
  }

  async createDomain(data: CreateDomainRequest): Promise<Domain> {
    return this.request("/api/v1/domains", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getDomain(id: string): Promise<Domain> {
    return this.request(`/api/v1/domains/${id}`);
  }

  async verifyDomain(
    id: string,
    method: "dns" | "meta" | "file",
  ): Promise<Domain> {
    return this.request(`/api/v1/domains/${id}/verify`, {
      method: "POST",
      body: JSON.stringify({ method }),
    });
  }

  async vetDomain(id: string): Promise<Domain> {
    return this.request(`/api/v1/domains/${id}/vet`, { method: "POST" });
  }

  async deleteDomain(id: string): Promise<void> {
    await this.request(`/api/v1/domains/${id}`, { method: "DELETE" });
  }

  // Credits
  async getBalance(domainId: string): Promise<CreditBalance> {
    return this.request(`/api/v1/credits/balance/${domainId}`);
  }

  async getCreditHistory(
    domainId: string,
    limit = 50,
    offset = 0,
  ): Promise<{ transactions: CreditTransaction[]; total: number }> {
    return this.request(
      `/api/v1/credits/history/${domainId}?limit=${limit}&offset=${offset}`,
    );
  }

  // Links
  async discoverLinks(
    data: DiscoverLinksRequest,
  ): Promise<{ suggestions: Link[]; credit_balance: number }> {
    return this.request("/api/v1/matching/discover", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async placeLink(data: PlaceLinkRequest): Promise<Link> {
    return this.request("/api/v1/matching/place", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async listLinks(status?: string): Promise<Link[]> {
    const query = status ? `?status=${status}` : "";
    return this.request(`/api/v1/links/${query}`);
  }

  async getLink(id: string): Promise<Link> {
    return this.request(`/api/v1/links/${id}`);
  }

  async validateLink(id: string): Promise<Link> {
    return this.request(`/api/v1/links/${id}/validate`, { method: "POST" });
  }

  // Auth
  async getMe(): Promise<{ id: string; email: string; name: string; avatar_url: string; plan: string }> {
    return this.request("/api/v1/auth/me");
  }

  async updateProfile(name: string): Promise<{ id: string; email: string; name: string; plan: string }> {
    return this.request("/api/v1/auth/profile", {
      method: "PUT",
      body: JSON.stringify({ name }),
    });
  }

  async deleteAccount(emailConfirmation: string): Promise<{ message: string }> {
    return this.request("/api/v1/auth/account", {
      method: "DELETE",
      body: JSON.stringify({ email_confirmation: emailConfirmation }),
    });
  }

  async generateApiKey(): Promise<{ key: string }> {
    return this.request("/api/v1/auth/api-keys", { method: "POST" });
  }

  async getApiKeyInfo(): Promise<{ masked_key: string; has_key: boolean }> {
    return this.request("/api/v1/auth/api-keys");
  }

  async revokeApiKey(): Promise<void> {
    await this.request("/api/v1/auth/api-keys", { method: "DELETE" });
  }

  // Network
  async browseNetwork(params?: {
    niche?: string;
    min_dr?: number;
    max_dr?: number;
    language?: string;
    min_traffic?: number;
    page?: number;
    page_size?: number;
  }): Promise<NetworkBrowseResponse> {
    const query = new URLSearchParams();
    if (params?.niche) query.set("niche", params.niche);
    if (params?.min_dr != null) query.set("min_dr", String(params.min_dr));
    if (params?.max_dr != null) query.set("max_dr", String(params.max_dr));
    if (params?.language) query.set("language", params.language);
    if (params?.min_traffic != null) query.set("min_traffic", String(params.min_traffic));
    if (params?.page != null) query.set("page", String(params.page));
    if (params?.page_size != null) query.set("page_size", String(params.page_size));
    const qs = query.toString();
    return this.request(`/api/v1/network/${qs ? `?${qs}` : ""}`);
  }

  // Notifications
  async getNotifications(): Promise<{ notifications: Notification[]; unread_count: number }> {
    return this.request("/api/v1/notifications/");
  }

  async markNotificationRead(id: string): Promise<{ id: string; read: boolean }> {
    return this.request(`/api/v1/notifications/${id}/read`, { method: "POST" });
  }

  async markAllNotificationsRead(): Promise<{ marked: number }> {
    return this.request("/api/v1/notifications/read-all", { method: "POST" });
  }

  // Analytics
  async getMetrics(domainId: string): Promise<{ history: Array<{ recorded_at: string; dr: number | null; da: number | null; wts: number | null; organic_traffic: number | null; spam_score: number | null }> }> {
    return this.request(`/api/v1/analytics/metrics/${domainId}`);
  }

  async getLinkSeries(domainId: string): Promise<{ series: Array<{ date: string; new_that_week: number; cumulative: number }> }> {
    return this.request(`/api/v1/analytics/links/${domainId}`);
  }

  async getCreditSeries(domainId: string): Promise<{ series: Array<{ week: string; earned: number; spent: number }> }> {
    return this.request(`/api/v1/analytics/credits/${domainId}`);
  }
}

export const weaveClient = new WeaveClient();
