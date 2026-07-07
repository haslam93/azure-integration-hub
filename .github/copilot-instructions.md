# Copilot instructions — Hammad's Azure Integration Hub

This repository is a **static GitHub Pages site** (no build step) that serves as a personal
single source of truth for Azure integration services: API Management, Logic Apps, Functions,
Container Apps, Service Bus / Event Grid / Event Hubs, and App Service.

## Site structure

| File | Purpose |
|------|---------|
| `index.html` | Homepage: service cards, pattern highlights, changelog preview, automation diagram |
| `apim.html` | API Management deep dive (gateway, policy pipeline, AI Gateway/Foundry/MCP, tiers) |
| `logic-apps.html` | Logic Apps (Standard vs Consumption, connectors, B2B, agent workflows) |
| `functions.html` | Functions (triggers/bindings, Flex Consumption, Durable Functions) |
| `container-apps.html` | Container Apps (KEDA, Dapr, jobs, dynamic sessions, GPUs) |
| `service-bus.html` | Service Bus, Event Grid, Event Hubs |
| `app-service.html` | App Service (plans, slots, networking) |
| `patterns.html` | Numbered architecture patterns + official accelerators section |
| `changelog.html` | Renders `data/changelog.json` client-side |
| `assets/site.css` | All styling (Clawpilot theme variables `--cp-*`) |
| `assets/site.js` | Header/nav/footer injection, Mermaid init, changelog rendering |
| `assets/icons/` | Official Azure architecture icons (SVG) |
| `data/changelog.json` | Machine-maintained changelog (updated by weekly workflow — do not hand-edit entries) |
| `scripts/update_changelog.py` | Weekly sync script (Azure Updates RSS + Architecture Center Atom + accelerator releases) |

## Conventions (follow these when editing)

- **Every page** has the same `<head>` boilerplate: theme-detection script, `assets/site.css`,
  Mermaid 10.x from jsdelivr, `assets/site.js` (deferred). Copy from an existing page when adding one.
- **Colors**: only `var(--cp-*)` CSS variables. Never hardcode colors.
- **Diagrams**: Mermaid inside `<div class="diagram"><pre class="mermaid">…</pre><div class="caption">…</div></div>`.
  Quote node labels containing `#`, `(`, `)` or `>`. Keep diagrams simple (5–15 nodes).
- **Pattern sections** in `patterns.html`: numbered `<h2 id="kebab-slug">N · Name</h2>`, then a
  `<p><strong>Services:</strong> … <strong>Problem:</strong> …</p>`, a diagram, and an
  "Official guidance" line (`<p class="updated-stamp">`) linking the Azure Architecture Center
  source article and/or accelerator repo. Renumber subsequent patterns if inserting in the middle
  (appending at the end before the Accelerators section is preferred).
- **Nav**: pages are registered in the `NAV` array in `assets/site.js`. Adding a page = one entry there.
- Content must stay grounded in official sources: Microsoft Learn docs, Azure Architecture Center,
  Azure Updates, and Microsoft-maintained accelerator repos. Link the source next to the content.
- Tone: concise, practical, personal knowledge-base style. Not marketing copy.

## Weekly content-refresh issues

The weekly workflow (`.github/workflows/weekly-update.yml`) syncs `data/changelog.json` from three
sources and opens an issue listing new items. When resolving such an issue:

1. **Azure Updates items** → update capability lists, tier/plan tables, use cases and best
   practices on the affected service page(s). Mark retirements clearly.
2. **Architecture Center items** ("New/Updated architecture guidance") → if relevant to the
   tracked services, add a new pattern section to `patterns.html` (with Mermaid diagram and
   source link) or update the existing pattern that the guidance affects.
3. **Accelerator releases** → refresh the corresponding card text in the Accelerators section of
   `patterns.html` if capabilities changed, and any "Key references" links on service pages.
4. Do **not** manually edit `data/changelog.json` — the workflow owns it.
5. Verify: every Mermaid diagram renders (no "syntax error" text), internal links resolve,
   and pages remain consistent with the conventions above.
