#!/usr/bin/env python3
"""
Bundle Harness Engineering book Markdown into a single self-contained reader.html.

Usage (from repo root or this directory):
  python3 harness-engineering-book/tools/build_reader.py

Requires: pip install -r tools/requirements.txt  (or: pip install markdown)
Does not modify any .md source files.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

import markdown

BOOK_ROOT = Path(__file__).resolve().parent.parent
OUT_HTML = BOOK_ROOT / "reader.html"
PUBLIC_DIR = BOOK_ROOT / "public"
OUT_MANIFEST = PUBLIC_DIR / "book-manifest.json"
MD_PUBLIC = PUBLIC_DIR / "md"

# Ordered navigation: (key, nav_label, relative_path_from_BOOK_ROOT)
NAV: list[tuple[str, str, str]] = [
    ("readme", "總覽 · README", "README.md"),
    ("index", "全書索引", "index.md"),
    ("syllabus", "課程大綱", "syllabus.md"),
    ("roadmap", "學習路線圖", "roadmap.md"),
    ("glossary", "術語表", "glossary.md"),
    ("references", "參考閱讀", "references.md"),
    ("ch01", "第 1 章", "part-1-foundations/01-from-prompt-to-harness-engineering.md"),
    ("ch02", "第 2 章", "part-1-foundations/02-agent-system-components.md"),
    ("ch03", "第 3 章", "part-1-foundations/03-harness-design-principles.md"),
    ("ch04", "第 4 章", "part-1-foundations/04-how-to-read-a-real-agent-harness.md"),
    ("ch05", "第 5 章", "part-2-claw-code/05-cli-entry-and-system-surface.md"),
    ("ch06", "第 6 章", "part-2-claw-code/06-conversation-runtime.md"),
    ("ch07", "第 7 章", "part-2-claw-code/07-tool-system.md"),
    ("ch08", "第 8 章", "part-2-claw-code/08-permissions-and-guardrails.md"),
    ("ch09", "第 9 章", "part-2-claw-code/09-session-transcript-memory.md"),
    ("ch10", "第 10 章", "part-2-claw-code/10-prompt-assembly-and-project-context.md"),
    ("ch11", "第 11 章", "part-2-claw-code/11-config-modes-and-environment.md"),
    ("ch12", "第 12 章", "part-2-claw-code/12-mcp-and-plugins.md"),
    ("ch13", "第 13 章", "part-2-claw-code/13-remote-and-execution-environments.md"),
    ("ch14", "第 14 章", "part-2-claw-code/14-parity-harness-and-testing.md"),
    ("ch15", "第 15 章", "part-2-claw-code/15-understanding-claw-code-as-a-whole.md"),
    ("ch16", "第 16 章", "part-3-mini-harness/16-defining-the-mini-harness-scope.md"),
    ("ch17", "第 17 章", "part-3-mini-harness/17-building-runtime-tools-permissions.md"),
    ("ch18", "第 18 章", "part-3-mini-harness/18-session-persistence-and-basic-testing.md"),
    ("ch19", "第 19 章", "part-4-integration/19-from-mini-harness-back-to-real-harness.md"),
    ("appendix-a", "附錄 A", "appendices/appendix-a-claw-code-reading-map.md"),
    ("appendix-b", "附錄 B", "appendices/appendix-b-mini-harness-project-guide.md"),
    ("appendix-d", "附錄 D", "appendices/appendix-d-further-study.md"),
]

PART_LABELS: list[tuple[str, str, tuple[str, ...]]] = [
    ("導覽與資源", "nav", ("readme", "index", "syllabus", "roadmap", "glossary", "references")),
    ("Part I · 基礎觀念", "p1", ("ch01", "ch02", "ch03", "ch04")),
    ("Part II · claw-code", "p2", ("ch05", "ch06", "ch07", "ch08", "ch09", "ch10", "ch11", "ch12", "ch13", "ch14", "ch15")),
    ("Part III · mini harness", "p3", ("ch16", "ch17", "ch18")),
    ("Part IV · 整合", "p4", ("ch19",)),
    ("附錄", "ap", ("appendix-a", "appendix-b", "appendix-d")),
]


def md_extensions():
    return [
        "markdown.extensions.fenced_code",
        "markdown.extensions.tables",
        "markdown.extensions.nl2br",
        "markdown.extensions.sane_lists",
        "markdown.extensions.codehilite",
    ]


def first_heading_title(md_text: str, fallback: str) -> str:
    for line in md_text.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return fallback


def rewrite_internal_md_links(html: str, path_to_key: dict[str, str]) -> str:
    """Turn same-book .md links into data-doc navigation targets."""

    def repl(m: re.Match) -> str:
        full = m.group(0)
        quote = m.group(1)
        href = m.group(2)
        if href.startswith(("http://", "https://", "mailto:", "#")):
            return full
        # Normalize path relative to book root
        clean = href.split("#", 1)[0]
        if not clean.lower().endswith(".md"):
            return full
        frag = ""
        if "#" in href:
            frag = "#" + href.split("#", 1)[1]
        norm = clean.replace("\\", "/").lstrip("./")
        key = path_to_key.get(norm)
        if not key:
            # try basename match (rare)
            for k, v in path_to_key.items():
                if k.endswith("/" + norm) or k == norm:
                    key = v
                    break
        if key:
            return f'href="{frag or "#"}" data-doc="{key}" class="internal-md-link"'
        return full

    return re.sub(
        r'href=(["\'])([^"\']+\.md(?:#[^"\']*)?)\1',
        repl,
        html,
    )


def strip_first_h1(html: str) -> str:
    """Avoid duplicate title: main chrome already shows document H1."""
    return re.sub(r"\A\s*<h1[^>]*>.*?</h1>\s*", "", html, count=1, flags=re.DOTALL | re.IGNORECASE)


def build_fragments() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    path_to_key: dict[str, str] = {rel.replace("\\", "/"): key for key, _nav, rel in NAV}

    md = markdown.Markdown(extensions=md_extensions())
    fragments: dict[str, str] = {}
    titles: dict[str, str] = {}

    for key, nav_label, rel in NAV:
        path = BOOK_ROOT / rel
        if not path.is_file():
            print(f"Missing: {path}", file=sys.stderr)
            sys.exit(1)
        raw = path.read_text(encoding="utf-8")
        titles[key] = first_heading_title(raw, nav_label)
        md.reset()
        html = md.convert(raw)
        html = rewrite_internal_md_links(html, path_to_key)
        html = strip_first_h1(html)
        fragments[key] = html

    return fragments, titles, path_to_key


def esc_js_str(s: str) -> str:
    return json.dumps(s)


HTML_SHELL = r"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="icon" href="public/favicon.svg" type="image/svg+xml" />
  <title>Harness Engineering 教材 · Web Reader</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,400;0,600;1,400&family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,600;1,7..72,400&family=Newsreader:ital,opsz,wght@0,6..72,500;0,6..72,700;1,6..72,500&display=swap" rel="stylesheet" />
  <style>
    :root {
      --font-display: "Newsreader", "Noto Serif TC", "Songti SC", serif;
      --font-body: "Literata", "Noto Serif TC", "Songti SC", Georgia, serif;
      --font-mono: "JetBrains Mono", "SF Mono", ui-monospace, monospace;
      --radius: 14px;
      --shadow: 0 18px 50px rgba(18, 24, 32, 0.12);
      --transition: 0.22s ease;
    }
    [data-theme="light"] {
      --bg: #f6f3ec;
      --bg-elevated: #fffdf8;
      --surface: rgba(255, 253, 248, 0.92);
      --text: #141820;
      --muted: #5c6470;
      --border: rgba(20, 24, 32, 0.1);
      --accent: #b54a2a;
      --accent-soft: rgba(181, 74, 42, 0.12);
      --link: #0b5cab;
      --code-bg: rgba(20, 24, 32, 0.06);
      --nav-active: rgba(181, 74, 42, 0.14);
      --focus: 0 0 0 3px rgba(11, 92, 171, 0.35);
      --noise: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.035'/%3E%3C/svg%3E");
    }
    [data-theme="dark"] {
      --bg: #0e1117;
      --bg-elevated: #151a22;
      --surface: rgba(21, 26, 34, 0.94);
      --text: #ece8e1;
      --muted: #9aa3b2;
      --border: rgba(236, 232, 225, 0.08);
      --accent: #e8a882;
      --accent-soft: rgba(232, 168, 130, 0.14);
      --link: #8ec5ff;
      --code-bg: rgba(0, 0, 0, 0.35);
      --nav-active: rgba(232, 168, 130, 0.16);
      --focus: 0 0 0 3px rgba(142, 197, 255, 0.45);
      --noise: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.06'/%3E%3C/svg%3E");
    }
    *, *::before, *::after { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      font-family: var(--font-body);
      font-size: 1.05rem;
      line-height: 1.72;
      color: var(--text);
      background-color: var(--bg);
      background-image: var(--noise);
      transition: background-color var(--transition), color var(--transition);
    }
    a { color: var(--link); text-underline-offset: 3px; }
    a:hover { opacity: 0.92; }
    .app {
      display: grid;
      grid-template-columns: minmax(260px, 300px) minmax(0, 1fr);
      min-height: 100vh;
      min-height: 100dvh;
    }
    @media (min-width: 1400px) {
      .app { grid-template-columns: minmax(280px, 320px) minmax(0, 1fr); }
    }
    @media (max-width: 900px) {
      .app { grid-template-columns: minmax(0, 1fr); }
      .sidebar { position: fixed; inset: 0 auto 0 0; width: min(92vw, 320px); max-width: calc(100vw - env(safe-area-inset-left, 0px) - env(safe-area-inset-right, 0px)); z-index: 40; transform: translateX(-105%); transition: transform 0.28s ease; box-shadow: var(--shadow); padding-bottom: calc(1.5rem + env(safe-area-inset-bottom, 0px)); }
      .sidebar.open { transform: translateX(0); }
      .backdrop { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.45); z-index: 30; -webkit-backdrop-filter: blur(2px); backdrop-filter: blur(2px); }
      .backdrop.show { display: block; }
    }
    .sidebar {
      border-right: 1px solid var(--border);
      background: var(--surface);
      backdrop-filter: blur(10px);
      padding: calc(1.25rem + env(safe-area-inset-top, 0px)) 1rem 2rem max(1rem, env(safe-area-inset-left, 0px));
      overflow-y: auto;
      -webkit-overflow-scrolling: touch;
      min-width: 0;
    }
    .brand {
      font-family: var(--font-display);
      font-size: 1.35rem;
      font-weight: 700;
      letter-spacing: 0.02em;
      line-height: 1.25;
      margin: 0 0 0.35rem;
    }
    .brand-sub {
      margin: 0 0 1rem;
      font-size: 0.88rem;
      color: var(--muted);
      line-height: 1.45;
    }
    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-bottom: 1rem;
    }
    .btn {
      font: inherit;
      cursor: pointer;
      border: 1px solid var(--border);
      background: var(--bg-elevated);
      color: var(--text);
      border-radius: 999px;
      padding: 0.35rem 0.85rem;
      font-size: 0.88rem;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      transition: background var(--transition), border-color var(--transition);
    }
    .btn:hover { border-color: var(--accent); }
    .btn:focus-visible { outline: none; box-shadow: var(--focus); }
    .search {
      width: 100%;
      margin-bottom: 0.75rem;
      padding: 0.55rem 0.75rem;
      border-radius: 10px;
      border: 1px solid var(--border);
      background: var(--bg-elevated);
      color: var(--text);
      font: inherit;
    }
    .search:focus { outline: none; box-shadow: var(--focus); border-color: transparent; }
    .nav-section-title {
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.14em;
      color: var(--muted);
      margin: 1.15rem 0 0.45rem;
      font-weight: 600;
    }
    .nav-list { list-style: none; margin: 0; padding: 0; min-width: 0; }
    .nav-item { margin: 0.15rem 0; min-width: 0; }
    .nav-link {
      display: block;
      width: 100%;
      max-width: 100%;
      min-width: 0;
      text-align: left;
      border: none;
      background: transparent;
      color: var(--text);
      font: inherit;
      font-size: 0.92rem;
      padding: 0.45rem 0.55rem;
      border-radius: 8px;
      cursor: pointer;
      line-height: 1.35;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .nav-link:hover { background: var(--accent-soft); }
    .nav-link[aria-current="page"] {
      background: var(--nav-active);
      font-weight: 600;
    }
    .nav-link.hidden { display: none; }
    main {
      width: 100%;
      min-width: 0;
      padding: calc(1.5rem + env(safe-area-inset-top, 0px)) clamp(1rem, 3.5vw, 2.75rem) calc(4rem + env(safe-area-inset-bottom, 0px)) clamp(1rem, 3.5vw, 2.75rem);
      padding-right: max(clamp(1rem, 3.5vw, 2.75rem), env(safe-area-inset-right, 0px));
    }
    @media (min-width: 1200px) {
      main {
        padding-left: clamp(1.5rem, 4vw, 3.25rem);
        padding-right: max(clamp(1.5rem, 4vw, 3.25rem), env(safe-area-inset-right, 0px));
      }
    }
    .main-header {
      display: flex;
      flex-wrap: wrap;
      align-items: flex-start;
      justify-content: space-between;
      gap: 1rem;
      margin-bottom: 1.25rem;
    }
    .doc-title {
      font-family: var(--font-display);
      font-size: clamp(1.55rem, 3vw, 2.1rem);
      font-weight: 700;
      margin: 0;
      line-height:1.25;
    }
    .doc-meta { font-size: 0.88rem; color: var(--muted); margin: 0.35rem 0 0; }
    .fab-mobile {
      display: none;
    }
    @media (max-width: 900px) {
      main { padding-top: calc(1.1rem + env(safe-area-inset-top, 0px)); }
      .fab-mobile {
        display: inline-flex;
        position: fixed;
        bottom: 1.1rem;
        right: 1.1rem;
        z-index: 50;
        border-radius: 999px;
        padding: 0.65rem 1rem;
        box-shadow: var(--shadow);
        border: 1px solid var(--border);
        background: var(--surface);
        font-weight: 600;
      }
    }
    @media (max-width: 480px) {
      body { font-size: 1rem; line-height: 1.68; }
      .doc-title { font-size: clamp(1.35rem, 6vw, 1.65rem); }
      .nav-link { padding: 0.55rem 0.6rem; min-height: 44px; }
      .btn { min-height: 44px; }
    }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
      }
    }
    .prose {
      width: 100%;
      max-width: none;
      background: var(--bg-elevated);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: clamp(1rem, 2.2vw, 1.85rem) clamp(1rem, 2.8vw, 2rem);
      box-shadow: var(--shadow);
    }
    .prose :first-child { margin-top: 0; }
    .prose :last-child { margin-bottom: 0; }
    .prose h1, .prose h2, .prose h3, .prose h4 {
      font-family: var(--font-display);
      line-height: 1.28;
      margin-top: 1.6em;
      margin-bottom: 0.55em;
    }
    .prose h1 { font-size: 1.75rem; }
    .prose h2 { font-size: 1.38rem; border-bottom: 1px solid var(--border); padding-bottom: 0.35rem; }
    .prose h3 { font-size: 1.15rem; }
    .prose p { margin: 0.85em 0; }
    .prose ul, .prose ol { padding-left: 1.35rem; }
    .prose li { margin: 0.35em 0; }
    .prose blockquote {
      margin: 1rem 0;
      padding: 0.6rem 1rem;
      border-left: 4px solid var(--accent);
      background: var(--accent-soft);
      color: var(--text);
    }
    .prose code {
      font-family: var(--font-mono);
      font-size: 0.88em;
      background: var(--code-bg);
      padding: 0.12em 0.35em;
      border-radius: 6px;
    }
    .prose pre {
      background: var(--code-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1rem 1.1rem;
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
      font-family: var(--font-mono);
      font-size: 0.86rem;
      line-height: 1.55;
    }
    .prose pre code { background: none; padding: 0; font-size: inherit; }
    .prose table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.95rem;
      margin: 1rem 0;
    }
    @media (max-width: 900px) {
      .prose { overflow-x: auto; -webkit-overflow-scrolling: touch; }
    }
    .prose th, .prose td {
      border: 1px solid var(--border);
      padding: 0.5rem 0.65rem;
      text-align: left;
    }
    .prose th { background: var(--accent-soft); }
    .codehilite { margin: 1rem 0; }
    .to-top {
      position: fixed;
      bottom: max(1.1rem, env(safe-area-inset-bottom, 0px));
      right: max(1.1rem, env(safe-area-inset-right, 0px));
      z-index: 45;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.2s ease;
    }
    .to-top.visible { opacity: 1; pointer-events: auto; }
    @media (max-width: 900px) {
      .to-top { bottom: max(4.5rem, calc(1.1rem + env(safe-area-inset-bottom, 0px))); }
    }
    .sr-only {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0,0,0,0);
      border: 0;
    }
  </style>
</head>
<body>
  <a class="sr-only" href="#content">跳到主要內容</a>
  <div class="app">
    <aside class="sidebar" id="sidebar" aria-label="章節導覽">
      <p class="brand">Harness Engineering</p>
      <p class="brand-sub">以 <code>claw-code</code> 為案例的教材 · 離線單檔，或部署到 Vercel 用 <code>public/index.html</code> 動態載入 Markdown</p>
      <div class="toolbar">
        <button type="button" class="btn" id="themeBtn" aria-label="切換深色與淺色模式">主題</button>
      </div>
      <input type="search" class="search" id="navSearch" placeholder="篩選章節標題…" autocomplete="off" />
      __NAV_HTML__
    </aside>
    <div class="backdrop" id="backdrop" hidden></div>
    <main id="content">
      <div class="main-header">
        <div>
          <h1 class="doc-title" id="docTitle">載入中…</h1>
          <p class="doc-meta" id="docMeta"></p>
        </div>
        <div class="toolbar">
          <button type="button" class="btn" id="menuBtn" aria-expanded="false" aria-controls="sidebar">目錄</button>
        </div>
      </div>
      <article class="prose" id="docBody" aria-live="polite"></article>
    </main>
  </div>
  <button type="button" class="btn to-top" id="toTop" aria-label="回到頂端">頂端</button>
  <script>
  (function () {
    var DOCS = __DOCS_JSON__;
    var TITLES = __TITLES_JSON__;
    var DEFAULT_KEY = "readme";

    var root = document.documentElement;
    var storedTheme = localStorage.getItem("he-reader-theme");
    function applyTheme(t) {
      root.setAttribute("data-theme", t);
      localStorage.setItem("he-reader-theme", t);
      var btn = document.getElementById("themeBtn");
      if (btn) btn.textContent = t === "dark" ? "淺色模式" : "深色模式";
    }
    if (storedTheme === "light" || storedTheme === "dark") {
      applyTheme(storedTheme);
    } else {
      applyTheme(window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    }
    document.getElementById("themeBtn").addEventListener("click", function () {
      var cur = root.getAttribute("data-theme") === "dark" ? "dark" : "light";
      applyTheme(cur === "dark" ? "light" : "dark");
    });

    function showDoc(key, push) {
      if (!DOCS[key]) return;
      var html = DOCS[key];
      document.getElementById("docBody").innerHTML = html;
      document.getElementById("docTitle").textContent = TITLES[key] || key;
      document.getElementById("docMeta").textContent = "";
      document.querySelectorAll(".nav-link").forEach(function (el) {
        el.setAttribute("aria-current", el.getAttribute("data-key") === key ? "page" : "false");
      });
      if (push !== false) {
        try {
          history.replaceState(null, "", "#" + encodeURIComponent(key));
        } catch (e) {}
      }
      localStorage.setItem("he-reader-last", key);
      wireInternalLinks();
      window.scrollTo({ top: 0, behavior: "smooth" });
      closeMenu();
    }

    function wireInternalLinks() {
      document.getElementById("docBody").querySelectorAll("a.internal-md-link").forEach(function (a) {
        a.addEventListener("click", function (ev) {
          var k = a.getAttribute("data-doc");
          if (!k || !DOCS[k]) return;
          ev.preventDefault();
          showDoc(k);
          var h = a.getAttribute("href");
          if (h && h.indexOf("#") > 0) {
            var id = h.slice(h.indexOf("#") + 1);
            setTimeout(function () {
              var target = document.getElementById(id);
              if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
            }, 50);
          }
        });
      });
    }

    function openMenu() {
      document.getElementById("sidebar").classList.add("open");
      document.getElementById("backdrop").classList.add("show");
      document.getElementById("backdrop").hidden = false;
      document.getElementById("menuBtn").setAttribute("aria-expanded", "true");
    }
    function closeMenu() {
      document.getElementById("sidebar").classList.remove("open");
      document.getElementById("backdrop").classList.remove("show");
      document.getElementById("backdrop").hidden = true;
      document.getElementById("menuBtn").setAttribute("aria-expanded", "false");
    }
    document.getElementById("menuBtn").addEventListener("click", function () {
      if (document.getElementById("sidebar").classList.contains("open")) closeMenu();
      else openMenu();
    });
    document.getElementById("backdrop").addEventListener("click", closeMenu);

    document.querySelectorAll(".nav-link").forEach(function (btn) {
      btn.addEventListener("click", function () {
        showDoc(btn.getAttribute("data-key"));
      });
    });

    var search = document.getElementById("navSearch");
    search.addEventListener("input", function () {
      var q = search.value.trim().toLowerCase();
      document.querySelectorAll(".nav-link").forEach(function (el) {
        var t = (el.textContent || "").toLowerCase();
        el.classList.toggle("hidden", q && t.indexOf(q) === -1);
      });
      document.querySelectorAll(".nav-section-title").forEach(function (title) {
        var section = title.nextElementSibling;
        if (!section) return;
        var any = false;
        section.querySelectorAll(".nav-link").forEach(function (el) {
          if (!el.classList.contains("hidden")) any = true;
        });
        title.style.display = q && !any ? "none" : "";
      });
    });

    var toTop = document.getElementById("toTop");
    window.addEventListener("scroll", function () {
      toTop.classList.toggle("visible", window.scrollY > 400);
    });
    toTop.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });

    var initial = DEFAULT_KEY;
    try {
      var h = location.hash ? decodeURIComponent(location.hash.slice(1)) : "";
      if (h && DOCS[h]) initial = h;
      else {
        var last = localStorage.getItem("he-reader-last");
        if (last && DOCS[last]) initial = last;
      }
    } catch (e) {}
    showDoc(initial, false);
  })();
  </script>
</body>
</html>
"""


def build_nav_html(nav_structure: list[tuple[str, str, tuple[str, ...]]], labels: dict[str, str]) -> str:
    chunks: list[str] = []
    for section_title, _sid, keys in nav_structure:
        chunks.append(f'<div class="nav-section-title">{section_title}</div>')
        chunks.append('<ul class="nav-list">')
        for k in keys:
            text = labels.get(k, k)
            title_attr = f' title="{_html_escape(text)}"'
            chunks.append(
                f'<li class="nav-item"><button type="button" class="nav-link" data-key="{k}"{title_attr}>{_html_escape(text)}</button></li>'
            )
        chunks.append("</ul>")
    return "\n".join(chunks)


def _html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def copy_markdown_to_public_md() -> None:
    """Mirror NAV .md files under public/md/ so Vercel can serve them as static assets."""
    if MD_PUBLIC.is_dir():
        shutil.rmtree(MD_PUBLIC)
    MD_PUBLIC.mkdir(parents=True, exist_ok=True)
    for _key, _nav, rel in NAV:
        src = BOOK_ROOT / rel
        dst = MD_PUBLIC / rel
        if not src.is_file():
            print(f"Missing (skip copy): {src}", file=sys.stderr)
            sys.exit(1)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    print(f"Wrote markdown mirrors under {MD_PUBLIC}")


def write_book_manifest(titles: dict[str, str]) -> None:
    """Emit JSON for public/index.html (dynamic Markdown reader) + static /md/*.md paths."""
    path_to_key: dict[str, str] = {rel.replace("\\", "/"): key for key, _nav, rel in NAV}
    keys: dict[str, str] = {key: rel.replace("\\", "/") for key, _nav, rel in NAV}
    labels: dict[str, str] = {key: nav for key, nav, _rel in NAV}
    sections: list[dict[str, object]] = [
        {"title": section_title, "keys": list(keys_tuple)}
        for section_title, _sid, keys_tuple in PART_LABELS
    ]
    manifest: dict[str, object] = {
        "version": 1,
        "keys": keys,
        "labels": labels,
        "titles": {k: titles[k] for k in titles},
        "sections": sections,
        "pathToKey": path_to_key,
    }
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_MANIFEST}")


def main() -> None:
    fragments, titles, _path_to_key = build_fragments()
    nav_html = build_nav_html(PART_LABELS, {k: titles[k] for k in titles})

    docs_json = json.dumps(fragments, ensure_ascii=False)
    titles_json = json.dumps(titles, ensure_ascii=False)

    out = HTML_SHELL.replace("__NAV_HTML__", nav_html)
    out = out.replace("__DOCS_JSON__", docs_json)
    out = out.replace("__TITLES_JSON__", titles_json)

    OUT_HTML.write_text(out, encoding="utf-8")
    size_mb = OUT_HTML.stat().st_size / (1024 * 1024)
    print(f"Wrote {OUT_HTML} ({size_mb:.2f} MB)")
    write_book_manifest(titles)
    copy_markdown_to_public_md()


if __name__ == "__main__":
    main()
