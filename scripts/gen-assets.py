#!/usr/bin/env python3
"""Regenerate the README's SVG assets in the SAMBANGGOLD palette.

    python3 scripts/gen-assets.py

Every composed asset (hero, badges, nav chips, ticker, divider, metrics chart,
roadmap, spinner) is written from code here, so the look is reproducible. The
eighteen product icons keep their glyphs and are recoloured in place by vertical.
Motion is SMIL wherever this file draws it, because that is what survives
GitHub's `<img>`; the embedded mascot keeps Sam's CSS keyframes, which GitHub
also renders. Anton is embedded as base64 where it is drawn — an `<img>` SVG
cannot load an external font.
"""

import base64
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
sys.path.insert(0, str(ROOT))
from app.brand import TOKENS as P  # noqa: E402
from app.products import PRODUCTS  # noqa: E402

FONT_B64 = base64.b64encode((ASSETS / "brand" / "anton.woff2").read_bytes()).decode()
SANS = "Inter,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

# Light variant of the palette, for the two <picture> sources.
LIGHT = dict(P, bg="#f5f7fb", surface="#ffffff", surface2="#eef1f6", border="#d5dbe6",
             fg="#0b0e14", muted="#5b6572", graphite="#e9ecf2")

# One accent per vertical. Gold family first; win/loss keep their meaning.
VERTICAL_ACCENT = {
    "Gold": P["gold"], "Gold IB": P["gold"], "Forex": P["gold2"], "Crypto": "#a87d0f",
    "Prop firm": P["chrome"], "Social": P["chrome"], "Stocks": P["win"],
    "Security": P["loss"], "Fintech": P["loss"],
}
OLD_ACCENTS = ("#f0b429", "#00e5ff", "#ff4d6d", "#a78bfa", "#34d399", "#38bdf8")


def font_style(extra=""):
    return ("<style>@font-face{font-family:'Anton';src:url(data:font/woff2;base64,%s) format('woff2')}"
            ".disp{font-family:Anton,Impact,'Arial Narrow',sans-serif;font-style:italic}%s</style>" % (FONT_B64, extra))


def chrome_grad(gid, light=False):
    if light:
        return ('<linearGradient id="%s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3a4250"/>'
                '<stop offset=".5" stop-color="#0b0e14"/><stop offset="1" stop-color="#4b5462"/></linearGradient>' % gid)
    return ('<linearGradient id="%s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/>'
            '<stop offset=".45" stop-color="#d9dee6"/><stop offset=".5" stop-color="#8f99a8"/>'
            '<stop offset="1" stop-color="#b7c0ce"/></linearGradient>' % gid)


def gold_grad(gid):
    return ('<linearGradient id="%s" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f5d76e"/>'
            '<stop offset=".5" stop-color="#d4af37"/><stop offset="1" stop-color="#8a6d1f"/></linearGradient>' % gid)


def wordmark(x, y, size, chrome_id, gold_id):
    return ('<text x="%d" y="%d" class="disp" font-size="%d" letter-spacing="1"><tspan fill="url(#%s)">SAMBANG</tspan>'
            '<tspan fill="url(#%s)">GOLD</tspan></text>' % (x, y, size, chrome_id, gold_id))


def glyph(x, y, chrome_id):
    return ('<g transform="translate(%d %d)"><circle cx="22" cy="22" r="21" fill="#050609"/>'
            '<circle cx="22" cy="22" r="20" fill="none" stroke="%s" stroke-opacity=".35" stroke-width="3"/>'
            '<circle cx="22" cy="22" r="20" fill="none" stroke="%s" stroke-width="3" stroke-linecap="round" stroke-dasharray="40 86">'
            '<animateTransform attributeName="transform" type="rotate" from="0 22 22" to="360 22 22" dur="3s" repeatCount="indefinite"/></circle>'
            '<text x="22" y="28" text-anchor="middle" class="disp" font-size="16"><tspan fill="#e5e7eb">SB</tspan><tspan fill="%s">G</tspan></text></g>'
            % (x, y, P["gold"], P["gold2"], P["gold"]))


def mascot_inline(x, y, scale):
    """Sam's mascot with every id, class and keyframe prefixed so it can live inside another SVG."""
    src = (ASSETS / "brand" / "mascot.svg").read_text()
    body = src[src.index(">", src.index("<svg")) + 1: src.rindex("</svg>")]
    for name in ("chromeCap", "chrome", "goldBall", "goldFace", "goldTop", "goldSide", "graphite", "visor", "flash", "soft"):
        body = body.replace('id="%s"' % name, 'id="m-%s"' % name).replace("url(#%s)" % name, "url(#m-%s)" % name)
    for cls in ("arm", "torso", "shard", "flash", "bar"):
        body = body.replace('class="%s"' % cls, 'class="m-%s"' % cls).replace(".%s{" % cls, ".m-%s{" % cls)
        body = body.replace(".%s," % cls, ".m-%s," % cls)
    for kf in ("swing", "lean", "burst", "flash", "barhit"):
        body = body.replace("@keyframes %s{" % kf, "@keyframes m-%s{" % kf).replace("animation:%s " % kf, "animation:m-%s " % kf)
    return '<g transform="translate(%d %d) scale(%s)">%s</g>' % (x, y, scale, body)


# --------------------------------------------------------------------------- #
# Composed assets
# --------------------------------------------------------------------------- #

def hero(light=False):
    c = LIGHT if light else P
    live = sum(1 for p in PRODUCTS if p.slug in ("gold-watch", "prop-calculator", "ib-revenue-calculator"))
    bg = ('<stop offset="0" stop-color="%s"/><stop offset=".55" stop-color="%s"/><stop offset="1" stop-color="%s"/>'
          % ((c["bg"], c["surface"], "#1a1607") if not light else (c["bg"], c["graphite"], "#f3ead0")))
    grid_op = ".18" if not light else ".28"
    candles = ""
    for i, (x, y, h, up) in enumerate(((700, 118, 34, True), (735, 150, 24, False), (770, 104, 50, True), (820, 138, 28, True))):
        col = P["win"] if up else P["loss"]
        dur = 3.6 + i * .5
        candles += ('<g transform="translate(%d %d)"><g><animateTransform attributeName="transform" type="translate" values="0 0;0 -10;0 0" dur="%.1fs" repeatCount="indefinite"/>'
                    '<line x1="0" y1="%d" x2="0" y2="%d" stroke="%s" stroke-width="2"/><rect x="-7" y="%d" width="14" height="%d" rx="2" fill="%s"/></g></g>'
                    % (x, y, dur, -h - 8, h + 8, col, -h // 2, h, col))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 340" width="1280" height="340" role="img" aria-label="SAMBANGGOLD — 18 gold tools, a Telegram bot and a dashboard for every one">'
            '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">%s</linearGradient>%s%s'
            '<radialGradient id="glow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="%s" stop-opacity=".5"/><stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>'
            '<linearGradient id="line" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="%s" stop-opacity="0"/><stop offset=".2" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>'
            '<linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="%s" stop-opacity="0"/><stop offset=".5" stop-color="%s" stop-opacity=".9"/><stop offset="1" stop-color="%s" stop-opacity="0"/>'
            '<animateTransform attributeName="gradientTransform" type="translate" values="-1 0;1 0;-1 0" dur="9s" repeatCount="indefinite"/></linearGradient>'
            '<filter id="blur"><feGaussianBlur stdDeviation="18"/></filter><clipPath id="clip"><rect width="1280" height="340" rx="24"/></clipPath>%s</defs>'
            '<g clip-path="url(#clip)"><rect width="1280" height="340" fill="url(#bg)"/>'
            # perspective floor grid, scrolling toward the viewer
            '<g opacity="%s" stroke="%s" stroke-width="1"><g><animateTransform attributeName="transform" type="translate" values="0 0;0 28" dur="2.2s" repeatCount="indefinite"/>'
            '<line x1="0" y1="224" x2="1280" y2="224"/><line x1="0" y1="252" x2="1280" y2="252"/><line x1="0" y1="280" x2="1280" y2="280"/><line x1="0" y1="308" x2="1280" y2="308"/><line x1="0" y1="336" x2="1280" y2="336"/></g>'
            '<line x1="640" y1="196" x2="640" y2="340"/><line x1="640" y1="196" x2="448" y2="340"/><line x1="640" y1="196" x2="256" y2="340"/><line x1="640" y1="196" x2="0" y2="340"/>'
            '<line x1="640" y1="196" x2="832" y2="340"/><line x1="640" y1="196" x2="1024" y2="340"/><line x1="640" y1="196" x2="1280" y2="340"/></g>'
            '<rect x="0" y="186" width="1280" height="60" fill="url(#bg)" opacity=".9"/>'
            '<ellipse cx="1000" cy="180" rx="260" ry="140" fill="url(#glow)" filter="url(#blur)"/>'
            '%s%s'
            # equity curve drawing itself
            '<path d="M560,296 C620,290 660,268 700,248 S780,238 820,214 S880,206 920,176 S990,160 1040,132 S1110,100 1180,66" fill="none" stroke="url(#line)" stroke-width="3" stroke-linecap="round" stroke-dasharray="1400" stroke-dashoffset="1400">'
            '<animate attributeName="stroke-dashoffset" from="1400" to="0" dur="4s" fill="freeze"/></path>'
            '<circle cx="1180" cy="66" r="7" fill="%s"><animate attributeName="r" values="6;9;6" dur="1.6s" repeatCount="indefinite"/><animate attributeName="opacity" values=".35;1;.35" dur="1.6s" repeatCount="indefinite"/></circle>'
            # brand text
            '<g transform="translate(60 74)">%s%s'
            '<text x="0" y="66" class="disp" font-size="56" fill="url(#chromeW)">GOLD TOOLS,</text>'
            '<text x="0" y="118" class="disp" font-size="56" fill="url(#gold)">TWO SURFACES.</text>'
            '<text x="0" y="150" font-family="%s" font-size="17" fill="%s">18 products · Telegram bot + dashboard on one account · free tier on every one · Bahasa Melayu &amp; English</text>'
            '<g transform="translate(0 176)" font-family="%s" font-size="13">'
            '<rect x="0" y="0" width="104" height="30" rx="15" fill="none" stroke="%s" stroke-opacity=".6"/><circle cx="18" cy="15" r="5" fill="%s"><animate attributeName="opacity" values=".35;1;.35" dur="1.6s" repeatCount="indefinite"/></circle><text x="32" y="19" fill="%s">%d LIVE</text>'
            '<rect x="116" y="0" width="186" height="30" rx="15" fill="none" stroke="%s" stroke-opacity=".6"/><text x="131" y="19" fill="%s">18 TOOLS · FREE TIER</text>'
            '<rect x="314" y="0" width="128" height="30" rx="15" fill="none" stroke="#26A5E4" stroke-opacity=".6"/><text x="329" y="19" fill="#26A5E4">Telegram bot</text></g></g>'
            '<rect width="1280" height="3" fill="url(#sweep)"/><rect y="337" width="1280" height="3" fill="url(#sweep)"/></g></svg>'
            % (bg, chrome_grad("chromeW", light), gold_grad("gold"), P["gold"], P["gold"], P["gold"], P["gold"], P["gold2"],
               P["gold"], P["gold2"], P["gold"], font_style(),
               grid_op, P["gold"],
               mascot_inline(880, 12, ".8"), candles,
               P["gold2"],
               glyph(0, -48, "chromeW"), wordmark(58, -12, 38, "chromeW", "gold"),
               SANS, c["muted"], MONO,
               P["win"], P["win"], P["win"], live, P["gold"], P["gold"]))


def badges():
    chips = [("PRODUCTS", "3 live · 9 shipped · 9 proposed", P["gold"]), ("PLATFORM", "Telegram + dashboard", P["chrome"]),
             ("FREE TIER", "all 18", P["win"]), ("STACK", "Python 3.12 / Flask", P["gold2"]), ("LICENSE", "MIT", P["muted"])]
    out, x = [], 0
    for i, (k, v, col) in enumerate(chips):
        kw = int(len(k) * 7.2) + 22
        vw = int(len(v) * 6.4) + 24
        w = kw + vw
        out.append('<g transform="translate(%d,0)"><rect width="%d" height="30" rx="15" fill="%s" stroke="%s" stroke-opacity=".45"/>'
                   '<rect width="%d" height="30" rx="15" fill="%s" fill-opacity=".14"/>'
                   '<text x="%d" y="20" text-anchor="middle" font-family="%s" font-size="11" fill="%s" letter-spacing="1">%s</text>'
                   '<text x="%d" y="20" text-anchor="middle" font-family="%s" font-size="11" fill="%s">%s</text>'
                   '<animate attributeName="opacity" from="0" to="1" begin="%.2fs" dur="0.6s" fill="freeze"/></g>'
                   % (x, w, P["surface"], col, kw, col, kw // 2, SANS, col, k, kw + vw // 2, SANS, P["fg"], v, i * .25))
        x += w + 12
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d 30" width="%d" height="30" role="img" aria-label="3 live, 9 shipped, 9 proposed; Telegram and dashboard; free tier on all 18; Python 3.12 Flask; MIT">%s</svg>'
            % (x - 12, x - 12, "".join(out)))


def nav_chip(label):
    w = int(len(label) * 7.4) + 44
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d 38" width="%d" height="38" role="img" aria-label="%s">'
            '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0%%" stop-color="%s" stop-opacity="0.30"/><stop offset="100%%" stop-color="%s" stop-opacity="0.06"/>'
            '<animateTransform attributeName="gradientTransform" type="translate" values="-1 0;1 0;-1 0" dur="6s" repeatCount="indefinite"/></linearGradient></defs>'
            '<rect x="1" y="1" width="%d" height="36" rx="18" fill="%s" stroke="%s" stroke-opacity="0.5" stroke-width="1.2"/><rect x="1" y="1" width="%d" height="36" rx="18" fill="url(#g)"/>'
            '<circle cx="20" cy="19" r="4" fill="%s"><animate attributeName="opacity" values="1;0.25;1" dur="2.4s" repeatCount="indefinite"/></circle>'
            '<text x="%d" y="24" text-anchor="middle" font-family="%s" font-size="11.5" fill="%s" letter-spacing="1.4">%s</text></svg>'
            % (w, w, label, P["gold"], P["gold"], w - 2, P["surface"], P["gold"], w - 2, P["gold"], w // 2 + 8, SANS, P["fg"], label))


def ticker():
    items = [("PYTHON 3.12", P["gold"]), ("FLASK", P["chrome"]), ("TELEGRAM BOT API", P["fg"]), ("BINANCE", P["gold"]),
             ("YAHOO FINANCE", P["chrome"]), ("SQLITE", P["gold2"]), ("FLY.IO", P["fg"]), ("GITHUB ACTIONS", P["win"])]
    run, x = [], 0
    for label, col in items:
        run.append('<text x="%d" y="38" fill="%s">%s</text>' % (x, col, label))
        x += int(len(label) * 10.6) + 28
        run.append('<text x="%d" y="38" fill="%s">/</text>' % (x, P["border"]))
        x += 26
    width = x
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 64" width="1280" height="64" role="img" aria-label="Stack: Python, Flask, Telegram Bot API, Binance, Yahoo Finance, SQLite, Fly.io, GitHub Actions">'
            '<defs><linearGradient id="fade" x1="0" y1="0" x2="1" y2="0"><stop offset="0%%" stop-color="%s" stop-opacity="1"/><stop offset="8%%" stop-color="%s" stop-opacity="0"/>'
            '<stop offset="92%%" stop-color="%s" stop-opacity="0"/><stop offset="100%%" stop-color="%s" stop-opacity="1"/></linearGradient>'
            '<g id="run" font-family="%s" font-size="15" letter-spacing="2">%s</g></defs>'
            '<rect width="1280" height="64" fill="%s"/><rect y="0" width="1280" height="1" fill="%s"/><rect y="63" width="1280" height="1" fill="%s"/>'
            '<g><animateTransform attributeName="transform" type="translate" from="0 0" to="-%d 0" dur="26s" repeatCount="indefinite"/>'
            '<use href="#run" x="0"/><use href="#run" x="%d"/><use href="#run" x="%d"/></g><rect width="1280" height="64" fill="url(#fade)"/></svg>'
            % (P["bg"], P["bg"], P["bg"], P["bg"], SANS, "".join(run), P["bg"], P["border"], P["border"], width, width, width * 2))


def divider():
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 24" width="1280" height="24" role="img" aria-label="divider">'
            '<defs><linearGradient id="d" x1="0" y1="0" x2="1" y2="0"><stop offset="0%%" stop-color="%s" stop-opacity="0"/><stop offset="35%%" stop-color="%s" stop-opacity="0.9"/>'
            '<stop offset="50%%" stop-color="%s" stop-opacity="1"/><stop offset="65%%" stop-color="%s" stop-opacity="0.9"/><stop offset="100%%" stop-color="%s" stop-opacity="0"/>'
            '<animateTransform attributeName="gradientTransform" type="translate" values="-1 0;1 0;-1 0" dur="8s" repeatCount="indefinite"/></linearGradient></defs>'
            '<rect y="11" width="1280" height="2" fill="%s" opacity="0.6"/><rect y="10" width="1280" height="4" fill="url(#d)"/>'
            '<circle cy="12" r="4" fill="%s"><animate attributeName="cx" values="0;1280;0" dur="8s" repeatCount="indefinite"/><animate attributeName="opacity" values="0;1;1;0" dur="8s" repeatCount="indefinite"/></circle></svg>'
            % (P["gold"], P["gold"], P["gold2"], P["chrome"], P["chrome"], P["border"], P["gold2"]))


def metrics(light=False):
    c = LIGHT if light else P
    data = [("Gold IB", 5, P["gold"]), ("Gold mkt", 3, P["gold2"]), ("Prop firm", 3, P["chrome"]), ("Forex", 2, "#8f99a8"),
            ("Crypto", 2, "#a87d0f"), ("Stocks", 1, P["win"]), ("Fintech", 2, P["loss"])]
    bars = []
    for i, (label, n, col) in enumerate(data):
        x, h = 130 + i * 122, n * 26
        top = 300 - h
        bars.append('<g><animateTransform attributeName="transform" type="translate" values="0 6;0 0" dur="1.1s" begin="%.2fs" fill="freeze" calcMode="spline" keySplines="0.2 0 0.2 1" keyTimes="0;1"/>'
                    '<polygon points="%d,%d %d,%d %d,%d %d,%d" fill="%s" fill-opacity="0.95"/><polygon points="%d,%d %d,%d %d,287 %d,300" fill="%s" fill-opacity="0.45"/>'
                    '<rect x="%d" y="%d" width="62" height="%d" fill="%s" fill-opacity="0.70"/>'
                    '<text x="%d" y="%d" text-anchor="middle" font-family="%s" font-size="19" font-weight="bold" fill="%s">%d</text>'
                    '<text x="%d" y="322" text-anchor="middle" font-family="%s" font-size="12" fill="%s">%s</text></g>'
                    % (i * .12, x, top, x + 62, top, x + 84, top - 13, x + 22, top - 13, col, x + 62, top, x + 84, top - 13, x + 84, x + 62, col,
                       x, top, h, col, x + 39, top - 22, SANS, col, n, x + 31, SANS, c["muted"], label))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1020 360" width="1020" height="360" role="img" aria-label="18 products by vertical: Gold IB 5, Gold market 3, Prop firm 3, Forex 2, Crypto 2, Stocks 1, Fintech 2">'
            '<rect width="1020" height="360" fill="%s"/><g stroke="%s" stroke-width="1"><path d="M110 300h880"/><path d="M110 300l22-13h880" opacity="0.6"/>'
            '<path d="M110 248h880" opacity="0.35"/><path d="M110 196h880" opacity="0.35"/><path d="M110 144h880" opacity="0.35"/></g>'
            '<text x="40" y="46" font-family="%s" font-size="17" font-weight="bold" fill="%s">18 PRODUCTS BY VERTICAL</text>'
            '<text x="40" y="68" font-family="%s" font-size="12" fill="%s">gold-weighted by design · every product has a free tier</text>%s</svg>'
            % (c["bg"], c["border"], SANS, c["fg"], SANS, c["muted"], "".join(bars)))


def roadmap():
    stops = [("NOW", "Vault I · 3 of 9 live", P["win"]), ("NEXT", "IB ops suite ·10-13", P["gold"]),
             ("THEN", "Prop + forex ·14-16", P["gold2"]), ("LATER", "Crypto + stocks ·17-18", P["chrome"])]
    out = []
    for i, (k, v, col) in enumerate(stops):
        a = i * 90
        out.append('<g transform="rotate(%d 300 300)"><circle cx="300" cy="118" r="13" fill="%s" fill-opacity="0.25" stroke="%s" stroke-width="2">'
                   '<animate attributeName="r" values="13;17;13" dur="3s" begin="%.1fs" repeatCount="indefinite"/></circle><circle cx="300" cy="118" r="5" fill="%s"/></g>'
                   '<g transform="rotate(%d 300 300)"><g transform="rotate(%d 300 118)"><text x="300" y="86" text-anchor="middle" font-family="%s" font-size="13" font-weight="bold" fill="%s" letter-spacing="2">%s</text>'
                   '<text x="300" y="150" text-anchor="middle" font-family="%s" font-size="11.5" fill="%s">%s</text></g></g>'
                   % (a, col, col, i * .5, col, a, -a, SANS, col, k, SANS, P["muted"], v))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="440" height="440" role="img" aria-label="Roadmap: now Vault I with 3 of 9 live, next IB ops suite, then prop and forex, later crypto and stocks">'
            '<defs><radialGradient id="c" cx="50%%" cy="50%%" r="50%%"><stop offset="0%%" stop-color="%s" stop-opacity="0.30"/><stop offset="100%%" stop-color="%s" stop-opacity="0"/></radialGradient>%s</defs>'
            '<circle cx="300" cy="300" r="182" fill="none" stroke="%s" stroke-width="1.5" stroke-dasharray="4 9"/>'
            '<circle cx="300" cy="300" r="182" fill="none" stroke="%s" stroke-opacity="0.5" stroke-width="2" stroke-dasharray="60 1085"><animateTransform attributeName="transform" type="rotate" from="0 300 300" to="360 300 300" dur="14s" repeatCount="indefinite"/></circle>'
            '<circle cx="300" cy="300" r="96" fill="url(#c)"/><circle cx="300" cy="300" r="74" fill="%s" stroke="%s" stroke-opacity="0.5" stroke-width="2"/>'
            '<text x="300" y="298" text-anchor="middle" class="disp" font-size="34" fill="%s">18</text>'
            '<text x="300" y="318" text-anchor="middle" font-family="%s" font-size="11" fill="%s" letter-spacing="2">PRODUCTS</text>%s</svg>'
            % (P["gold"], P["gold"], font_style(), P["border"], P["gold"], P["surface"], P["gold"], P["gold2"], SANS, P["muted"], "".join(out)))


def spinner():
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%%" height="100%%" role="img" aria-label="SBG">'
            '<defs>%s%s</defs>'
            '<circle cx="100" cy="100" r="85" fill="none" stroke="%s" stroke-width="2" opacity="0.25"><animateTransform attributeName="transform" type="rotate" from="0 100 100" to="360 100 100" dur="20s" repeatCount="indefinite"/></circle>'
            '<circle cx="100" cy="100" r="60" fill="none" stroke="%s" stroke-width="1.5" opacity="0.4" stroke-dasharray="30 6 8 6 40 6"><animateTransform attributeName="transform" type="rotate" from="360 100 100" to="0 100 100" dur="15s" repeatCount="indefinite"/></circle>'
            '<circle cx="100" cy="100" r="35" fill="none" stroke="%s" stroke-width="3" opacity="0.7" stroke-dasharray="8 6"><animateTransform attributeName="transform" type="rotate" from="0 100 100" to="-360 100 100" dur="25s" repeatCount="indefinite"/></circle>'
            '<text x="100" y="110" text-anchor="middle" class="disp" font-size="30"><tspan fill="url(#cw)">SB</tspan><tspan fill="url(#gd)">G</tspan></text></svg>'
            % (font_style(), chrome_grad("cw") + gold_grad("gd"), P["chrome"], P["gold"], P["gold2"]))


# --------------------------------------------------------------------------- #
# Icons: keep the glyph, recolour by vertical
# --------------------------------------------------------------------------- #

def recolour_icon(path, product):
    accent = VERTICAL_ACCENT.get(product.vertical, P["gold"])
    glyph_col = P["gold2"] if accent in (P["gold"], P["gold2"], "#a87d0f") else P["fg"]
    s = path.read_text()
    for old in OLD_ACCENTS:
        s = s.replace(old, accent)
    s = s.replace("#ffd873", glyph_col).replace("#16203a", P["surface2"]).replace("#0a1120", P["surface"])
    path.write_text(s)


def main():
    (ASSETS / "hero-banner-dark.svg").write_text(hero(False))
    (ASSETS / "hero-banner-light.svg").write_text(hero(True))
    (ASSETS / "badges-strip.svg").write_text(badges())
    for name, label in (("vault", "THE VAULT · 9 SHIPPED"), ("vault2", "VAULT II · 9 PROPOSED"), ("platforms", "PLATFORMS"),
                        ("roadmap", "ROADMAP"), ("quickstart", "QUICKSTART")):
        (ASSETS / "nav" / ("%s.svg" % name)).write_text(nav_chip(label))
    (ASSETS / "stack-ticker.svg").write_text(ticker())
    (ASSETS / "divider-flow.svg").write_text(divider())
    (ASSETS / "metrics-3d-dark.svg").write_text(metrics(False))
    (ASSETS / "metrics-3d-light.svg").write_text(metrics(True))
    (ASSETS / "roadmap-orbit.svg").write_text(roadmap())
    (ASSETS / "hero-animated.svg").write_text(spinner())
    for p in PRODUCTS:
        recolour_icon(ASSETS / "icons" / ("ic-%02d.svg" % p.number), p)
    print("assets regenerated in the SAMBANGGOLD palette")


if __name__ == "__main__":
    main()
