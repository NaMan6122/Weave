export type DomainVettingStatus = "pending" | "approved" | "rejected";
export type DomainStatus = "active" | "suspended" | "removed";

export interface Domain {
  id: string;
  userId: string;
  domain: string;
  verified: boolean;
  verificationMethod: string | null;
  verificationToken: string | null;

  // Metrics
  wts: number | null;
  dr: number | null;
  da: number | null;
  spamScore: number | null;
  domainAgeDays: number | null;
  organicTraffic: number | null;
  contentQuality: number | null;

  // PBN detection
  isPbn: boolean | null;

  // Vetting
  vettedAt: string | null;
  vettingStatus: DomainVettingStatus;
  rejectionReason: string | null;

  // Classification
  niche: string | null;
  language: string;
  blocklist: string[] | null;
  nicheStrict: boolean;

  status: DomainStatus;
  createdAt: string;
  updatedAt: string;
}
