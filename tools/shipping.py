"""Draws img/shipping.svg and the links under it from the latest public releases.

    GITHUB_TOKEN=... python tools/shipping.py

Standard library only. Every public repo of the account that has releases shows up by
itself, private ones never do. Dates are absolute, so the output (and a commit) only
changes when something new ships, never just because a day passed.

App name: NAMES below, else the release title without its version ("Foo 1.2" -> "Foo"),
else the repo name. Icon: img/icon-<repo>.png if it exists, else a monogram.
"""
import base64
import datetime
import json
import os
import re
import urllib.error
import urllib.request

OWNER = "itsnotsimple"
SKIP = {OWNER}                      # the profile repo itself
NAMES = {"macglance": "MacGlance", "craftdock": "CraftDock"}
SHOW = 5
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(ROOT, "README.md")
SVG = os.path.join(ROOT, "img", "shipping.svg")
FONTS = os.path.join(ROOT, "tools", "shipping-fonts.css")
WIDTHS = os.path.join(ROOT, "tools", "shipping-widths.json")
START, END = "<!-- shipping:start -->", "<!-- shipping:end -->"
COPPER, COPPER_HI = "#D0864D", "#E59A5E"


def api(path):
    req = urllib.request.Request(f"https://api.github.com/{path}", headers={"Accept": "application/vnd.github+json"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def app_name(repo, release):
    if repo in NAMES:
        return NAMES[repo]
    title = re.sub(r"\s*v?\d+(\.\d+)*.*$", "", release.get("name") or "").strip()
    return title or repo.replace("-", " ").title()


def collect():
    rows = []
    for repo in api(f"users/{OWNER}/repos?per_page=100&type=owner"):
        if repo["private"] or repo["fork"] or repo["archived"] or repo["name"] in SKIP:
            continue
        try:
            rels = api(f"repos/{OWNER}/{repo['name']}/releases?per_page=10")
        except urllib.error.HTTPError:
            continue
        for r in rels:
            if r["draft"] or r["prerelease"]:
                continue
            when = datetime.datetime.fromisoformat(r["published_at"].replace("Z", "+00:00"))
            rows.append(dict(when=when, repo=repo["name"], name=app_name(repo["name"], r),
                             version=r["tag_name"].lstrip("vV"), url=r["html_url"]))
    rows.sort(key=lambda x: x["when"], reverse=True)
    return rows


def icon(repo, x, y, s, name):
    path = os.path.join(ROOT, "img", f"icon-{repo}.png")
    if os.path.exists(path):
        with open(path, "rb") as fh:
            data = base64.b64encode(fh.read()).decode()
        return (f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="9" fill="#191C22"/>'
                f'<image x="{x}" y="{y}" width="{s}" height="{s}" href="data:image/png;base64,{data}"/>')
    return (f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="9" fill="#1C1F26" stroke="#2A2F38"/>'
            f'<text class="mono" x="{x + s / 2}" y="{y + s / 2 + 6}" text-anchor="middle" '
            f'style="font-size:17px;fill:{COPPER_HI}">{esc(name[:1].upper())}</text>')


def render(rows):
    global ADV
    with open(WIDTHS) as fh:
        ADV = json.load(fh)
    W, X, ROW, Y0 = 900, 48, 62, 118
    shown = rows[:SHOW]
    H = Y0 + ROW * len(shown) + 22
    line_x = X + 8
    parts = []
    if len(shown) > 1:
        parts.append(f'<line class="rail" x1="{line_x}" x2="{line_x}" y1="{Y0 + 22}" y2="{Y0 + 22 + ROW * (len(shown) - 1)}" '
                     f'stroke="#2A2F38" stroke-width="2" stroke-dasharray="3 5"/>')
    for i, r in enumerate(shown):
        y = Y0 + i * ROW
        cy = y + 22
        latest = i == 0
        dot = (f'<circle class="ring" cx="{line_x}" cy="{cy}" r="7" fill="{COPPER}"/>'
               f'<circle cx="{line_x}" cy="{cy}" r="6" fill="{COPPER_HI}"/>' if latest else
               f'<circle cx="{line_x}" cy="{cy}" r="5" fill="#0A0B0E" stroke="#4A505B" stroke-width="2"/>')
        date = f"{r['when']:%b} {r['when'].day}, {r['when'].year}"
        name_w = sum(ADV.get(c, 0.6) for c in r["name"]) * 20
        pill = (f'<rect x="{X + 98 + name_w + 14 + 9.6 * len(r["version"]) + 14}" y="{cy - 11}" width="54" height="22" rx="11" '
                f'fill="none" stroke="{COPPER}" stroke-opacity=".7"/>'
                f'<text class="mono" x="{X + 98 + name_w + 14 + 9.6 * len(r["version"]) + 41}" y="{cy + 4}" text-anchor="middle" '
                f'style="font-size:11px;fill:{COPPER_HI}">latest</text>') if latest else ""
        parts.append(
            f'<g class="row" style="animation-delay:{0.2 + i * 0.09:.2f}s">{dot}'
            f'{icon(r["repo"], X + 40, cy - 18, 36, r["name"])}'
            f'<text class="name" x="{X + 92}" y="{cy + 7}">{esc(r["name"])}</text>'
            f'<text class="ver{" hi" if latest else ""}" x="{X + 98 + name_w}" y="{cy + 7}">{esc(r["version"])}</text>'
            f'{pill}<text class="date" x="{W - X}" y="{cy + 6}" text-anchor="end">{esc(date)}</text></g>')
    with open(FONTS) as fh:
        fonts = fh.read()
    css = fonts + f"""
      .t{{font-family:Brico;font-weight:800;font-size:30px;fill:#F3EEE8}}
      .t tspan{{font-family:Serif;font-style:italic;font-weight:400;fill:{COPPER_HI};font-size:33px}}
      .s{{font-family:Mono;font-size:13px;fill:#6E747F}}
      .name{{font-family:Brico;font-weight:800;font-size:20px;fill:#F1ECE6}}
      .ver{{font-family:Mono;font-size:16px;fill:#8E939C}} .hi{{fill:{COPPER_HI}}}
      .date{{font-family:Mono;font-size:14px;fill:#8E939C}} .mono{{font-family:Mono}}
      .row{{opacity:0;animation:up .6s cubic-bezier(.2,.7,.2,1) forwards}}
      @keyframes up{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
      .ring{{transform-box:fill-box;transform-origin:center;animation:ring 2.2s ease-out infinite}}
      @keyframes ring{{from{{opacity:.7;transform:scale(1)}}to{{opacity:0;transform:scale(2.6)}}}}
      @media (prefers-reduced-motion:reduce){{.row,.ring{{animation:none;opacity:1}}}}
    """
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
           f'aria-label="Recently shipped: {esc(", ".join(r["name"] + " " + r["version"] for r in shown))}">'
           f'<title>Recently shipped</title><style>{css}</style>'
           f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="21.5" fill="#0A0B0E" stroke="#1F232A"/>'
           f'<text class="t" x="{X}" y="62">Recently <tspan>shipped</tspan></text>'
           f'<text class="s" x="{W - X}" y="60" text-anchor="end">updates itself from GitHub releases</text>'
           f'<line x1="{X}" x2="{W - X}" y1="88" y2="88" stroke="#1F232A"/>'
           + "".join(parts) + "</svg>")
    with open(SVG, "w") as fh:
        fh.write(svg)


def block(rows):
    if not rows:
        return f"{START}\n{END}"
    apps, seen = [], set()
    for r in rows:
        if r["repo"] not in seen:
            seen.add(r["repo"])
            apps.append(f'<a href="https://github.com/{OWNER}/{r["repo"]}/releases">{esc(r["name"])}</a>')
    return (f'{START}\n<p align="center">\n  <a href="{rows[0]["url"]}"><img src="img/shipping.svg" width="100%" '
            f'alt="Recently shipped: {esc(", ".join(r["name"] + " " + r["version"] for r in rows[:SHOW]))}"></a>\n</p>\n'
            f'<p align="center"><sub>All releases: {" · ".join(apps)}</sub></p>\n{END}')


def main():
    rows = collect()
    render(rows)
    with open(README, encoding="utf-8") as fh:
        text = fh.read()
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block(rows), text, flags=re.S)
    with open(README, "w", encoding="utf-8") as fh:
        fh.write(new)


if __name__ == "__main__":
    main()
