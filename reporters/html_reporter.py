"""
reporters/html_reporter.py — Generador de informes HTML profesional
Diseño: dark terminal theme, sidebar de navegación, secciones por módulo
"""

import os
import json
from datetime import datetime
from utils.banner import Colors

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")

MODULE_ICONS = {
    "domain":   "🌐",
    "ip":       "📡",
    "email":    "📧",
    "username": "👤",
    "dorks":    "🔎",
    "vt":       "🛡️",
}

MODULE_LABELS = {
    "domain":   "Dominio",
    "ip":       "Dirección IP",
    "email":    "Email",
    "username": "Username",
    "dorks":    "Google Dorks",
    "vt":       "VirusTotal",
}


# ─────────────────────────────────────────────────────────────────────────────
# ENTRADA PÚBLICA
# ─────────────────────────────────────────────────────────────────────────────

def generate_report(module: str, target: str, results: dict):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_target = target.replace("/", "_").replace("@", "_at_").replace(":", "_")
    filename    = f"owlsec_{module}_{safe_target}_{timestamp}.html"
    filepath    = os.path.join(OUTPUT_DIR, filename)

    html = _build_html(module, target, results)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    print(Colors.ok(f"Informe generado: output/{filename}"))
    return filepath


# ─────────────────────────────────────────────────────────────────────────────
# ESQUELETO HTML PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def _build_html(module: str, target: str, results: dict) -> str:
    ts      = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    icon    = MODULE_ICONS.get(module, "🔍")
    label   = MODULE_LABELS.get(module, module.upper())

    builders = {
        "domain":   _build_domain_html,
        "ip":       _build_ip_html,
        "email":    _build_email_html,
        "username": _build_username_html,
        "dorks":    _build_dorks_html,
        "vt":       _build_vt_html,
    }
    body_content = builders.get(module, _build_generic_html)(results)

    # Sidebar sections (IDs extraídos del contenido)
    sections_js = _extract_section_ids(body_content)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OwlSec Report — {target}</title>
  <style>
{_CSS}
  </style>
</head>
<body>

  <!-- TOPBAR -->
  <div class="topbar">
    <div class="topbar-brand">
      <span class="topbar-logo">🦉</span>
      <span class="topbar-title">OwlSec</span>
      <span class="topbar-version">v0.1</span>
    </div>
    <div class="topbar-meta">
      <span class="badge badge-module">{icon} {label}</span>
      <span class="topbar-ts">{ts}</span>
    </div>
  </div>

  <div class="layout">

    <!-- SIDEBAR -->
    <nav class="sidebar">
      <div class="sidebar-target">
        <div class="sidebar-target-label">OBJETIVO</div>
        <div class="sidebar-target-value" title="{target}">{target}</div>
      </div>
      <ul class="sidebar-nav" id="sidebarNav"></ul>
      <div class="sidebar-footer">
        <div class="sidebar-footer-line">OwlSec</div>
        <div class="sidebar-footer-line" style="color:#484f58">Uso ético y legal únicamente</div>
      </div>
    </nav>

    <!-- MAIN -->
    <main class="main">
      <div class="page-header">
        <h1>{icon} {label} <span class="page-header-target">{target}</span></h1>
        <p class="page-header-meta">Análisis generado el {ts}</p>
      </div>

      <div id="reportContent">
        {body_content}
      </div>

      <footer class="footer">
        OwlSec v0.1 &nbsp;·&nbsp; Solo para sistemas con autorización explícita
      </footer>
    </main>

  </div>

  <script>
{_JS}
  </script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────

_CSS = """
    :root {
      --bg:        #0d1117;
      --bg2:       #161b22;
      --bg3:       #21262d;
      --border:    #30363d;
      --border2:   #21262d;
      --text:      #c9d1d9;
      --text-dim:  #8b949e;
      --text-bright: #f0f6fc;
      --blue:      #58a6ff;
      --blue-dark: #1f6feb;
      --green:     #3fb950;
      --green-dark:#238636;
      --yellow:    #d29922;
      --red:       #da3633;
      --purple:    #bc8cff;
      --cyan:      #79c0ff;
      --sidebar-w: 220px;
      --topbar-h:  48px;
      --radius:    6px;
      --font-mono: 'Courier New', 'Lucida Console', monospace;
      --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html { scroll-behavior: smooth; }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-sans);
      font-size: 14px;
      line-height: 1.5;
      min-height: 100vh;
    }

    /* ── TOPBAR ── */
    .topbar {
      position: fixed; top: 0; left: 0; right: 0;
      height: var(--topbar-h);
      background: var(--bg2);
      border-bottom: 1px solid var(--border);
      display: flex; align-items: center; justify-content: space-between;
      padding: 0 1.5rem;
      z-index: 100;
    }
    .topbar-brand { display: flex; align-items: center; gap: 0.5rem; }
    .topbar-logo  { font-size: 1.2rem; color: var(--blue); }
    .topbar-title { font-weight: 600; color: var(--text-bright); font-family: var(--font-mono); }
    .topbar-version { font-size: 0.7rem; color: var(--text-dim); padding: 1px 6px;
                      background: var(--bg3); border-radius: 10px; }
    .topbar-meta  { display: flex; align-items: center; gap: 1rem; }
    .topbar-ts    { font-size: 0.78rem; color: var(--text-dim); font-family: var(--font-mono); }

    /* ── LAYOUT ── */
    .layout {
      display: flex;
      margin-top: var(--topbar-h);
      min-height: calc(100vh - var(--topbar-h));
    }

    /* ── SIDEBAR ── */
    .sidebar {
      width: var(--sidebar-w);
      min-height: calc(100vh - var(--topbar-h));
      background: var(--bg2);
      border-right: 1px solid var(--border);
      position: sticky;
      top: var(--topbar-h);
      height: calc(100vh - var(--topbar-h));
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      padding: 1.2rem 0;
      flex-shrink: 0;
    }
    .sidebar-target {
      padding: 0 1rem 1rem;
      border-bottom: 1px solid var(--border2);
      margin-bottom: 0.8rem;
    }
    .sidebar-target-label {
      font-size: 0.65rem; letter-spacing: 0.08em;
      color: var(--text-dim); margin-bottom: 0.3rem;
    }
    .sidebar-target-value {
      font-family: var(--font-mono); font-size: 0.8rem;
      color: var(--cyan); word-break: break-all;
    }
    .sidebar-nav { list-style: none; flex: 1; }
    .sidebar-nav li a {
      display: flex; align-items: center; gap: 0.5rem;
      padding: 0.45rem 1rem;
      color: var(--text-dim); text-decoration: none;
      font-size: 0.82rem; border-left: 2px solid transparent;
      transition: all 0.15s;
    }
    .sidebar-nav li a:hover,
    .sidebar-nav li a.active {
      color: var(--text-bright);
      background: var(--bg3);
      border-left-color: var(--blue);
    }
    .sidebar-nav li a .nav-icon { font-size: 0.9rem; min-width: 18px; }
    .sidebar-footer {
      padding: 0.8rem 1rem 0;
      border-top: 1px solid var(--border2);
      font-size: 0.7rem; color: var(--text-dim);
    }
    .sidebar-footer-line { margin-bottom: 2px; }

    /* ── MAIN ── */
    .main {
      flex: 1;
      padding: 2rem 2.5rem;
      min-width: 0;
    }
    .page-header { margin-bottom: 2rem; padding-bottom: 1.2rem; border-bottom: 1px solid var(--border); }
    .page-header h1 { font-size: 1.5rem; color: var(--text-bright); font-weight: 600; }
    .page-header-target { color: var(--blue); font-family: var(--font-mono); font-size: 1rem; }
    .page-header-meta { color: var(--text-dim); font-size: 0.82rem; margin-top: 0.3rem; }

    /* ── SECTIONS ── */
    .section {
      margin-bottom: 2.5rem;
      scroll-margin-top: calc(var(--topbar-h) + 1.5rem);
    }
    .section-header {
      display: flex; align-items: center; justify-content: space-between;
      cursor: pointer; user-select: none;
      padding-bottom: 0.6rem;
      border-bottom: 1px solid var(--border);
      margin-bottom: 1rem;
    }
    .section-header:hover .section-title { color: var(--blue); }
    .section-title {
      font-size: 0.9rem; font-weight: 600;
      color: var(--text-bright); display: flex; align-items: center; gap: 0.5rem;
    }
    .section-toggle {
      color: var(--text-dim); font-size: 0.75rem;
      transition: transform 0.2s;
    }
    .section-toggle.collapsed { transform: rotate(-90deg); }
    .section-body { transition: opacity 0.15s; }
    .section-body.hidden { display: none; }

    /* ── BADGES ── */
    .badge {
      display: inline-flex; align-items: center; gap: 4px;
      padding: 2px 9px; border-radius: 12px;
      font-size: 0.72rem; font-weight: 500; line-height: 1.4;
    }
    .badge-module  { background: var(--blue-dark); color: #fff; }
    .badge-clean   { background: rgba(63,185,80,.15); color: var(--green); border: 1px solid rgba(63,185,80,.3); }
    .badge-warn    { background: rgba(210,153,34,.15); color: var(--yellow); border: 1px solid rgba(210,153,34,.3); }
    .badge-danger  { background: rgba(218,54,51,.15); color: var(--red); border: 1px solid rgba(218,54,51,.3); }
    .badge-neutral { background: var(--bg3); color: var(--text-dim); border: 1px solid var(--border); }
    .badge-found   { background: rgba(88,166,255,.12); color: var(--blue); border: 1px solid rgba(88,166,255,.25); }

    /* ── STATS ROW ── */
    .stats-row { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; }
    .stat-card {
      background: var(--bg2); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 0.8rem 1.2rem;
      min-width: 90px; text-align: center;
    }
    .stat-card-value { font-size: 1.5rem; font-weight: 700; color: var(--blue); display: block;
                       font-family: var(--font-mono); line-height: 1; margin-bottom: 4px; }
    .stat-card-label { font-size: 0.72rem; color: var(--text-dim); }

    /* ── KVTABLE (key-value pairs) ── */
    .kv-table { width: 100%; border-collapse: collapse; font-size: 0.84rem; }
    .kv-table tr:not(:last-child) td { border-bottom: 1px solid var(--border2); }
    .kv-table td { padding: 0.5rem 0.6rem; vertical-align: top; }
    .kv-table td:first-child {
      color: var(--text-dim); width: 38%; font-family: var(--font-mono);
      font-size: 0.78rem; padding-right: 1rem;
    }
    .kv-table td:last-child { color: var(--text); word-break: break-all; }

    /* ── DATA TABLE ── */
    .data-table { width: 100%; border-collapse: collapse; font-size: 0.83rem; }
    .data-table th {
      background: var(--bg3); color: var(--text-dim); font-weight: 500;
      text-align: left; padding: 0.5rem 0.8rem;
      border-bottom: 1px solid var(--border); font-size: 0.75rem; letter-spacing: 0.04em;
    }
    .data-table td { padding: 0.5rem 0.8rem; border-bottom: 1px solid var(--border2); vertical-align: top; }
    .data-table tr:hover td { background: var(--bg2); }
    .data-table .mono { font-family: var(--font-mono); font-size: 0.8rem; color: var(--cyan); word-break: break-all; }

    /* ── OPEN BUTTON ── */
    .btn-open {
      display: inline-block; background: var(--green-dark); color: #fff;
      text-decoration: none; padding: 3px 11px; border-radius: 4px;
      font-size: 0.73rem; white-space: nowrap; transition: background 0.15s;
    }
    .btn-open:hover { background: #2ea043; }
    .btn-vt {
      display: inline-block; background: var(--blue-dark); color: #fff;
      text-decoration: none; padding: 5px 14px; border-radius: 4px;
      font-size: 0.8rem; white-space: nowrap;
    }

    /* ── VERDICT BANNER ── */
    .verdict-banner {
      display: flex; align-items: center; gap: 1rem;
      padding: 1rem 1.2rem; border-radius: var(--radius);
      margin-bottom: 1.5rem; border: 1px solid;
    }
    .verdict-banner.clean   { background: rgba(63,185,80,.08);  border-color: rgba(63,185,80,.3); }
    .verdict-banner.suspicious { background: rgba(210,153,34,.08); border-color: rgba(210,153,34,.3); }
    .verdict-banner.malicious  { background: rgba(218,54,51,.08);  border-color: rgba(218,54,51,.3); }
    .verdict-banner.unknown    { background: var(--bg2); border-color: var(--border); }
    .verdict-icon  { font-size: 2rem; line-height: 1; }
    .verdict-label { font-size: 1.1rem; font-weight: 700; }
    .verdict-sub   { font-size: 0.8rem; color: var(--text-dim); margin-top: 2px; }

    /* ── DETECTION BAR ── */
    .det-bar-wrap {
      background: var(--bg3); border-radius: 4px;
      height: 10px; width: 100%; max-width: 480px;
      margin: 0.8rem 0; overflow: hidden;
    }
    .det-bar-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease; }

    /* ── TAG LIST ── */
    .tag-list { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.5rem; }
    .tag {
      background: var(--bg3); border: 1px solid var(--border);
      border-radius: 10px; padding: 2px 9px;
      font-size: 0.72rem; color: var(--text-dim); font-family: var(--font-mono);
    }

    /* ── SUBDOMAIN / PLATFORM GRID ── */
    .item-grid {
      display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      gap: 0.6rem; margin-top: 0.5rem;
    }
    .item-card {
      background: var(--bg2); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 0.55rem 0.8rem;
      font-size: 0.8rem; display: flex; align-items: center; gap: 0.5rem;
    }
    .item-card a { color: var(--cyan); text-decoration: none; word-break: break-all; }
    .item-card a:hover { color: var(--blue); }
    .item-card .dot-green { color: var(--green); font-size: 0.7rem; }
    .item-card .dot-red   { color: var(--red);   font-size: 0.7rem; }

    /* ── DNS RECORD TYPE ── */
    .dns-type {
      display: inline-block; font-family: var(--font-mono); font-size: 0.7rem;
      padding: 1px 6px; border-radius: 3px; margin-right: 6px; min-width: 40px;
      text-align: center; font-weight: 600;
    }
    .dns-A     { background: rgba(88,166,255,.15); color: var(--blue); }
    .dns-AAAA  { background: rgba(88,166,255,.10); color: var(--cyan); }
    .dns-MX    { background: rgba(188,140,255,.15); color: var(--purple); }
    .dns-NS    { background: rgba(63,185,80,.12); color: var(--green); }
    .dns-TXT   { background: rgba(210,153,34,.12); color: var(--yellow); }
    .dns-CNAME { background: rgba(218,54,51,.12); color: #f97583; }
    .dns-SOA   { background: var(--bg3); color: var(--text-dim); }

    /* ── CODE BLOCK ── */
    pre {
      background: var(--bg2); border: 1px solid var(--border); border-radius: var(--radius);
      padding: 1.2rem; overflow-x: auto; font-family: var(--font-mono);
      font-size: 0.8rem; line-height: 1.6; color: var(--text);
    }

    /* ── EMPTY STATE ── */
    .empty { color: var(--text-dim); font-size: 0.82rem; padding: 0.8rem 0; font-style: italic; }

    /* ── FOOTER ── */
    .footer {
      margin-top: 3rem; padding-top: 1.2rem;
      border-top: 1px solid var(--border2);
      color: var(--text-dim); font-size: 0.75rem; text-align: center;
    }
"""


# ─────────────────────────────────────────────────────────────────────────────
# JS
# ─────────────────────────────────────────────────────────────────────────────

_JS = """
  // Build sidebar navigation from section elements
  document.addEventListener('DOMContentLoaded', () => {
    const nav     = document.getElementById('sidebarNav');
    const sections = document.querySelectorAll('.section[id]');

    sections.forEach(sec => {
      const titleEl = sec.querySelector('.section-title');
      const text = titleEl ? titleEl.textContent.trim() : sec.id;
      const li   = document.createElement('li');
      li.innerHTML = `<a href="#${sec.id}"><span class="nav-icon">${text.slice(0,2)}</span>${text.slice(2).trim()}</a>`;
      nav.appendChild(li);
    });

    // Active link on scroll
    const links = nav.querySelectorAll('a');
    const observer = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          links.forEach(l => l.classList.remove('active'));
          const link = nav.querySelector(`a[href="#${e.target.id}"]`);
          if (link) link.classList.add('active');
        }
      });
    }, { rootMargin: '-48px 0px -60% 0px' });

    sections.forEach(s => observer.observe(s));
  });

  // Toggle section collapse
  function toggleSection(id) {
    const body   = document.getElementById('body-' + id);
    const toggle = document.getElementById('toggle-' + id);
    if (!body) return;
    body.classList.toggle('hidden');
    toggle.classList.toggle('collapsed');
  }
"""


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS DE SECCIONES
# ─────────────────────────────────────────────────────────────────────────────

def _section(sid: str, title: str, content: str) -> str:
    return f"""
<div class="section" id="{sid}">
  <div class="section-header" onclick="toggleSection('{sid}')">
    <span class="section-title">{title}</span>
    <span class="section-toggle" id="toggle-{sid}">▾</span>
  </div>
  <div class="section-body" id="body-{sid}">
    {content}
  </div>
</div>"""


def _kv_row(key: str, value) -> str:
    if value is None or value == "N/A" or value == "":
        return ""
    if isinstance(value, list):
        value = ", ".join(str(v) for v in value) if value else "—"
    return f"<tr><td>{key}</td><td>{value}</td></tr>"


def _kv_table(rows: list) -> str:
    inner = "".join(_kv_row(k, v) for k, v in rows if v not in (None, "N/A", "", []))
    if not inner:
        return '<p class="empty">Sin datos disponibles.</p>'
    return f'<table class="kv-table"><tbody>{inner}</tbody></table>'


def _stats_row(cards: list) -> str:
    """cards = list of (value, label, color?)"""
    html = '<div class="stats-row">'
    for item in cards:
        val, lbl = item[0], item[1]
        color = item[2] if len(item) > 2 else "var(--blue)"
        html += f'<div class="stat-card"><span class="stat-card-value" style="color:{color}">{val}</span><span class="stat-card-label">{lbl}</span></div>'
    html += '</div>'
    return html


def _extract_section_ids(html: str) -> list:
    import re
    return re.findall(r'class="section" id="([^"]+)"', html)


# ─────────────────────────────────────────────────────────────────────────────
# MODULE: DOMAIN
# ─────────────────────────────────────────────────────────────────────────────

def _build_domain_html(results: dict) -> str:
    out = ""

    # WHOIS
    if "whois" in results:
        w = results["whois"]
        if "error" not in w:
            ns = "<br>".join(w.get("name_servers") or [])
            emails = "<br>".join(w.get("emails") or []) if isinstance(w.get("emails"), list) else w.get("emails","")
            rows = [
                ("Registrador", w.get("registrar")),
                ("Organización", w.get("org")),
                ("País", w.get("country")),
                ("Creación", w.get("creation_date")),
                ("Expiración", w.get("expiration_date")),
                ("Name servers", ns or None),
                ("Emails registrador", emails or None),
            ]
            out += _section("whois", "📋 WHOIS", _kv_table(rows))
        else:
            out += _section("whois", "📋 WHOIS", f'<p class="empty">Error: {w["error"]}</p>')

    # DNS
    if "dns" in results:
        dns = results["dns"]
        dns_html = ""
        for rtype, records in dns.items():
            css = f"dns-{rtype}"
            for r in records:
                dns_html += f'<div style="padding:4px 0;border-bottom:1px solid var(--border2)">' \
                            f'<span class="dns-type {css}">{rtype}</span>' \
                            f'<span style="font-family:var(--font-mono);font-size:0.82rem">{r}</span></div>'
        out += _section("dns", "🔀 Registros DNS",
                        dns_html or '<p class="empty">Sin registros encontrados.</p>')

    # SUBDOMINIOS
    if "subdomains" in results:
        subs = results["subdomains"]
        if subs:
            cards = "".join(
                f'<div class="item-card"><span class="dot-green">●</span>'
                f'<span style="font-family:var(--font-mono);font-size:0.79rem">{s}</span></div>'
                for s in subs
            )
            content = _stats_row([(len(subs), "subdominios", "var(--green)")]) + \
                      f'<div class="item-grid">{cards}</div>'
        else:
            content = '<p class="empty">No se encontraron subdominios.</p>'
        out += _section("subdomains", f"🌿 Subdominios ({len(subs)})", content)

    return out or _build_generic_html(results)


# ─────────────────────────────────────────────────────────────────────────────
# MODULE: IP
# ─────────────────────────────────────────────────────────────────────────────

def _build_ip_html(results: dict) -> str:
    out = ""

    if "geo" in results:
        g = results["geo"]
        rows = [
            ("País",      g.get("country")),
            ("Región",    g.get("region")),
            ("Ciudad",    g.get("city")),
            ("ISP",       g.get("isp")),
            ("ASN",       g.get("as")),
            ("Org",       g.get("org")),
            ("Zona horaria", g.get("timezone")),
            ("Coordenadas",  f'{g.get("lat")}, {g.get("lon")}' if g.get("lat") else None),
        ]
        out += _section("geo", "📍 Geolocalización", _kv_table(rows))

    if "shodan" in results:
        s = results["shodan"]
        if "error" not in s:
            ports_html = " ".join(
                f'<span class="badge badge-neutral" style="font-family:var(--font-mono)">{p}</span>'
                for p in (s.get("ports") or [])
            )
            vulns_html = " ".join(
                f'<span class="badge badge-danger">{v}</span>'
                for v in (s.get("vulns") or [])
            )
            rows = [
                ("OS",         s.get("os")),
                ("Hostnames",  ", ".join(s.get("hostnames") or [])),
                ("Tags",       ", ".join(s.get("tags") or [])),
                ("Puertos abiertos", ports_html or "—"),
                ("CVEs conocidos",   vulns_html or "Ninguno"),
            ]
            out += _section("shodan", "🔭 Shodan", _kv_table(rows))
        else:
            out += _section("shodan", "🔭 Shodan", f'<p class="empty">{s["error"]}</p>')

    return out or _build_generic_html(results)


# ─────────────────────────────────────────────────────────────────────────────
# MODULE: EMAIL
# ─────────────────────────────────────────────────────────────────────────────

def _build_email_html(results: dict) -> str:
    out = ""

    if "validation" in results:
        v = results["validation"]
        fmt_badge = '<span class="badge badge-clean">✓ Válido</span>' if v.get("format_valid") \
                    else '<span class="badge badge-danger">✗ Inválido</span>'
        mx_badge  = '<span class="badge badge-clean">✓ MX encontrado</span>' if v.get("mx_valid") \
                    else '<span class="badge badge-warn">⚠ Sin MX</span>'
        mx_str = "<br>".join(v.get("mx_records") or [])
        rows = [
            ("Formato",        fmt_badge),
            ("Registros MX",   mx_badge),
            ("Servidores MX",  mx_str or None),
        ]
        out += _section("validation", "✅ Validación", _kv_table(rows))

    if "hibp" in results:
        h = results["hibp"]
        if "error" not in h:
            if h.get("breached"):
                breaches = h.get("breaches", [])
                cards = "".join(
                    f'<div class="item-card"><span class="dot-red">●</span>{b}</div>'
                    for b in breaches
                )
                content = _stats_row([(h["count"], "brechas encontradas", "var(--red)")]) + \
                          f'<div class="item-grid">{cards}</div>'
            else:
                content = '<p><span class="badge badge-clean">✓ No encontrado en ninguna brecha conocida</span></p>'
            out += _section("hibp", "🔓 Have I Been Pwned", content)
        else:
            out += _section("hibp", "🔓 Have I Been Pwned", f'<p class="empty">{h["error"]}</p>')

    return out or _build_generic_html(results)


# ─────────────────────────────────────────────────────────────────────────────
# MODULE: USERNAME
# ─────────────────────────────────────────────────────────────────────────────

def _build_username_html(results: dict) -> str:
    found     = results.get("found", [])
    not_found = results.get("not_found", [])
    total     = results.get("total_checked", len(found) + len(not_found))

    stats = _stats_row([
        (len(found),     "encontrado en", "var(--green)"),
        (total,          "plataformas",   "var(--blue)"),
        (len(not_found), "no encontrado", "var(--text-dim)"),
    ])

    found_cards = "".join(
        f'<div class="item-card"><span class="dot-green">●</span>'
        f'<a href="{p["url"]}" target="_blank" rel="noopener">{p["platform"]}</a></div>'
        for p in found
    )

    found_section = _section(
        "found", f"✅ Encontrado ({len(found)})",
        stats + (f'<div class="item-grid">{found_cards}</div>' if found_cards
                 else '<p class="empty">No encontrado en ninguna plataforma.</p>')
    )

    nf_cards = "".join(
        f'<div class="item-card"><span class="dot-red">●</span>'
        f'<span style="color:var(--text-dim)">{p}</span></div>'
        for p in not_found
    )
    nf_section = _section(
        "notfound", f"❌ No encontrado ({len(not_found)})",
        f'<div class="item-grid">{nf_cards}</div>' if nf_cards
        else '<p class="empty">—</p>'
    )

    return found_section + nf_section


# ─────────────────────────────────────────────────────────────────────────────
# MODULE: DORKS
# ─────────────────────────────────────────────────────────────────────────────

def _build_dorks_html(results: dict) -> str:
    engine = results.get("engine", "google")
    total  = results.get("total", 0)
    cats   = results.get("categories", {})

    stats = _stats_row([
        (total,     "dorks generados", "var(--blue)"),
        (len(cats), "categorías",      "var(--purple)"),
        (engine.capitalize(), "motor", "var(--cyan)"),
    ])

    out = stats
    for cat, dorks in cats.items():
        rows_html = "".join(
            f'<tr>'
            f'<td>{d["name"]}</td>'
            f'<td class="mono">{d["query"]}</td>'
            f'<td><a class="btn-open" href="{d["url"]}" target="_blank" rel="noopener">Abrir →</a></td>'
            f'</tr>'
            for d in dorks
        )
        table = f'''<table class="data-table">
          <thead><tr><th>Descripción</th><th>Query</th><th></th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>'''
        safe_id = "dork_" + cat.encode("ascii", "ignore").decode().replace(" ","_").replace("/","_")[:20]
        out += _section(safe_id, cat, table)

    return out


# ─────────────────────────────────────────────────────────────────────────────
# MODULE: VIRUSTOTAL
# ─────────────────────────────────────────────────────────────────────────────

def _build_vt_html(results: dict) -> str:
    verdict    = results.get("verdict", "unknown")
    malicious  = results.get("malicious", 0)
    suspicious = results.get("suspicious", 0)
    undetected = results.get("undetected", 0)
    total      = results.get("total_engines", 0)
    vt_link    = results.get("vt_link", "#")
    detections = results.get("detections", [])
    vt_type    = results.get("type", "")

    icons  = {"malicious":"🔴","suspicious":"🟡","clean":"🟢","unknown":"⚪"}
    labels = {"malicious":"MALICIOSO","suspicious":"SOSPECHOSO","clean":"LIMPIO","unknown":"DESCONOCIDO"}
    colors = {"malicious":"var(--red)","suspicious":"var(--yellow)","clean":"var(--green)","unknown":"var(--text-dim)"}

    icon_v  = icons.get(verdict, "❓")
    label_v = labels.get(verdict, verdict.upper())
    color_v = colors.get(verdict, "var(--text-dim)")
    pct     = round((malicious / total) * 100) if total else 0

    banner = f"""
    <div class="verdict-banner {verdict}">
      <div class="verdict-icon">{icon_v}</div>
      <div>
        <div class="verdict-label" style="color:{color_v}">{label_v}</div>
        <div class="verdict-sub">{malicious} malicioso · {suspicious} sospechoso · {total} motores analizados</div>
        <div class="det-bar-wrap">
          <div class="det-bar-fill" style="width:{pct}%;background:{color_v}"></div>
        </div>
        <a class="btn-vt" href="{vt_link}" target="_blank" rel="noopener">Ver en VirusTotal →</a>
      </div>
    </div>"""

    stats = _stats_row([
        (malicious,  "maliciosos",  "var(--red)"),
        (suspicious, "sospechosos", "var(--yellow)"),
        (undetected, "sin det.",    "var(--green)"),
        (total,      "total",       "var(--blue)"),
    ])

    out = banner + stats

    # Detecciones
    if detections:
        rows_html = "".join(
            f'<tr>'
            f'<td style="font-family:var(--font-mono);font-size:0.8rem">{d["engine"]}</td>'
            f'<td><span class="badge {"badge-danger" if d["category"]=="malicious" else "badge-warn"}">'
            f'{d["result"] or d["category"]}</span></td>'
            f'</tr>'
            for d in detections
        )
        det_content = f'''<table class="data-table">
          <thead><tr><th>Motor</th><th>Resultado</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>'''
    else:
        det_content = '<p class="empty">Sin detecciones por ningún motor.</p>'
    out += _section("vt_detections", f"🦠 Detecciones ({len(detections)})", det_content)

    # Detalles del objeto analizado
    detail_rows = []
    for key, label in [
        ("file_name","Nombre fichero"), ("file_type","Tipo"), ("file_size","Tamaño (bytes)"),
        ("md5","MD5"), ("sha1","SHA-1"), ("sha256","SHA-256"),
        ("first_seen","Primera vez visto"), ("last_seen","Última vez"),
        ("times_submitted","Veces enviado"), ("registrar","Registrador"),
        ("creation_date","Creación"), ("asn","ASN"), ("as_owner","AS Owner"),
        ("country","País"), ("network","Red"), ("reputation","Reputación"),
    ]:
        val = results.get(key)
        if val and val != "N/A":
            detail_rows.append((label, val))

    tags = results.get("tags", [])
    if tags:
        tags_html = '<div class="tag-list">' + "".join(f'<span class="tag">{t}</span>' for t in tags) + '</div>'
        detail_rows.append(("Tags", tags_html))

    if detail_rows:
        out += _section("vt_details", "📋 Detalles", _kv_table(detail_rows))

    # IPs históricas / URLs asociadas
    for key, title, icon in [
        ("resolved_ips",    "🌐 IPs históricas",  "dot-green"),
        ("associated_urls", "🔗 URLs asociadas",  "dot-red"),
    ]:
        items = results.get(key, [])
        if items:
            cards = "".join(
                f'<div class="item-card"><span class="{icon}">●</span>'
                f'<span style="font-family:var(--font-mono);font-size:0.78rem">{i}</span></div>'
                for i in items
            )
            safe_id = "vt_" + key
            out += _section(safe_id, title, f'<div class="item-grid">{cards}</div>')

    return out


# ─────────────────────────────────────────────────────────────────────────────
# FALLBACK GENÉRICO
# ─────────────────────────────────────────────────────────────────────────────

def _build_generic_html(results: dict) -> str:
    j = json.dumps(results, indent=2, ensure_ascii=False, default=str)
    return _section("raw", "📄 Datos", f"<pre>{j}</pre>")
