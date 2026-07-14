export type LinkStatus =
  | "pending"
  | "matched"
  | "placed"
  | "verified"
  | "removed"
  | "expired";

export interface MatchScore {
  overall: number;
  topicalRelevance: number;
  domainAuthority: number;
  contentQuality: number;
  nicheMatch: number;
}

export interface AnchorSuggestion {
  text: string;
  type: "exact" | "partial" | "branded" | "natural";
  score: number;
}

export interface LinkSuggestion {
  linkId: string;
  sourcePageUrl: string;
  sourceDomain: string;
  targetPageUrl: string;
  targetDomain: string;
  matchScore: MatchScore;
  anchorSuggestions: AnchorSuggestion[];
  creditsRequired: number;
  creditsEarned: number;
  placementType: string;
}

export interface Link {
  id: string;
  sourcePageId: string;
  targetPageId: string;
  sourceDomainId: string;
  targetDomainId: string;
  anchorText: string | null;
  matchScore: number | null;
  matchBreakdown: MatchScore | null;
  placementType: string | null;
  creditsEarned: number | null;
  creditsSpent: number | null;
  triangleId: string | null;
  status: LinkStatus;
  placedAt: string | null;
  verifiedAt: string | null;
  removedAt: string | null;
  slaExpiresAt: string | null;
  createdAt: string;
  updatedAt: string;
}
