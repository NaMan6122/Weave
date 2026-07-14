# spec-005-v1 — MCP Server (Tool Schema & Integration)

**Version:** 1
**Date:** 2026-05-23
**Status:** Draft — pending human approval (Gate G1)
**PRD Refs:** FR-4.1, FR-4.2, FR-4.3, FR-4.4, FR-4.5, FR-4.6
**TDD Refs:** §4.1 (MCP Server), §6 (MCP Protocol Specification)

---

## 1. Overview

The MCP server is **implemented** in `packages/mcp-server/src/`:
- `index.ts` — 4 tools registered: `get_backlink`, `place_link`, `check_credits`, `browse_network`
- `client.ts` — HTTP client with 6 methods (includes `domainStatus` and `linkHealth` not yet wired to tools)

**This spec fills gaps:**
- A. Add missing tools: `domain_status` and `link_health`
- B. Rename tools to match PRD convention (`weave_` prefix)
- C. Error handling and user-friendly error messages
- D. Rate limiting awareness (pass through 429 responses gracefully)
- E. MCP server configuration and setup documentation
- F. npm package publishing prep

---

## 2. Tool Naming Convention

### 2.1 Decision: Keep Short Names (No `weave_` Prefix)

MCP tool names should be concise since the server is already namespaced as "weave". The PRD uses `weave_` prefix for documentation clarity, but in practice:
- Tool names are already scoped to the server
- Shorter names reduce token usage in AI context

**Final tool names:**

| Current | Final | PRD Equivalent |
|---------|-------|----------------|
| `get_backlink` | `get_backlink` | `weave_discover_links` |
| `place_link` | `place_link` | `weave_place_link` |
| `check_credits` | `check_credits` | `weave_check_balance` |
| _(missing)_ | `domain_status` | `weave_domain_status` |
| _(missing)_ | `link_health` | `weave_link_health` |
| `browse_network` | `browse_network` | _(bonus, not in PRD)_ |

---

## 3. Gap A — Missing Tools

### 3.1 `domain_status`

```typescript
server.tool(
  "domain_status",
  "Check your domain's Weave Trust Score, DR, vetting status, and verification state.",
  {
    domain: z.string().describe("Your domain (e.g. yourdomain.com)"),
  },
  async (args) => {
    const result = await client.domainStatus(args.domain);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  },
);
```

### 3.2 `link_health`

```typescript
server.tool(
  "link_health",
  "Check the status of your placed links (live, removed, broken). Filter by status.",
  {
    domain: z.string().describe("Your domain (e.g. yourdomain.com)"),
    status: z.enum(["all", "live", "placed", "removed", "broken"]).default("all")
      .describe("Filter by link status"),
  },
  async (args) => {
    const result = await client.linkHealth(args.domain, args.status);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  },
);
```

### 3.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-3.1 | `domain_status` returns WTS, DR, DA, vetting_status, verified |
| AC-3.2 | `link_health` returns list of links filtered by status |
| AC-3.3 | Both tools return meaningful error on 404 (domain not found) |

---

## 4. Gap C — Error Handling

### 4.1 Current Issue

The client throws a generic `Error` on non-2xx responses. AI agents need structured, actionable error messages.

### 4.2 Improved Error Handling

```typescript
private async request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${this.baseUrl}${path}`, { ... });

  if (!res.ok) {
    const body = await res.text();
    let detail = body;
    try {
      const json = JSON.parse(body);
      detail = json.detail || json.message || body;
    } catch {}

    if (res.status === 401) throw new WeaveError("Invalid API key. Check WEAVE_API_KEY.", 401);
    if (res.status === 403) throw new WeaveError(detail, 403);
    if (res.status === 404) throw new WeaveError(detail, 404);
    if (res.status === 429) throw new WeaveError("Rate limit exceeded. Please wait and retry.", 429);
    throw new WeaveError(`API error: ${detail}`, res.status);
  }
  return res.json() as Promise<T>;
}
```

### 4.3 Tool-Level Error Wrapping

Each tool should catch errors and return them as text content (not throw), so the AI agent sees a useful message:

```typescript
async (args) => {
  try {
    const result = await client.discoverLinks(...);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  } catch (err) {
    const msg = err instanceof WeaveError ? err.message : "Unknown error";
    return { content: [{ type: "text", text: `Error: ${msg}` }], isError: true };
  }
}
```

### 4.4 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-4.1 | Invalid API key returns clear error message (not stack trace) |
| AC-4.2 | 429 rate limit returns "Rate limit exceeded" with no crash |
| AC-4.3 | 404 domain not found returns actionable message |
| AC-4.4 | Tool errors use `isError: true` in MCP response |

---

## 5. Gap D — Rate Limiting Awareness

### 5.1 Behavior

The MCP server itself doesn't rate-limit — the Core API does (per API key). The MCP server should:
- Pass through 429 responses as user-friendly errors (done via §4)
- Include `X-RateLimit-Remaining` in response metadata if available (Phase 2)

No client-side throttling needed for MVP.

---

## 6. Gap E — Setup & Configuration Documentation

### 6.1 Claude Desktop Configuration

```json
{
  "mcpServers": {
    "weave": {
      "command": "npx",
      "args": ["@weave/mcp-server"],
      "env": {
        "WEAVE_API_KEY": "wv_live_your_key_here",
        "WEAVE_API_URL": "https://api.getweave.io"
      }
    }
  }
}
```

### 6.2 Claude Code Configuration

```bash
claude mcp add weave -- npx @weave/mcp-server
# Then set env vars in .claude.json or shell
export WEAVE_API_KEY=wv_live_your_key_here
export WEAVE_API_URL=https://api.getweave.io
```

### 6.3 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WEAVE_API_KEY` | Yes | — | API key from dashboard |
| `WEAVE_API_URL` | No | `http://localhost:8000` | Core API URL |

### 6.4 README.md Update

Create/update `packages/mcp-server/README.md` with:
- What Weave is (1 paragraph)
- Available tools (table with name + description)
- Setup instructions for Claude Desktop, Claude Code, and generic MCP clients
- Environment variables
- Troubleshooting (common errors)

---

## 7. Gap F — npm Package Prep

### 7.1 package.json Updates

```json
{
  "name": "@weave/mcp-server",
  "version": "0.1.0",
  "description": "Weave MCP server — AI-native backlink exchange",
  "bin": { "weave-mcp": "./dist/index.js" },
  "main": "./dist/index.js",
  "type": "module",
  "files": ["dist"],
  "scripts": {
    "build": "tsc",
    "dev": "tsx src/index.ts",
    "prepublishOnly": "npm run build"
  },
  "keywords": ["mcp", "backlinks", "seo", "ai", "claude"]
}
```

### 7.2 Shebang

`src/index.ts` already has `#!/usr/bin/env node` — good.

### 7.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-7.1 | `npx @weave/mcp-server` works with WEAVE_API_KEY set |
| AC-7.2 | Package builds cleanly with `tsc` |
| AC-7.3 | All 6 tools respond without crashing when backend is unavailable (error message returned) |

---

## 8. Files to Modify/Create

| File | Change |
|------|--------|
| `packages/mcp-server/src/index.ts` | Add domain_status + link_health tools, error wrapping |
| `packages/mcp-server/src/client.ts` | Improve error handling with WeaveError class |
| `packages/mcp-server/src/errors.ts` | Create (WeaveError class) |
| `packages/mcp-server/package.json` | Add bin, files, scripts |
| `packages/mcp-server/README.md` | Create (setup + usage docs) |
| `packages/mcp-server/tsconfig.json` | Ensure outDir=dist, declaration=true |

---

## 9. Out of Scope

- SSE transport (hosted MCP endpoint) — Phase 2
- Streaming responses for large result sets — Phase 2
- Multi-agent support (multiple API keys per session) — Phase 3
- Tool-level rate limiting in MCP server
