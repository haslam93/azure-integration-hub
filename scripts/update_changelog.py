#!/usr/bin/env python3
"""Refresh data/changelog.json from official sources.

Sources monitored:
  1. Azure Updates RSS            — service capability announcements (GA/preview/retirements)
  2. Azure Architecture Center    — new/updated patterns, guides and reference architectures (Atom)
  3. Accelerator GitHub repos     — releases of the official landing-zone / gateway accelerators

New entries are merged into data/changelog.json (deduplicated), and a markdown
summary is written to new_updates.md so the weekly workflow can open a
content-refresh issue instructing a full site update (service pages, patterns,
diagrams), not just the changelog.

Usage: python scripts/update_changelog.py
"""

import html
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

AZURE_UPDATES_RSS = "https://www.microsoft.com/releasecommunications/api/v2/azure/rss"
ARCH_CENTER_ATOM = "https://learn.microsoft.com/azure/architecture/feed.atom"
ACCELERATOR_REPOS = [
    "Azure/apim-landing-zone-accelerator",
    "Azure/Integration-Services-Landing-Zone-Accelerator",
    "Azure/aca-landing-zone-accelerator",
    "Azure/appservice-landing-zone-accelerator",
    "Azure-Samples/AI-Gateway",
    "Azure-Samples/ai-hub-gateway-solution-accelerator",
    "Azure/AI-Landing-Zones",
    "Azure/logicapps",
]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(ROOT, "data", "changelog.json")
SUMMARY_FILE = os.path.join(ROOT, "new_updates.md")
MAX_ENTRIES = 500
UA = "Mozilla/5.0 (compatible; azure-integration-hub-sync/1.0; +https://github.com/haslam93/azure-integration-hub)"
ATOM_NS = "{http://www.w3.org/2005/Atom}"

# service key -> regex matched against title + categories + description
SERVICE_PATTERNS = {
    "apim": r"api management|apim\b|api center|api gateway",
    "logic-apps": r"logic apps?",
    "functions": r"azure functions|durable functions|functions runtime|flex consumption",
    "container-apps": r"container apps",
    "service-bus": r"service bus",
    "event-grid": r"event grid",
    "event-hubs": r"event hubs?",
    "app-service": r"app service(?! environment for power)",
    "ai-foundry": r"ai foundry|azure openai|foundry agent|model inference",
}

# Architecture Center entries also match on integration-relevant themes
ARCH_THEME = (
    r"\bpattern\b|integration|messag|event-driven|serverless|gateway|microservice"
    r"|\bapis?\b|queue|saga|agent|rag\b|workflow|web app"
)


def detect_services(text):
    lowered = text.lower()
    return [k for k, p in SERVICE_PATTERNS.items() if re.search(p, lowered)]


def detect_status(text):
    lowered = text.lower()
    if "retire" in lowered or "deprecat" in lowered:
        return "retirement"
    if "general availability" in lowered or "generally available" in lowered or lowered.startswith("ga:"):
        return "ga"
    if "public preview" in lowered or "in preview" in lowered or lowered.startswith("preview"):
        return "preview"
    return ""


def clean_html(raw):
    text = re.sub(r"<[^>]+>", " ", raw or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def truncate(text, limit=400):
    if len(text) <= limit:
        return text
    return text[: limit - 3].rsplit(" ", 1)[0] + "…"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


# ---------------------------------------------------------------- sources

def azure_updates_items():
    root = ET.fromstring(fetch(AZURE_UPDATES_RSS))
    items = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or link or title).strip()
        description = clean_html(item.findtext("description") or "")
        categories = [c.text or "" for c in item.findall("category")]
        try:
            date = parsedate_to_datetime(item.findtext("pubDate")).astimezone(timezone.utc)
        except Exception:
            date = datetime.now(timezone.utc)

        services = detect_services(" ".join([title, description] + categories))
        if not services:
            continue
        items.append(
            {
                "id": guid,
                "date": date.strftime("%Y-%m-%d"),
                "title": title,
                "summary": truncate(description),
                "link": link,
                "services": services,
                "status": detect_status(title + " " + description),
                "source": "azure-updates",
            }
        )
    return items


def arch_center_items():
    root = ET.fromstring(fetch(ARCH_CENTER_ATOM))
    items = []
    for entry in root.iter(f"{ATOM_NS}entry"):
        title = clean_html(entry.findtext(f"{ATOM_NS}title") or "")
        link_el = entry.find(f"{ATOM_NS}link")
        link = (link_el.get("href") if link_el is not None else "") or (entry.findtext(f"{ATOM_NS}id") or "")
        summary = clean_html(entry.findtext(f"{ATOM_NS}summary") or "")
        cat_el = entry.find(f"{ATOM_NS}category")
        kind = (cat_el.get("term") if cat_el is not None else "") or "updated"
        updated = entry.findtext(f"{ATOM_NS}updated") or ""
        try:
            date = datetime.fromisoformat(updated.replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            date = datetime.now(timezone.utc)

        haystack = f"{title} {summary} {link}"
        services = detect_services(haystack)
        relevant = bool(services) or re.search(ARCH_THEME, haystack.lower())
        if not relevant:
            continue

        label = "New" if kind == "new" else "Updated"
        items.append(
            {
                "id": link,
                "date": date.strftime("%Y-%m-%d"),
                "title": f"{label} architecture guidance: {title}",
                "summary": truncate(summary),
                "link": link,
                "services": services or ["architecture"],
                "status": "",
                "source": "architecture-center",
            }
        )
    return items


def accelerator_items():
    items = []
    for repo in ACCELERATOR_REPOS:
        try:
            root = ET.fromstring(fetch(f"https://github.com/{repo}/releases.atom"))
        except Exception as exc:
            print(f"WARN: could not fetch releases for {repo}: {exc}", file=sys.stderr)
            continue
        for entry in root.iter(f"{ATOM_NS}entry"):
            title = clean_html(entry.findtext(f"{ATOM_NS}title") or "")
            link_el = entry.find(f"{ATOM_NS}link")
            link = link_el.get("href") if link_el is not None else f"https://github.com/{repo}/releases"
            updated = entry.findtext(f"{ATOM_NS}updated") or ""
            try:
                date = datetime.fromisoformat(updated.replace("Z", "+00:00")).astimezone(timezone.utc)
            except Exception:
                date = datetime.now(timezone.utc)
            services = detect_services(f"{repo} {title}") or ["architecture"]
            items.append(
                {
                    "id": link,
                    "date": date.strftime("%Y-%m-%d"),
                    "title": f"Accelerator release: {repo.split('/')[1]} — {title}",
                    "summary": f"New release in the official {repo} accelerator repository.",
                    "link": link,
                    "services": services,
                    "status": "",
                    "source": "accelerator",
                }
            )
    return items


# ---------------------------------------------------------------- merge

def load_existing():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"lastUpdated": None, "entries": []}


SOURCE_LABEL = {
    "azure-updates": "Azure Updates",
    "architecture-center": "Architecture Center",
    "accelerator": "Accelerator release",
    "seed": "Curated",
}


def main():
    data = load_existing()
    existing_ids = {e.get("id") or e.get("link") or e.get("title") for e in data["entries"]}

    all_items, failures = [], []
    for name, fn in [
        ("azure-updates", azure_updates_items),
        ("architecture-center", arch_center_items),
        ("accelerators", accelerator_items),
    ]:
        try:
            fetched = fn()
            all_items.extend(fetched)
            print(f"{name}: {len(fetched)} matched items")
        except Exception as exc:
            failures.append(name)
            print(f"ERROR: {name} failed: {exc}", file=sys.stderr)

    if len(failures) == 3:
        print("ERROR: all sources failed; aborting without changes", file=sys.stderr)
        sys.exit(1)

    new_items = [i for i in all_items if i["id"] not in existing_ids]

    if new_items:
        data["entries"] = new_items + data["entries"]
        data["entries"].sort(key=lambda e: e["date"], reverse=True)
        data["entries"] = data["entries"][:MAX_ENTRIES]

    data["lastUpdated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    if new_items:
        lines = [
            f"The weekly sync found **{len(new_items)}** new item(s) across "
            "Azure Updates, the Azure Architecture Center, and the official accelerator repos.",
            "",
            "| Date | Source | Services | Item |",
            "|------|--------|----------|------|",
        ]
        for i in sorted(new_items, key=lambda x: x["date"], reverse=True):
            services = ", ".join(i["services"])
            title = i["title"].replace("|", "\\|")
            source = SOURCE_LABEL.get(i["source"], i["source"])
            lines.append(f"| {i['date']} | {source} | {services} | [{title}]({i['link']}) |")
        lines += [
            "",
            "### Task: refresh the whole site, not just the changelog",
            "",
            "`data/changelog.json` has already been updated automatically. Now review each item above and:",
            "",
            "1. **Service capability changes** (Azure Updates): update the capabilities, tiers/plans tables, "
            "use cases and best practices on the affected service pages "
            "(`apim.html`, `logic-apps.html`, `functions.html`, `container-apps.html`, "
            "`service-bus.html`, `app-service.html`). Mark new features and remove/annotate retired ones.",
            "2. **New or updated architecture guidance** (Architecture Center): if a new pattern or reference "
            "architecture is relevant to these services, add or update a pattern section in `patterns.html` "
            "with a Mermaid diagram and a source link to the Architecture Center article. "
            "Update existing pattern sections if the guidance changed materially.",
            "3. **Accelerator releases**: check the release notes and update the accelerator descriptions/links "
            "in `patterns.html` (Accelerators section) and the Key references on the relevant service pages.",
            "4. Keep diagrams, tables and copy consistent with the site's existing style. "
            "See `.github/copilot-instructions.md` for site structure and conventions.",
        ]
        with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    print(f"total matched: {len(all_items)}; new: {len(new_items)}; changelog size: {len(data['entries'])}")

    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a", encoding="utf-8") as f:
            f.write(f"new_count={len(new_items)}\n")


if __name__ == "__main__":
    main()
