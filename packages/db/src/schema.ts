import {
  pgTable,
  uuid,
  text,
  boolean,
  timestamp,
  integer,
  decimal,
  jsonb,
} from "drizzle-orm/pg-core";

// ── Users ──────────────────────────────────────────────────────────────────────

export const users = pgTable("users", {
  id: uuid("id").primaryKey().defaultRandom(),
  email: text("email").notNull().unique(),
  name: text("name"),
  avatarUrl: text("avatar_url"),
  plan: text("plan").notNull().default("free"),
  stripeCustomerId: text("stripe_customer_id"),
  apiKey: text("api_key").unique(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
});

// ── Domains ────────────────────────────────────────────────────────────────────

export const domains = pgTable("domains", {
  id: uuid("id").primaryKey().defaultRandom(),
  userId: uuid("user_id")
    .notNull()
    .references(() => users.id),
  domain: text("domain").notNull().unique(),
  verified: boolean("verified").notNull().default(false),
  verificationMethod: text("verification_method"),
  verificationToken: text("verification_token"),

  // Metrics
  wts: integer("wts"),
  dr: integer("dr"),
  da: integer("da"),
  spamScore: decimal("spam_score"),
  domainAgeDays: integer("domain_age_days"),
  organicTraffic: integer("organic_traffic"),
  contentQuality: decimal("content_quality"),

  // PBN detection
  isPbn: boolean("is_pbn"),

  // Vetting
  vettedAt: timestamp("vetted_at", { withTimezone: true }),
  vettingStatus: text("vetting_status").notNull().default("pending"),
  rejectionReason: text("rejection_reason"),

  // Classification
  niche: text("niche"),
  language: text("language").notNull().default("en"),
  blocklist: jsonb("blocklist"),
  nicheStrict: boolean("niche_strict").default(false),

  status: text("status").notNull().default("active"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
});

// ── Pages ──────────────────────────────────────────────────────────────────────

export const pages = pgTable("pages", {
  id: uuid("id").primaryKey().defaultRandom(),
  domainId: uuid("domain_id")
    .notNull()
    .references(() => domains.id),
  url: text("url").notNull().unique(),
  title: text("title"),
  contentHash: text("content_hash"),
  niche: text("niche"),
  language: text("language"),
  wordCount: integer("word_count"),
  embeddingId: text("embedding_id"),
  lastCrawledAt: timestamp("last_crawled_at", { withTimezone: true }),
  status: text("status").notNull().default("active"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
});

// ── Credit Accounts ────────────────────────────────────────────────────────────

export const creditAccounts = pgTable("credit_accounts", {
  id: uuid("id").primaryKey().defaultRandom(),
  domainId: uuid("domain_id")
    .notNull()
    .unique()
    .references(() => domains.id),
  balance: decimal("balance").notNull().default("0"),
  lifetimeEarned: decimal("lifetime_earned").notNull().default("0"),
  lifetimeSpent: decimal("lifetime_spent").notNull().default("0"),
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
});

// ── Credit Transactions ────────────────────────────────────────────────────────

export const creditTransactions = pgTable("credit_transactions", {
  id: uuid("id").primaryKey().defaultRandom(),
  accountId: uuid("account_id")
    .notNull()
    .references(() => creditAccounts.id),
  type: text("type").notNull(),
  amount: decimal("amount").notNull(),
  linkId: uuid("link_id").references(() => links.id),
  description: text("description"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

// ── Links ──────────────────────────────────────────────────────────────────────

export const links = pgTable("links", {
  id: uuid("id").primaryKey().defaultRandom(),
  sourcePageId: uuid("source_page_id")
    .notNull()
    .references(() => pages.id),
  targetPageId: uuid("target_page_id")
    .notNull()
    .references(() => pages.id),
  sourceDomainId: uuid("source_domain_id")
    .notNull()
    .references(() => domains.id),
  targetDomainId: uuid("target_domain_id")
    .notNull()
    .references(() => domains.id),
  anchorText: text("anchor_text"),
  matchScore: decimal("match_score"),
  matchBreakdown: jsonb("match_breakdown"),
  placementType: text("placement_type"),
  creditsEarned: decimal("credits_earned"),
  creditsSpent: decimal("credits_spent"),
  triangleId: uuid("triangle_id"),
  status: text("status").notNull().default("pending"),
  placedAt: timestamp("placed_at", { withTimezone: true }),
  verifiedAt: timestamp("verified_at", { withTimezone: true }),
  removedAt: timestamp("removed_at", { withTimezone: true }),
  slaExpiresAt: timestamp("sla_expires_at", { withTimezone: true }),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
});

// ── Triangles ──────────────────────────────────────────────────────────────────

export const triangles = pgTable("triangles", {
  id: uuid("id").primaryKey().defaultRandom(),
  domainAId: uuid("domain_a_id")
    .notNull()
    .references(() => domains.id),
  domainBId: uuid("domain_b_id")
    .notNull()
    .references(() => domains.id),
  domainCId: uuid("domain_c_id")
    .notNull()
    .references(() => domains.id),
  linkAbId: uuid("link_ab_id").references(() => links.id),
  linkBcId: uuid("link_bc_id").references(() => links.id),
  linkCaId: uuid("link_ca_id").references(() => links.id),
  status: text("status").notNull().default("forming"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

// ── Webhooks ───────────────────────────────────────────────────────────────────

export const webhooks = pgTable("webhooks", {
  id: uuid("id").primaryKey().defaultRandom(),
  userId: uuid("user_id")
    .notNull()
    .references(() => users.id),
  url: text("url").notNull(),
  events: jsonb("events").notNull(),
  secret: text("secret").notNull(),
  active: boolean("active").notNull().default(true),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

// ── Domain Metrics History ─────────────────────────────────────────────────────

export const domainMetricsHistory = pgTable("domain_metrics_history", {
  id: uuid("id").primaryKey().defaultRandom(),
  domainId: uuid("domain_id")
    .notNull()
    .references(() => domains.id),
  dr: integer("dr"),
  da: integer("da"),
  wts: integer("wts"),
  organicTraffic: integer("organic_traffic"),
  spamScore: decimal("spam_score"),
  recordedAt: timestamp("recorded_at", { withTimezone: true }).notNull().defaultNow(),
});
