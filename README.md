# DomainCheckr MCP Server

Check domain name availability instantly using RDAP. No API key or installation required. Works as a remote MCP server.

[![Domain Checker MCP server](https://glama.ai/mcp/servers/nach-dakwale/domaincheckr-mcp/badges/card.svg)](https://glama.ai/mcp/servers/nach-dakwale/domaincheckr-mcp)

## Quick Start

This is a **remote MCP server** -- no local installation needed. Just add the URL to your MCP client.

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "domaincheckr": {
      "url": "https://domaincheckr.fly.dev/mcp"
    }
  }
}
```

Config file location:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

### Claude Code

```bash
claude mcp add domaincheckr --transport http https://domaincheckr.fly.dev/mcp
```

### Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "domaincheckr": {
      "url": "https://domaincheckr.fly.dev/mcp"
    }
  }
}
```

### Windsurf

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "domaincheckr": {
      "url": "https://domaincheckr.fly.dev/mcp"
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `check_domain` | Check if a single domain name is available for registration. Returns registrar, creation date, expiry, and nameservers for taken domains. |
| `check_domains_bulk` | Check up to 50 domain names at once. Returns per-domain results with summary counts. |
| `suggest_domains` | Generate and check domain name ideas for a keyword or business description. Creates 15 variations across .com, .io, .ai, .dev, .co and common prefixes/suffixes. |

## Example Prompts

Try asking your AI assistant:

- "Is coolstartup.com available?"
- "Check if these domains are available: acmecorp.com, acmehq.com, getacme.com"
- "Find me a domain for a pet grooming business"
- "I'm building a fintech app called PayFlow, find me a domain"

## How It Works

DomainCheckr uses the [RDAP protocol](https://about.rdap.org/) (Registration Data Access Protocol) to check domain availability in real time. RDAP is the modern replacement for WHOIS, standardized by the IETF.

- Queries Verisign RDAP for .com/.net domains
- Queries PIR RDAP for .org domains
- Falls back to rdap.org for all other TLDs
- HTTP 404 = available, HTTP 200 = taken

No scraping, no third-party APIs, no rate-limited services. Direct registry queries.

## REST API

The same service is available as a REST API for building your own integrations or ChatGPT Actions.

| Endpoint | Description |
|----------|-------------|
| `GET /check/{domain}` | Check a single domain |
| `POST /check` | Bulk check (body: `{"domains": ["a.com", "b.com"]}`, max 50) |
| `GET /suggest?keyword=fintech` | Generate and check domain ideas |
| `GET /health` | Health check |
| `GET /docs` | Interactive API documentation |
| `GET /openapi.json` | OpenAPI spec (for ChatGPT Actions) |

Base URL: `https://domaincheckr.fly.dev`

## License

MIT