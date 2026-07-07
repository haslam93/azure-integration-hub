/* Shared site behavior: nav injection, theme toggle, mermaid init, changelog rendering. */
(function () {
  "use strict";

  const NAV = [
    { href: "index.html", label: "Home" },
    { href: "apim.html", label: "API Management" },
    { href: "logic-apps.html", label: "Logic Apps" },
    { href: "functions.html", label: "Functions" },
    { href: "container-apps.html", label: "Container Apps" },
    { href: "service-bus.html", label: "Messaging & Events" },
    { href: "app-service.html", label: "App Service" },
    { href: "patterns.html", label: "Patterns" },
    { href: "changelog.html", label: "Changelog" },
  ];

  function currentPage() {
    const p = location.pathname.split("/").pop();
    return p === "" ? "index.html" : p;
  }

  function buildHeader() {
    const header = document.createElement("header");
    header.className = "site-header";
    const inner = document.createElement("div");
    inner.className = "inner";

    const brand = document.createElement("a");
    brand.className = "brand";
    brand.href = "index.html";
    brand.innerHTML = '<span class="logo">Az</span><span>Hammad&#8217;s Azure Integration Hub</span>';
    inner.appendChild(brand);

    const nav = document.createElement("nav");
    nav.className = "site-nav";
    const page = currentPage();
    NAV.forEach((item) => {
      const a = document.createElement("a");
      a.href = item.href;
      a.textContent = item.label;
      if (item.href === page) a.className = "active";
      nav.appendChild(a);
    });
    inner.appendChild(nav);

    const toggle = document.createElement("button");
    toggle.className = "theme-toggle";
    toggle.setAttribute("aria-label", "Toggle theme");
    toggle.textContent = document.documentElement.getAttribute("data-theme") === "dark" ? "☀" : "☾";
    toggle.addEventListener("click", () => {
      const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("cpTheme", next);
      toggle.textContent = next === "dark" ? "☀" : "☾";
      location.reload(); // re-render mermaid with matching theme
    });
    inner.appendChild(toggle);

    header.appendChild(inner);
    document.body.prepend(header);
  }

  function buildFooter() {
    const footer = document.createElement("footer");
    footer.className = "site-footer";
    footer.innerHTML =
      'Hammad&#8217;s Azure Integration Hub &mdash; personal single source of truth. Auto-refreshed weekly from ' +
      '<a href="https://azure.microsoft.com/updates/" target="_blank" rel="noopener">Azure Updates</a>. ' +
      'Not an official Microsoft site.';
    document.body.appendChild(footer);
  }

  function initMermaid() {
    if (!window.mermaid) return;
    const dark = document.documentElement.getAttribute("data-theme") === "dark";
    window.mermaid.initialize({
      startOnLoad: false,
      securityLevel: "loose",
      theme: dark ? "dark" : "neutral",
      themeVariables: dark
        ? { primaryColor: "#3d3b3a", primaryBorderColor: "#fd8ea1", lineColor: "#b0b0b0", fontFamily: '"Segoe UI", sans-serif' }
        : { primaryColor: "#fdf2f5", primaryBorderColor: "#b11f4b", lineColor: "#5c5c5c", fontFamily: '"Segoe UI", sans-serif' },
      flowchart: { curve: "basis", htmlLabels: true },
      sequence: { actorMargin: 40 },
    });
    window.mermaid.run({ querySelector: ".mermaid" });
  }

  function buildToc() {
    const toc = document.querySelector(".toc[data-auto]");
    if (!toc) return;
    const headings = document.querySelectorAll(".content h2[id]");
    if (!headings.length) return;
    const title = document.createElement("h4");
    title.textContent = "On this page";
    toc.appendChild(title);
    headings.forEach((h) => {
      const a = document.createElement("a");
      a.href = "#" + h.id;
      a.textContent = h.textContent;
      toc.appendChild(a);
    });
  }

  /* ---------- Changelog ---------- */

  const SERVICE_LABELS = {
    apim: "API Management",
    "logic-apps": "Logic Apps",
    functions: "Functions",
    "container-apps": "Container Apps",
    "service-bus": "Service Bus",
    "event-grid": "Event Grid",
    "event-hubs": "Event Hubs",
    "app-service": "App Service",
    "ai-foundry": "AI Foundry",
    architecture: "Architecture",
    general: "Integration",
  };

  const SOURCE_LABELS = {
    "architecture-center": "Architecture Center",
    accelerator: "Accelerator",
  };

  function statusPill(status) {
    const s = (status || "").toLowerCase();
    if (s.includes("general") || s === "ga") return '<span class="pill ga">GA</span>';
    if (s.includes("preview")) return '<span class="pill preview">Preview</span>';
    if (s.includes("retire") || s.includes("deprecat")) return '<span class="pill retire">Retirement</span>';
    return "";
  }

  function renderEntries(entries, container) {
    container.innerHTML = "";
    if (!entries.length) {
      container.innerHTML = '<p class="updated-stamp">No entries match this filter yet.</p>';
      return;
    }
    let lastMonth = "";
    entries.forEach((e) => {
      const d = new Date(e.date);
      const month = d.toLocaleDateString(undefined, { year: "numeric", month: "long" });
      if (month !== lastMonth) {
        const h = document.createElement("div");
        h.className = "changelog-month";
        h.textContent = month;
        container.appendChild(h);
        lastMonth = month;
      }
      const div = document.createElement("div");
      div.className = "changelog-entry";
      const services = (e.services || ["general"])
        .map((s) => '<span class="pill">' + (SERVICE_LABELS[s] || s) + "</span>")
        .join("");
      const source = SOURCE_LABELS[e.source]
        ? '<span class="pill source">' + SOURCE_LABELS[e.source] + "</span>"
        : "";
      div.innerHTML =
        '<div class="meta">' +
        '<span>' + d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }) + "</span>" +
        services + statusPill(e.status) + source +
        "</div>" +
        "<h3>" + (e.link ? '<a href="' + e.link + '" target="_blank" rel="noopener">' + e.title + "</a>" : e.title) + "</h3>" +
        "<p>" + (e.summary || "") + "</p>";
      container.appendChild(div);
    });
  }

  async function loadChangelog() {
    const container = document.getElementById("changelog-list");
    const preview = document.getElementById("changelog-preview");
    if (!container && !preview) return;
    let data;
    try {
      const res = await fetch("data/changelog.json", { cache: "no-store" });
      data = await res.json();
    } catch (err) {
      const target = container || preview;
      target.innerHTML =
        '<p class="updated-stamp">Could not load changelog data. If you opened this file directly from disk, serve it over HTTP (e.g. <code>python -m http.server</code>) or view the GitHub Pages site.</p>';
      return;
    }
    const entries = (data.entries || []).slice().sort((a, b) => new Date(b.date) - new Date(a.date));

    const stamp = document.getElementById("changelog-updated");
    if (stamp && data.lastUpdated) {
      stamp.textContent = "Last refreshed: " + new Date(data.lastUpdated).toLocaleString();
    }

    if (preview) {
      renderEntries(entries.slice(0, 6), preview);
    }

    if (container) {
      renderEntries(entries, container);
      const controls = document.getElementById("changelog-filters");
      if (controls) {
        const services = new Set();
        entries.forEach((e) => (e.services || []).forEach((s) => services.add(s)));
        const makeBtn = (value, label) => {
          const b = document.createElement("button");
          b.className = "filter-btn" + (value === "all" ? " active" : "");
          b.textContent = label;
          b.dataset.service = value;
          b.addEventListener("click", () => {
            controls.querySelectorAll(".filter-btn").forEach((x) => x.classList.remove("active"));
            b.classList.add("active");
            const filtered =
              value === "all" ? entries : entries.filter((e) => (e.services || []).includes(value));
            renderEntries(filtered, container);
          });
          return b;
        };
        controls.appendChild(makeBtn("all", "All"));
        Object.keys(SERVICE_LABELS).forEach((s) => {
          if (services.has(s)) controls.appendChild(makeBtn(s, SERVICE_LABELS[s]));
        });
      }
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    buildHeader();
    buildFooter();
    buildToc();
    initMermaid();
    loadChangelog();
  });
})();
