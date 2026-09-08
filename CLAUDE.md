# Project defaults — sambangold-products

Standing instructions for this repository. They apply to every session and every
phase of work unless the request explicitly overrides one.

## 1. Free services only

No paid APIs, no paid hosting tiers, no paid fonts, no paid asset libraries, no
services that require a card to start.

Approved by default: GitHub (repos, Actions, Pages), Fly.io free allowance,
Binance and Yahoo Finance public market endpoints, Telegram Bot API, Stripe
(free to integrate; only end users pay), self-hosted SVG assets, system font
stacks.

Before adding any dependency or service, confirm it has a genuinely free tier
that covers the intended use. If the only viable option costs money, stop and
say so rather than adding it quietly.

## 2. Auto git ops on every successful build

When a change builds and its checks pass, commit and push without waiting to be
asked. Do not leave verified work sitting uncommitted in the working tree.

- Commit with a descriptive conventional-commit message (`feat:`, `fix:`,
  `docs:`, `chore:`).
- Push to the working branch, then open a pull request if none is open.
- `scripts/auto-commit.sh` and `scripts/auto-deploy.sh` exist for this.
- Never commit `.env` or any real key. `.env.example` carries the key names only.

A build is "successful" when the repo's own checks pass — not merely when the
files were written.

## 3. Theme: modern, futuristic, premium

Every visual surface — README, web pages, generated SVG, bot cards, PDFs —
shares one identity.

| Token | Value | Use |
|:--|:--|:--|
| Background | `#060b14` → `#0d1b30` | Deep navy base, gradient ground |
| Surface | `#0b1424` | Cards and panels |
| Gold | `#f0b429` | Primary accent — gold products, IB, headlines |
| Cyan | `#00e5ff` | Secondary accent — prop firm, forex |
| Rose | `#ff4d6d` | Alerts, risk, security |
| Violet | `#a78bfa` | Crypto |
| Green | `#34d399` | Stocks, success, free tier |
| Text | `#e8f0ff` / muted `#8fa3c0` | Body and secondary text |

Principles: dark-first with a light variant wherever the host supports one;
generous spacing over dense layout; depth through isometric geometry, extruded
faces, and soft shadow rather than skeuomorphic texture; motion that is subtle
and looping, never distracting; every asset self-hosted.

## 4. README is a product surface

Treat `README.md` as a designed page, not a text file. It carries emojis,
deliberate spacing, and GitHub's interactive elements.

**GitHub honors:** animated SVG via `<img>` (SMIL), `<picture>` with
`prefers-color-scheme` for dark/light, `<details>`/`<summary>` accordions,
mermaid diagrams in fenced blocks, alert callouts (`> [!NOTE]`,
`> [!IMPORTANT]`), tables, task lists, `<div align="center">`, and
`<a href><img></a>` clickable image chips.

**GitHub strips — never use in a `.md` file:** `<style>`, `<script>`, `class=`,
inline `style=`, `<html>`/`<head>`/`<body>`, CSS `:hover`, `<iframe>`.

All motion and depth must live *inside* the SVG files, because that is the only
place it survives. The README was once written as a raw HTML document; GitHub
rendered it as a wall of unstyled CSS text. Do not repeat that.

Reference assets by relative path (`assets/...`), never absolute URLs.

## 5. Check trending repositories before each phase

Before starting a new phase — a new product, a redesign, a new integration —
look at what comparable well-regarded repositories are doing right now, and
carry over what genuinely works.

Look for: current README and documentation conventions, asset and animation
techniques that render correctly on GitHub today, project layout, and CI
patterns. Adopt what fits this project's constraints; do not copy wholesale, and
never adopt something that breaks rules 1 through 4.

Say briefly what was checked and what was taken from it.

---

## Verification before any README change

```bash
# 1. no constructs GitHub strips
grep -nE '<style|<script|class=|style=|<!DOCTYPE|<iframe' README.md   # must be empty

# 2. every referenced asset exists
for p in $(grep -oE '(src|srcset)="[^"]+"' README.md | sed -E 's/.*="([^"]+)"/\1/' | sort -u); do
  case "$p" in http*) continue;; esac; [ -f "$p" ] || echo "MISSING: $p"
done

# 3. all SVGs are well-formed
python3 -c "import xml.dom.minidom,glob;[xml.dom.minidom.parse(f) for f in glob.glob('assets/**/*.svg',recursive=True)]"
```

## Repo layout

```
assets/          self-hosted animated SVGs (hero, dividers, icons, nav chips, charts)
products/        product-01..18.md — one spec per product
scripts/         auto-commit.sh, auto-deploy.sh
.github/         CI/CD workflow
```

## Product conventions

Every product states its **platform** (🤖 Telegram / 🌐 Web / 🤖🌐 Both) and its
**free tier**. No product is paywalled at the door — paid tiers sell scale and
automation only, never basic access.

## Disclaimer

Every user-facing surface carries: **educational research only, not financial
advice, verify every price with your broker.**
