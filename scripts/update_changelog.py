#!/usr/bin/env python3
"""Refresh data/changelog.json from the official Azure Updates RSS feed.

Filters the feed to the services tracked by this site, merges new entries into
the existing changelog (deduplicated), and writes a markdown summary of the new
entries to new_updates.md so the weekly workflow can open a content-refresh issue.

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

FEED_URL = "https://www.microsoft.com/releasecommunications/api/v2/azure/rss"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(ROOT, "data", "changelog.json")
SUMMARY_FILE = os.path.join(ROOT, "new_updates.md")
MAX_ENTRIES = 400

# service key -> regex matched against title + categories + description
SERVICE_PATTERNS = {
    "apim": r"api management|apim\b|api center",
    "logic-apps": r"logic apps?",
    "functions": r"azure functions|durable functions|functions runtime|flex consumption",
    "container-apps": r"container apps",
    "service-bus": r"service bus",
    "event-grid": r"event grid",
    "event-hubs": r"event hubs?",
    "app-service": r"app service(?! environment for power)",
    "ai-foundry": r"ai foundry|azure openai|foundry agent|model inference",
}


def detect_services(text):
    found = []
    lowered = text.lower()
    for key, pattern in SERVICE_PATTERNS.items():
        if re.search(pattern, lowered):
            found.append(key)
    return found


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


def fetch_feed():
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "azure-integration-hub/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def parse_items(xml_bytes):
    root = ET.fromstring(xml_bytes)
    items = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or link or title).strip()
        description = clean_html(item.findtext("description") or "")
        categories = [c.text or "" for c in item.findall("category")]
        pub = item.findtext("pubDate")
        try:
            date = parsedate_to_datetime(pub).astimezone(timezone.utc)
        except Exception:
            date = datetime.now(timezone.utc)

        haystack = " ".join([title, description] + categories)
        services = detect_services(haystack)
        if not services:
            continue

        summary = description
        if len(summary) > 400:
            summary = summary[:397].rsplit(" ", 1)[0] + "…"

        items.append(
            {
                "id": guid,
                "date": date.strftime("%Y-%m-%d"),
                "title": title,
                "summary": summary,
                "link": link,
                "services": services,
                "status": detect_status(title + " " + description),
                "source": "azure-updates",
            }
        )
    return items


def load_existing():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"lastUpdated": None, "entries": []}


def main():
    data = load_existing()
    existing_ids = {e.get("id") or e.get("link") or e.get("title") for e in data["entries"]}

    try:
        feed_items = parse_items(fetch_feed())
    except Exception as exc:  # network/parse failure: keep site intact
        print(f"ERROR: failed to fetch/parse feed: {exc}", file=sys.stderr)
        sys.exit(1)

    new_items = [i for i in feed_items if i["id"] not in existing_ids]

    if new_items:
        data["entries"] = new_items + data["entries"]
        data["entries"].sort(key=lambda e: e["date"], reverse=True)
        data["entries"] = data["entries"][:MAX_ENTRIES]

    data["lastUpdated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Markdown summary for the content-refresh issue
    if new_items:
        lines = [
            "The weekly Azure Updates sync found "
            f"**{len(new_items)}** new update(s) relevant to this site.",
            "",
            "| Date | Services | Update |",
            "|------|----------|--------|",
        ]
        for i in new_items:
            services = ", ".join(i["services"])
            title = i["title"].replace("|", "\\|")
            lines.append(f"| {i['date']} | {services} | [{title}]({i['link']}) |")
        lines += [
            "",
            "### Task",
            "Review each update above and refresh the affected pages "
            "(`apim.html`, `logic-apps.html`, `functions.html`, `container-apps.html`, "
            "`service-bus.html`, `app-service.html`, `patterns.html`) so capabilities, "
            "architecture patterns, diagrams and use cases stay accurate. "
            "The changelog (`data/changelog.json`) has already been updated automatically.",
        ]
        with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    print(f"Feed items matched: {len(feed_items)}; new: {len(new_items)}; total: {len(data['entries'])}")

    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a", encoding="utf-8") as f:
            f.write(f"new_count={len(new_items)}\n")


if __name__ == "__main__":
    main()
