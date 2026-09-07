#!/usr/bin/env python3
"""Render the site from the figures the profile repo already computed.

Booyaka101/Booyaka101 fetches HACS, npm and ESLint every morning and commits
the result as data/figures.json. Reading that rather than re-fetching keeps the
site and the profile from ever disagreeing, and means this build is one request.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html import escape
from pathlib import Path

USER = "Booyaka101"
SITE = "https://booyaka101.github.io/"
FIGURES = (
    "https://raw.githubusercontent.com/Booyaka101/Booyaka101/main/data/figures.json"
)
HERO = (
    "https://raw.githubusercontent.com/Booyaka101/Booyaka101/main/assets/hero-{}.svg"
)
ROOT = Path(__file__).resolve().parent
# Search Console ownership. The page is regenerated daily, so this has to live
# in the builder; pasting it into index.html would survive exactly one rebuild.
GOOGLE_VERIFY = "qVjvha3r2cO1Vwd_ZyE-ctq_6IDq6ePVEOO98VFVRn8"


def get(url: str, token: str | None = None) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": f"{USER}-site"})
    if token and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def repos(token: str | None) -> list[dict]:
    out = []
    for page in range(1, 3):
        rows = json.loads(
            get(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}", token)
        )
        out.extend(rows)
        if len(rows) < 100:
            break
    return out


def package_of(repo: dict) -> str | None:
    home = repo.get("homepage") or ""
    if "npmjs.com/package/" in home:
        return home.split("npmjs.com/package/", 1)[1].strip("/")
    if "pypi.org/project/" in home:
        return home.split("pypi.org/project/", 1)[1].strip("/")
    return None


def install_line(repo: dict) -> str:
    home = repo.get("homepage") or ""
    pkg = package_of(repo)
    if not pkg:
        return ""
    return f"pip install {pkg}" if "pypi.org" in home else f"npm i {pkg}"


def answers(fig: dict) -> list[dict]:
    """The three questions the crawlers exist to answer, already answered."""
    out = []
    radar, eslint, census = fig.get("radar"), fig.get("eslint"), fig.get("census")

    if radar:
        nxt = ""
        if radar.get("next_release"):
            nxt = (
                f" The next {radar['next_count']} break in Home Assistant "
                f"{radar['next_release']}."
            )
        out.append(
            {
                "id": "home-assistant",
                "q": "Which of my Home Assistant integrations are about to break?",
                "a": (
                    f"Of {radar['scanned']:,} HACS integrations crawled today against "
                    f"core {radar['core']}, {radar['affected']:,} use an API that is "
                    f"going away and {radar['clean']:,} are clean.{nxt}"
                ),
                "href": "https://booyaka101.github.io/hass-breakage-radar/",
                "cta": "Search your integrations",
                "repo": "hass-breakage-radar",
            }
        )

    if eslint:
        out.append(
            {
                "id": "eslint-10",
                "q": "Can I upgrade to ESLint 10 yet?",
                "a": (
                    f"{eslint['clean']} of {eslint['total']} plugins run clean on "
                    f"ESLint {eslint['v10']}, measured by actually executing them "
                    f"rather than reading a peer range. "
                    f"{eslint['broke']} worked on {eslint['v9']} and no longer do."
                ),
                "href": "https://booyaka101.github.io/eslint10-matrix/",
                "cta": "Check your plugins",
                "repo": "eslint10-matrix",
            }
        )

    if census:
        top = ""
        if census.get("top_name"):
            top = (
                f" The biggest is {census['top_name']} at "
                f"{census['top_downloads'] / 1e6:.0f}M installs a week."
            )
        out.append(
            {
                "id": "npm-install",
                "q": "What actually runs when I npm install?",
                "a": (
                    f"Of {census['total']:,} packages audited from a download-ranked "
                    f"sample today, {census['scripted']} run an install script and "
                    f"{census['high']} of those score HIGH risk.{top}"
                ),
                "href": f"https://github.com/{USER}/npm-install-census",
                "cta": "Read the census",
                "repo": "npm-script-lens",
            }
        )
    return out


CSS = """
:root{--bg:#05060a;--fg:#d6dbe6;--dim:#8a93a6;--line:#1a1e28;--acc:#4fb3ff}
@media (prefers-color-scheme:light){
:root{--bg:#fff;--fg:#1f2328;--dim:#59636e;--line:#d1d9e0;--acc:#0969da}
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.6 ui-monospace,'Cascadia Code',Consolas,'DejaVu Sans Mono',monospace}
.wrap{max-width:900px;margin:0 auto;padding:48px 20px 72px}
a{color:var(--acc)}
h1{font-size:22px;margin:0 0 6px;font-weight:600}
h2{font-size:13px;letter-spacing:2.2px;text-transform:uppercase;color:var(--dim);
font-weight:600;margin:56px 0 18px;padding-bottom:10px;border-bottom:1px solid var(--line)}
h3{font-size:18px;margin:0 0 8px;font-weight:600}
p{margin:0 0 12px}
.lede{color:var(--dim);margin-bottom:28px}
img.hero{width:100%;height:auto;display:block;border-radius:8px;margin:24px 0 8px}
.stamp{color:var(--dim);font-size:12px}
article{margin:0 0 30px;padding-left:16px;border-left:2px solid var(--line)}
article p{color:var(--dim)}
table{width:100%;border-collapse:collapse;font-size:14px}
th{text-align:left;color:var(--dim);font-weight:600;font-size:12px;
letter-spacing:1.4px;text-transform:uppercase;padding:0 10px 10px 0;
border-bottom:1px solid var(--line)}
td{padding:11px 10px 11px 0;border-bottom:1px solid var(--line);vertical-align:top}
td.n{text-align:right;white-space:nowrap;color:var(--acc)}
td.i{white-space:nowrap}
td.i code{color:var(--dim);font-size:13px}
td .what{display:block;color:var(--dim);font-size:13px;margin-top:3px}
footer{margin-top:56px;padding-top:18px;border-top:1px solid var(--line);
color:var(--dim);font-size:13px}
"""


def render(fig: dict, rows: list[dict], stamp: str) -> str:
    up = fig.get("upstream") or {}
    npm = fig.get("npm") or {}
    fable = fig.get("fable") or {}

    title = "Booyaka101: breaking-change watch for Home Assistant, ESLint and npm"
    desc = (
        "Which of your dependencies break in the next release, answered daily. "
        "HACS integrations against Home Assistant core, ESLint plugins actually "
        "executed against ESLint 10, and what runs at npm install time."
    )

    out = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        f"<title>{escape(title)}</title>",
        f'<meta name="description" content="{escape(desc)}">',
        f'<link rel="canonical" href="{SITE}">',
        f'<meta name="google-site-verification" content="{GOOGLE_VERIFY}">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:title" content="{escape(title)}">',
        f'<meta property="og:description" content="{escape(desc)}">',
        f'<meta property="og:url" content="{SITE}">',
        f'<meta property="og:image" content="{SITE}assets/og.png">',
        '<meta name="twitter:card" content="summary_large_image">',
        f"<style>{CSS}</style></head><body><div class=wrap>",
        "<header>",
        f"<h1>Christo · {USER}</h1>",
        '<p class="lede">Hong Kong. I build guardrails for dependency and toolchain '
        "risk. Everything below is crawled on a schedule, so the answer is already "
        "here rather than something you have to go and measure.</p>",
        '<picture>'
        '<source media="(prefers-color-scheme: light)" srcset="assets/hero-light.svg">'
        '<img class="hero" src="assets/hero-dark.svg" '
        'alt="Live project figures over a flow field seeded by today\'s date">'
        "</picture>",
        f'<p class="stamp">Rebuilt {escape(stamp)}.</p>',
        "</header><main>",
    ]

    out.append("<h2>Answers</h2>")
    for a in answers(fig):
        out.append(
            f'<article id="{a["id"]}"><h3>{escape(a["q"])}</h3>'
            f'<p>{escape(a["a"])}</p>'
            f'<p><a href="{escape(a["href"])}">{escape(a["cta"])}</a> · '
            f'<a href="https://github.com/{USER}/{a["repo"]}">source</a></p></article>'
        )

    if rows:
        weekly = npm.get("weekly")
        note = (
            f" {weekly:,} installs a week between them."
            if weekly
            else ""
        )
        out.append("<h2>What I ship</h2>")
        out.append(
            f'<p class="lede">{len(rows)} published packages.{escape(note)} '
            "Download counts include CI and mirrors, so read them as reach rather "
            "than as people.</p>"
        )
        out.append(
            "<table><thead><tr><th>Package</th><th>Install</th>"
            "<th style='text-align:right'>Weekly</th></tr></thead><tbody>"
        )
        for r in rows:
            out.append(
                f'<tr><td><a href="https://github.com/{USER}/{r["repo"]}">'
                f'{escape(r["repo"])}</a>'
                f'<span class="what">{escape(r["desc"])}</span></td>'
                f'<td class="i"><code>{escape(r["install"])}</code></td>'
                f'<td class="n">{r["weekly"]:,}</td></tr>'
            )
        out.append("</tbody></table>")

    if up.get("merged"):
        named = ", ".join(
            escape(repo.split("/")[-1]) for repo, _ in (up.get("top") or [])[:8]
        )
        out.append("<h2>Upstream</h2>")
        out.append(
            f"<p>When I depend on something and hit a real bug, I send the fix back. "
            f"<strong>{up['merged']} merged pull requests across "
            f"{up['projects']} projects</strong>, including {named}. "
            f"{up.get('open', 0)} more open. "
            f'<a href="https://github.com/issues?q=author%3A{USER}+is%3Apr">'
            f"Every PR I've opened</a>.</p>"
        )

    if fable.get("link"):
        out.append("<h2>Elsewhere</h2>")
        out.append(
            f'<p><a href="https://booyaka101.github.io/thedailyfable/">The Daily '
            f"Fable</a> is one brand-new generative piece every day, made end to end "
            f'by an AI. Latest: <a href="{escape(fable["link"])}">'
            f'{escape(fable["title"])}</a>, {escape(fable.get("date") or "")}.</p>'
        )

    out.append("</main><footer>")
    out.append(
        f'<a href="https://github.com/{USER}">GitHub</a> · '
        f'<a href="https://www.npmjs.com/~booyaka">npm</a> · '
        f'<a href="https://github.com/{USER}/{USER}">how this page is built</a>'
    )
    out.append("</footer></div></body></html>")
    return "\n".join(out)


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    fig = json.loads(get(FIGURES))

    each = (fig.get("npm") or {}).get("each") or {}
    by_pkg = {}
    for repo in repos(token):
        pkg = package_of(repo)
        if pkg:
            by_pkg[pkg] = repo

    rows = []
    for pkg, weekly in sorted(each.items(), key=lambda kv: -kv[1]):
        repo = by_pkg.get(pkg)
        if not repo:
            continue
        rows.append(
            {
                "repo": repo["name"],
                "desc": (repo.get("description") or "").strip(),
                "install": install_line(repo),
                "weekly": weekly,
            }
        )

    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    for mode in ("dark", "light"):
        try:
            (assets / f"hero-{mode}.svg").write_bytes(get(HERO.format(mode)))
        except (urllib.error.URLError, TimeoutError):
            # Keep yesterday's banner rather than shipping a broken image.
            pass

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    (ROOT / "index.html").write_text(render(fig, rows, stamp), encoding="utf-8")
    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE}sitemap.xml\n", encoding="utf-8"
    )
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{SITE}</loc><lastmod>{stamp}</lastmod></url>\n"
        "</urlset>\n",
        encoding="utf-8",
    )
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")

    print(f"built {len(rows)} package rows, {len(answers(fig))} answers, stamp {stamp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
