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

When a change passes its checks, commit and push without waiting to be asked.
Do not leave verified work sitting uncommitted in the working tree.

- Run `scripts/check-readme.sh` first. It is the gate, and CI runs the same
  script — if it fails, fix the change rather than pushing it.
- Commit with a descriptive conventional-commit message (`feat:`, `fix:`,
  `docs:`, `chore:`).
- `scripts/auto-commit.sh "<message>"` runs the check, commits, and pushes the
  current branch with retries. It refuses to run on `master` or `main`.
- Opening the pull request is a separate step — the script does not do it.
  Open one from the session or the GitHub UI after the push, if none is open.
- `scripts/auto-deploy.sh` runs the checks and deploys; it skips deploy cleanly
  when `fly.toml` or the CLI is absent.
- Never commit `.env` or any real key. `.env.example` carries the key names only.

A change is "successful" when `scripts/check-readme.sh` passes, plus any tests
that exist — not merely when the files were written. Application code, tests,
and `requirements.txt` do not exist yet; the CI jobs skip those steps until
they do, so a green run today means the docs and assets are sound, nothing
more.

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

Run the checked-in script — it is the same one CI runs:

```bash
bash scripts/check-readme.sh
```

It verifies four things and exits non-zero on any failure:

1. **No stripped HTML** — `<style>`, `<script>`, `class=`, `style=`, `<!DOCTYPE>`,
   `<iframe>` anywhere in `README.md`.
2. **Every referenced file resolves** — HTML `src=` and `srcset=` (including each
   candidate of a multi-candidate `srcset`), plus markdown `![img](path)` and
   `[link](path)` targets. External URLs and anchors are skipped.
3. **Every SVG under `assets/` parses** as well-formed XML.
4. **Every product spec** in `products/product-1*.md` carries its required
   headings.

Do not hand-roll these checks inline; extend the script instead, so the local
run and the CI run never drift apart.

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
