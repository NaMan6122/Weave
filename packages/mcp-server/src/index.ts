#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { WeaveApiClient } from "./client.js";

const WEAVE_API_URL = process.env.WEAVE_API_URL ?? "http://localhost:8000";
const WEAVE_API_KEY = process.env.WEAVE_API_KEY ?? "";

if (!WEAVE_API_KEY) {
  console.error("WEAVE_API_KEY is not set. Exiting.");
  process.exit(1);
}

const client = new WeaveApiClient(WEAVE_API_URL, WEAVE_API_KEY);

const server = new McpServer({
  name: "weave",
  version: "1.0.0",
});

server.tool(
  "get_backlink",
  "Find high-quality backlink matches for an article. Call this when writing content to discover relevant partner links to embed.",
  {
    article_text: z.string().describe("Full article text (plain text, max 50000 chars)"),
    domain: z.string().describe("Your domain (e.g. yourdomain.com)"),
    niche: z.string().optional().describe("Optional niche hint (e.g. fitness, finance, tech)"),
  },
  async (args) => {
    const result = await client.discoverLinks({
      content: args.article_text,
      url: `https://${args.domain}/draft`,
      max_results: 3,
      niche_strict: !!args.niche,
    });
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  },
);

server.tool(
  "place_link",
  "Record a link placement after embedding the partner link in your article. Deducts credits.",
  {
    your_url: z.string().describe("The URL of your article containing the link"),
    partner_url: z.string().describe("The partner URL being linked to"),
    anchor: z.string().describe("The anchor text used for the link"),
    domain: z.string().describe("Your domain (e.g. yourdomain.com)"),
  },
  async (args) => {
    const result = await client.placeLink({
      source_url: args.your_url,
      target_url: args.partner_url,
      anchor_text: args.anchor,
      placement_type: "body",
    });
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  },
);

server.tool(
  "check_credits",
  "Check credit balance, domain rating, and link stats for a domain.",
  {
    domain: z.string().describe("The domain to check (e.g. yourdomain.com)"),
  },
  async (args) => {
    const result = await client.checkBalance(args.domain);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  },
);

server.tool(
  "browse_network",
  "Browse verified member sites in the weave network. Filter by niche, DR range, language, and traffic.",
  {
    niche: z.string().optional().describe("Filter by niche (e.g. fitness, finance, tech)"),
    min_dr: z.number().int().optional().describe("Minimum Domain Rating"),
    max_dr: z.number().int().optional().describe("Maximum Domain Rating"),
    language: z.string().optional().describe("Language code (e.g. en, de, fr)"),
    min_traffic: z.number().int().optional().describe("Minimum monthly organic traffic"),
  },
  async (args) => {
    const result = await client.browseNetwork(args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  },
);

server.tool(
  "domain_status",
  "Check the verification and vetting status of a domain you own.",
  {
    domain: z.string().describe("The domain name (e.g. yourdomain.com)"),
  },
  async (args) => {
    const result = await client.domainStatus(args.domain);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  },
);

server.tool(
  "link_health",
  "Get link health status for a domain you own. Shows live/removed/broken links.",
  {
    domain: z.string().describe("The domain name (e.g. yourdomain.com)"),
    status: z.string().default("all").describe("Filter by status: all, live, placed, removed, broken, pending"),
  },
  async (args) => {
    const result = await client.linkHealth(args.domain, args.status);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  },
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("weave MCP server running on stdio");
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
