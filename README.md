# Hammad's Azure Integration Hub

My personal **single source of truth** for Azure integration & app services (not an official Microsoft site):

- **API Management** — gateway architecture, policy pipeline, AI Gateway (Azure OpenAI / AI Foundry, MCP), tiers, self-hosted gateway
- **Logic Apps** — Standard vs Consumption, connectors, B2B/EDI, AI agent workflows
- **Azure Functions** — triggers/bindings, Flex Consumption, Durable Functions patterns
- **Container Apps** — KEDA, Dapr, revisions, jobs, dynamic sessions, serverless GPUs
- **Messaging & events** — Service Bus, Event Grid, Event Hubs
- **App Service** — plans, slots, networking, sidecars
- **Architecture patterns** — AI gateway, API-led connectivity, event-driven, async request-reply, saga, strangler fig, claim check
- **Living changelog** — filtered from the official Azure Updates feed

## How it stays current

A GitHub Actions workflow ([`.github/workflows/weekly-update.yml`](.github/workflows/weekly-update.yml)) runs every Monday and pulls **three official sources**:

1. **[Azure Updates RSS](https://www.microsoft.com/releasecommunications/api/v2/azure/rss)** — service capability announcements (GA / preview / retirements)
2. **[Azure Architecture Center what's-new feed](https://learn.microsoft.com/azure/architecture/changelog)** — new and updated patterns, guides and reference architectures
3. **Accelerator repo releases** — the official landing-zone / AI gateway accelerators (APIM, Integration Services, Container Apps, App Service, AI-Gateway labs, AI Hub Gateway, AI Landing Zones, Logic Apps)

`scripts/update_changelog.py` filters everything to the tracked services, merges new entries into `data/changelog.json` (deduplicated), and commits — which redeploys the GitHub Pages site so the changelog and homepage refresh automatically.

If there are new items, the workflow also opens a **content-refresh issue** listing them (and tries to assign it to the Copilot coding agent, guided by [`.github/copilot-instructions.md`](.github/copilot-instructions.md)) so the deep-dive pages, patterns and diagrams get updated too — not just the changelog.

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
