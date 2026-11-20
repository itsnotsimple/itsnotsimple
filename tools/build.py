"""Builds every image for the itsnotsimple GitHub profile.

Each SVG is self-contained: fonts are subset and embedded as WOFF2, images are inlined
and all motion is CSS, because GitHub shows README images through a sandboxed <img>
that loads nothing external and runs no script.

    python build.py <fonts dir> <icons dir> <out dir>

Outputs
    header.svg              animated banner: it's ~~not~~ simple.
    card-<project>.svg      one live card per project
    footer.svg              closing strip
    avatar.svg              the logo, for the GitHub avatar (rasterised to PNG separately)
    social-<repo>.svg       1280x640 link previews (rasterised to PNG separately)
"""
import base64, os, sys
from fonts import Font

FONTS, ICONS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)

COPPER, COPPER_HI, INK, BG = "#D0864D", "#E59A5E", "#F3EEE8", "#0A0B0E"
GREEN = "#3FB950"
# The avatar's 5x5 identicon is the brand mark.
MARK = ["##.##", ".#.#.", ".#.#.", "#...#", "#.#.#"]


def F(name, **axes):
    return Font(os.path.join(FONTS, name), axes or None)


def data_uri(path):
    ext = os.path.splitext(path)[1].lstrip(".").replace("jpg", "jpeg")
    with open(path, "rb") as fh:
        return f"data:image/{ext};base64," + base64.b64encode(fh.read()).decode()


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def write(name, w, h, css, body, title):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
           f'role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>'
           f'<style>{css}</style>{body}</svg>')
    with open(os.path.join(OUT, name), "w") as fh:
        fh.write(svg)
    print(f"{name:26} {len(svg) / 1024:6.1f} KB")


def mark(x, y, cell, fill, cls="", gap=0, rx=0):
    out, i = [], 0
    for r, row in enumerate(MARK):
        for c, ch in enumerate(row):
            if ch == "#":
                out.append(f'<rect class="{cls}" style="animation-delay:{0.04 * i:.2f}s" x="{x + c * cell + gap / 2}" '
                           f'y="{y + r * cell + gap / 2}" width="{cell - gap}" height="{cell - gap}" rx="{rx}" fill="{fill}"/>')
                i += 1
    return "".join(out)


# Fonts: Bricolage Grotesque (display + text), Instrument Serif italic (the word "simple"),
# JetBrains Mono (labels). Each Font object records the characters it is asked to draw.
def fonts():
    return dict(
        bold=F("BricolageGrotesque.ttf", wght=800, opsz=96, wdth=100),
        text=F("BricolageGrotesque.ttf", wght=450, opsz=14, wdth=100),
        serif=F("InstrumentSerif-Italic.ttf"),
        mono=F("JetBrainsMono.ttf", wght=450),
    )


ANIM = """
  .up{opacity:0;animation:up .8s cubic-bezier(.2,.7,.2,1) forwards}
  @keyframes up{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
  .pop{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .5s cubic-bezier(.3,1.6,.5,1) forwards}
  @keyframes pop{from{opacity:0;transform:scale(.2)}to{opacity:1;transform:none}}
"""

GLOW_DEFS = """
  <filter id="blur" filterUnits="userSpaceOnUse" x="-400" y="-400" width="2400" height="1600"><feGaussianBlur stdDeviation="{sd}"/></filter>
  <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1.1" fill="#fff"/></pattern>
"""


# ─────────────────────────────── header ───────────────────────────────

def header():
    f = fonts()
    bold, text, serif, mono = f["bold"], f["text"], f["serif"], f["mono"]
    W, H = 900, 330
    X, BASE, S = 58, 200, 88
    w_its = bold.width("it’s ", S)
    w_not = bold.width("not ", S)
    w_not_word = bold.width("not", S)
    nx0, nx1 = X + w_its - 6, X + w_its + w_not_word + 6
    sy = BASE - S * 0.27
    strike = f"M{nx0:.1f} {sy + 4:.1f} C {nx0 + 40:.1f} {sy - 6:.1f}, {nx1 - 60:.1f} {sy + 8:.1f}, {nx1:.1f} {sy - 3:.1f}"

    # Right side, looping forever: the mark's squares scatter into chaos, then snap back into place.
    import random
    rnd = random.Random(11)
    CX, CY, C = 735, 162, 30
    ox, oy = CX - 2.5 * C, CY - 2.5 * C
    sq, kf, i = [], [], 0
    for r, row in enumerate(MARK):
        for c, ch in enumerate(row):
            if ch != "#":
                continue
            ang = rnd.uniform(0, 6.283)
            dist = rnd.uniform(70, 125)
            import math
            dx, dy = math.cos(ang) * dist, math.sin(ang) * dist
            dx = max(dx, -70)  # never drift over the headline
            dy = max(min(dy, 110), -110)
            rot = rnd.choice([-1, 1]) * rnd.uniform(60, 200)
            sc = rnd.uniform(.35, .7)
            far = f"transform:translate({dx:.0f}px,{dy:.0f}px) rotate({rot:.0f}deg) scale({sc:.2f});opacity:.35"
            kf.append(f"@keyframes s{i}{{0%,8%{{{far}}}38%,74%{{transform:none;opacity:1}}100%{{{far}}}}}")
            sq.append(f'<rect class="sq" style="animation-name:s{i};animation-delay:-{0.07 * i:.2f}s" '
                      f'x="{ox + c * C + 2}" y="{oy + r * C + 2}" width="{C - 4}" height="{C - 4}" rx="5" fill="url(#cg)"/>')
            i += 1
    orbit = (f'<g class="orb1" style="transform-origin:{CX}px {CY}px"><circle cx="{CX}" cy="{CY}" r="118" fill="none" stroke="{COPPER}" stroke-opacity=".28" stroke-dasharray="2 9"/>'
             f'<circle cx="{CX + 118}" cy="{CY}" r="4" fill="{COPPER_HI}"/></g>'
             f'<g class="orb2" style="transform-origin:{CX}px {CY}px"><circle cx="{CX}" cy="{CY}" r="92" fill="none" stroke="#8FA8FF" stroke-opacity=".2" stroke-dasharray="14 10"/>'
             f'<circle cx="{CX}" cy="{CY - 92}" r="3" fill="#8FA8FF"/></g>')
    right = (f'<g class="up" style="animation-delay:.4s"><defs><linearGradient id="cg" x1="0" y1="0" x2="0" y2="1">'
             f'<stop offset="0" stop-color="#F0AE74"/><stop offset="1" stop-color="#C47437"/></linearGradient></defs>'
             f'{orbit}{"".join(sq)}</g>')
    right_css = "".join(kf) + (
        ".sq{transform-box:fill-box;transform-origin:center;animation-duration:6s;animation-iteration-count:infinite;"
        "animation-timing-function:cubic-bezier(.65,0,.35,1)}"
        ".orb1{animation:spin 18s linear infinite}.orb2{animation:spin 26s linear infinite reverse}"
        "@keyframes spin{to{transform:rotate(360deg)}}"
        "@media (prefers-reduced-motion:reduce){.sq,.orb1,.orb2{animation:none!important}}")

    body = f"""
    <defs><clipPath id="clip"><rect width="{W}" height="{H}" rx="22"/></clipPath>{GLOW_DEFS.format(sd=55)}</defs>
    <g clip-path="url(#clip)">
      <rect width="{W}" height="{H}" fill="{BG}"/>
      <g filter="url(#blur)">
        <circle class="blob1" cx="760" cy="290" r="170" fill="{COPPER}" opacity=".38"/>
        <circle class="blob2" cx="560" cy="30" r="120" fill="#3D63DD" opacity=".22"/>
      </g>
      <rect width="{W}" height="{H}" fill="url(#dots)" opacity=".05"/>
    </g>
    <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="21.5" fill="none" stroke="#1F232A"/>
    {mark(X, 40, 7, COPPER, "pop")}
    {right}
    <text class="mono up" style="animation-delay:.3s;fill:#8A8F99" x="{X + 50}" y="70">{mono.use("github.com/itsnotsimple")}</text>
    <g class="up" style="animation-delay:.5s">
      <text class="h" x="{X}" y="{BASE}">{bold.use("it’s")}</text>
      <g id="not"><text class="h" x="{X + w_its:.1f}" y="{BASE}">{bold.use("not")}</text>
        <path id="strike" d="{strike}" fill="none" stroke="{COPPER_HI}" stroke-width="8" stroke-linecap="round"/></g>
      <text id="simple" class="s" x="{X + w_its + w_not:.1f}" y="{BASE}">{serif.use("simple")}<tspan dx="-9">{serif.use(".")}</tspan></text>
    </g>
    <text class="t up" style="animation-delay:3.2s" x="{X}" y="{BASE + 52}">{text.use("Kristiyan · I build the hard part, so it feels simple.")}</text>
    <text class="mono foot up" style="animation-delay:3.5s" x="{X}" y="{H - 34}">{mono.use("macOS apps   ·   desktop tools   ·   self-hosted servers   ·   Bulgaria")}</text>
    """
    css = (bold.face("Brico", 800) + text.face("BricoText", 450) + serif.face("Serif", 400, "italic")
           + mono.face("Mono", 450) + ANIM + f"""
      .h{{font-family:Brico;font-weight:800;font-size:{S}px;fill:{INK};font-kerning:none}}
      .s{{font-family:Serif;font-style:italic;font-size:{S * 1.08:.0f}px;fill:{COPPER_HI}}}
      .t{{font-family:BricoText;font-size:22px;fill:#AEB2BB}}
      .mono{{font-family:Mono;font-size:13px}}
      .lab{{fill:#6E747F;font-size:11px}} .val{{fill:#E9E4DD;font-size:12px}}
      .foot{{fill:#6E747F;letter-spacing:.02em}}
      #strike{{stroke-dasharray:420;stroke-dashoffset:420;animation:draw .55s 1.5s cubic-bezier(.6,0,.3,1) forwards}}
      @keyframes draw{{to{{stroke-dashoffset:0}}}}
      #not{{animation:gone .5s 2.45s ease-in forwards}}
      @keyframes gone{{to{{opacity:0;transform:translateY(-10px)}}}}
      #simple{{animation:slide .7s 2.75s cubic-bezier(.7,0,.2,1) forwards}}
      @keyframes slide{{to{{transform:translateX(-{w_not:.1f}px)}}}}
      .state{{opacity:0;animation:cycle 6.4s infinite}}
      @keyframes cycle{{0%,22%{{opacity:1}}25%,100%{{opacity:0}}}}
      .blob1{{animation:drift1 14s ease-in-out infinite alternate}}
      .blob2{{animation:drift2 11s ease-in-out infinite alternate}}
      @keyframes drift1{{to{{transform:translate(-90px,-30px)}}}}
      @keyframes drift2{{to{{transform:translate(60px,40px)}}}}
      @media (prefers-reduced-motion:reduce){{*{{animation-duration:0s!important;animation-delay:0s!important}}}}
    """ + right_css)
    write("header.svg", W, H, css, body, "It’s not simple. Kristiyan builds the hard part, so it feels simple.")


# ─────────────────────────────── cards ───────────────────────────────

PROJECTS = {
    "macglance": dict(
        name="MacGlance", icon="mg-icon.png", tags="macOS  ·  Swift  ·  native",
        desc=["A featherweight menu bar monitor for Apple Silicon:",
              "CPU, GPU, RAM, watts, temperatures, disk, network."],
        stats=[("0.5%", "of one core"), ("<20 MB", "of memory"), ("EN · BG", "languages")],
        cta="Download for macOS  →", live="spark"),
    "craftdock": dict(
        name="CraftDock", icon="cd-icon.png", tags="Windows  ·  macOS  ·  Electron",
        desc=["Host a Minecraft server on your own computer in",
              "60 seconds, then run it from your phone."],
        stats=[("1 click", "play with friends"), ("0 €", "no subscription"), ("1.8–26.x", "Java editions")],
        cta="Download for Windows & Mac  →", live=("ONLINE 3/20", GREEN)),
    "musclemap": dict(
        name="MuscleMap AI", icon="mm-icon.png", tags="React  ·  Node  ·  MongoDB  ·  AI",
        desc=["Tap a muscle, get the exercises. An interactive",
              "body map with an AI coach, diet plans and BMI."],
        stats=[("Llama 3.1", "AI gym coach"), ("Stripe", "Pro membership"), ("EN · BG", "languages")],
        cta="Open the live app  →", live=("LIVE", GREEN)),
    "apmedia": dict(
        name="AP Media", icon="ap-icon.png", tags="React  ·  WebGL  ·  client work",
        desc=["A cinematic portfolio for a video editor: a custom",
              "WebGL shader that stays smooth even on phones."],
        stats=[("GLSL", "plasma shader"), ("60 FPS", "on mobile"), ("EN · BG", "languages")],
        cta="apmedia.my  →", live=("LIVE", GREEN)),
}


def cards():
    W, H = 440, 250
    for key, p in PROJECTS.items():
        f = fonts()
        bold, text, mono = f["bold"], f["text"], f["mono"]
        tiles = []
        for i, (big, small) in enumerate(p["stats"]):
            tx = 24 + i * 134
            tiles.append(f'<rect x="{tx}" y="142" width="124" height="54" rx="10" fill="#15181D" stroke="#22262E"/>'
                         f'<text class="big" x="{tx + 12}" y="166">{bold.use(big)}</text>'
                         f'<text class="small" x="{tx + 12}" y="185">{mono.use(small)}</text>')
        if p["live"] == "spark":
            pts = [14, 20, 12, 26, 18, 30, 16, 22, 34, 19, 24, 15, 28, 21, 12, 18]
            step, n = 8, 16
            d = "M" + " L".join(f"{i * step} {40 - v}" for i, v in enumerate(pts + pts[:1]))
            path = f'fill="none" stroke="{COPPER_HI}" stroke-width="2" stroke-linejoin="round"'
            live = (f'<g transform="translate(316 26)"><clipPath id="sp"><rect width="100" height="36"/></clipPath>'
                    f'<g clip-path="url(#sp)"><g class="scroll"><path d="{d}" {path}/>'
                    f'<path d="{d}" transform="translate({n * step} 0)" {path}/></g></g></g>')
            extra = f".scroll{{animation:scroll 4s linear infinite}}@keyframes scroll{{to{{transform:translateX(-{n * step}px)}}}}"
        else:
            label, col = p["live"]
            lw = mono.width(label, 10.5)
            lx = W - 24 - lw - 18
            live = (f'<g transform="translate({lx:.1f} 34)"><circle class="pulse" cx="6" cy="6" r="6" fill="{col}"/>'
                    f'<circle cx="6" cy="6" r="4" fill="{col}"/>'
                    f'<text class="small" x="18" y="10" style="fill:{col}">{mono.use(label)}</text></g>')
            extra = (".pulse{transform-box:fill-box;transform-origin:center;animation:pulse 1.6s ease-out infinite}"
                     "@keyframes pulse{from{opacity:.7;transform:scale(.6)}to{opacity:0;transform:scale(2.2)}}")
        body = f"""
        <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="18" fill="#0E1014" stroke="#22262E"/>
        <rect x="24" y="22" width="56" height="56" rx="13" fill="#191C22"/>
        <image x="24" y="22" width="56" height="56" href="{data_uri(os.path.join(ICONS, p['icon']))}"/>
        <text class="name" x="94" y="50">{bold.use(p['name'])}</text>
        <text class="tags" x="95" y="70">{mono.use(p['tags'])}</text>
        {live}
        <text class="desc" x="24" y="110">{text.use(p['desc'][0])}</text>
        <text class="desc" x="24" y="129">{text.use(p['desc'][1])}</text>
        {"".join(tiles)}
        <text class="cta" x="24" y="226">{mono.use(p['cta'])}</text>
        """
        css = (bold.face("Head", 800) + text.face("Body", 450) + mono.face("Mono", 450) + f"""
          .name{{font-family:Head;font-weight:800;font-size:28px;fill:#F1ECE6}}
          .tags{{font-family:Mono;font-size:11.5px;fill:#757A85}}
          .desc{{font-family:Body;font-size:15px;fill:#C3C7CF}}
          .big{{font-family:Head;font-weight:800;font-size:19px;fill:{COPPER_HI}}}
          .small{{font-family:Mono;font-size:10.5px;fill:#757A85}}
          .cta{{font-family:Mono;font-size:12.5px;fill:{COPPER_HI}}}
          {extra}
          @media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}""")
        write(f"card-{key}.svg", W, H, css, body, f"{p['name']}: {' '.join(p['desc'])}")


# ─────────────────────────────── footer ───────────────────────────────

def footer():
    f = fonts()
    mono = f["mono"]
    W, H = 900, 70
    txt = mono.use("itsnotsimple  ·  made in Bulgaria  ·  thanks for scrolling this far")
    tw = mono.width("itsnotsimple  ·  made in Bulgaria  ·  thanks for scrolling this far", 12)
    x0 = (W - tw - 34) / 2
    body = f"""
      <line x1="0" x2="{W}" y1="20" y2="20" stroke="#8B949E" stroke-opacity=".25" stroke-dasharray="2 6"/>
      <rect x="{x0 - 14:.0f}" y="6" width="{tw + 62:.0f}" height="28" fill="{BG}" rx="14"/>
      {mark(x0, 13, 3, COPPER, "pop")}
      <text x="{x0 + 24:.1f}" y="25" class="m">{txt}</text>"""
    css = mono.face("Mono", 450) + ANIM + ".m{font-family:Mono;font-size:12px;fill:#8B949E}"
    write("footer.svg", W, 40, css, body, "itsnotsimple, made in Bulgaria")


# ─────────────────────────────── avatar ───────────────────────────────

def avatar():
    S = 512
    cell = 64
    off = (S - 5 * cell) / 2
    body = f"""
    <defs>
      <radialGradient id="g" cx=".72" cy=".78" r=".75"><stop offset="0" stop-color="{COPPER}" stop-opacity=".45"/><stop offset="1" stop-color="{COPPER}" stop-opacity="0"/></radialGradient>
      <linearGradient id="c" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F0AE74"/><stop offset="1" stop-color="#C47437"/></linearGradient>
    </defs>
    <rect width="{S}" height="{S}" fill="{BG}"/>
    <rect width="{S}" height="{S}" fill="url(#g)"/>
    {mark(off, off, cell, "url(#c)", gap=6, rx=7)}
    """
    write("avatar.svg", S, S, "", body, "itsnotsimple logo")


# ─────────────────────────── social previews ───────────────────────────

def social(name, title, line1, line2, icon, chips, shot=None, align="xMidYMid"):
    f = fonts()
    bold, text, mono = f["bold"], f["text"], f["mono"]
    W, H = 1280, 640
    x = 80
    chip_svg, cx = [], x
    for c in chips:
        w = mono.width(c, 18) + 32
        chip_svg.append(f'<rect x="{cx}" y="470" width="{w:.0f}" height="44" rx="22" fill="#15181D" stroke="#2A2F38"/>'
                        f'<text class="chip" x="{cx + 16}" y="498">{mono.use(c)}</text>')
        cx += w + 12
    tsize = min(96, 590 / bold.width(title, 1))
    pic = ""
    if shot:
        pic = (f'<g transform="translate(700 70) rotate(-3)"><rect x="-6" y="-6" width="572" height="514" rx="22" fill="#1A1D23"/>'
               f'<image width="560" height="491" href="{data_uri(shot)}" preserveAspectRatio="{align} slice" clip-path="url(#shot)"/></g>')
    body = f"""
    <defs>{GLOW_DEFS.format(sd=90)}<clipPath id="shot"><rect width="560" height="491" rx="16"/></clipPath></defs>
    <rect width="{W}" height="{H}" fill="{BG}"/>
    <g filter="url(#blur)"><circle cx="1100" cy="600" r="300" fill="{COPPER}" opacity=".35"/><circle cx="300" cy="0" r="220" fill="#3D63DD" opacity=".18"/></g>
    <rect width="{W}" height="{H}" fill="url(#dots)" opacity=".05"/>
    {pic}
    <image x="{x}" y="96" width="120" height="120" href="{data_uri(os.path.join(ICONS, icon.replace(".png", "-lg.png")))}"/>
    <text class="t" x="{x}" y="330" style="font-size:{tsize:.0f}px">{bold.use(title)}</text>
    <text class="d" x="{x}" y="392">{text.use(line1)}</text>
    <text class="d" x="{x}" y="430">{text.use(line2)}</text>
    {"".join(chip_svg)}
    {mark(x, 566, 6, COPPER)}<text class="u" x="{x + 44}" y="592">{mono.use("github.com/itsnotsimple/" + name)}</text>
    """
    css = (bold.face("Head", 800) + text.face("Body", 450) + mono.face("Mono", 450) + f"""
      .t{{font-family:Head;font-weight:800;font-size:96px;fill:{INK}}}
      .d{{font-family:Body;font-size:30px;fill:#B9BDC6}}
      .chip{{font-family:Mono;font-size:18px;fill:#D9D4CC}}
      .u{{font-family:Mono;font-size:20px;fill:#8A8F99}}""")
    write(f"social-{name}.svg", W, H, css, body, title)


header()
cards()
footer()
avatar()
social("macglance", "MacGlance", "A light menu bar monitor", "for Apple Silicon Macs.", "mg-icon.png",
       ["CPU", "GPU", "RAM", "Watts", "Temps", "SSD"],
       shot=os.path.join(ICONS, "shot-macglance.jpg"))
social("craftdock", "CraftDock", "Your own Minecraft server in 60 seconds,", "on Windows or Mac. Run it from your phone.",
       "cd-icon.png", ["Paper", "Fabric", "Purpur", "Vanilla", "No subscription"],
       shot=os.path.join(ICONS, "shot-craftdock.jpg"))
social("muscle-map-web-app", "MuscleMap AI", "Tap a muscle, get the exercises.", "AI gym coach, diet plans and BMI.",
       "mm-icon.png", ["React", "Node", "MongoDB", "Llama 3.1", "EN · BG"],
       shot=os.path.join(ICONS, "shot-musclemap.jpg"))
social("portfolio-website", "AP Media", "A cinematic portfolio for a video", "editor. Live at apmedia.my",
       "ap-icon.png", ["React 19", "WebGL", "GLSL", "Framer Motion"],
       shot=os.path.join(ICONS, "shot-apmedia.jpg"), align="xMinYMid")
