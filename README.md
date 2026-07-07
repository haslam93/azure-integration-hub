# Azure Integration Hub

My personal **single source of truth** for Azure integration & app services:

- **API Management** — gateway architecture, policy pipeline, AI Gateway (Azure OpenAI / AI Foundry, MCP), tiers, self-hosted gateway
- **Logic Apps** — Standard vs Consumption, connectors, B2B/EDI, AI agent workflows
- **Azure Functions** — triggers/bindings, Flex Consumption, Durable Functions patterns
- **Container Apps** — KEDA, Dapr, revisions, jobs, dynamic sessions, serverless GPUs
- **Messaging & events** — Service Bus, Event Grid, Event Hubs
- **App Service** — plans, slots, networking, sidecars
- **Architecture patterns** — AI gateway, API-led connectivity, event-driven, async request-reply, saga, strangler fig, claim check
- **Living changelog** — filtered from the official Azure Updates feed

## How it stays current

A GitHub Actions workflow ([`.github/workflows/weekly-update.yml`](.github/workflows/weekly-update.yml)) runs every Monday:

1. `scripts/update_changelog.py` fetches the [Azure Updates RSS feed](https://www.microsoft.com/releasecommunications/api/v2/azure/rss), filters it to the tracked services, and merges new entries into `data/changelog.json` (deduplicated).
2. Changes are committed, which redeploys the GitHub Pages site — the changelog page and homepage "Latest updates" refresh automatically.
3. If there are new updates, the workflow opens a **content-refresh issue** listing them (and tries to assign it to the Copilot coding agent) so the deep-dive pages, patterns and diagrams get updated too — not just the changelog.

Run the sync manually anytime from the Actions tab (`workflow_dispatch`) or locally:

```bash
python scripts/update_changelog.py
```

## Local preview

Static site, no build step. Serve it over HTTP (the changelog fetches JSON):

```bash
python -m http.server 8080
# open http://localhost:8080
```

Diagrams are rendered client-side with [Mermaid](https://mermaid.js.org/). Light/dark theme follows your OS, with a manual toggle in the header.

> Personal knowledge base — not an official Microsoft site. Always confirm details against [Microsoft Learn](https://learn.microsoft.com/azure/).
