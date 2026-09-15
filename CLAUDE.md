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

A change is "successful" when `scripts/check-readme.sh` passes **and** `pytest`
passes — not merely when the files were written. Both run in CI.

## 3. Theme: SAMBANGGOLD — futuristic, premium, one brand across every surface

The dashboard, the bot and the README carry **Sam's brand**, taken from the
website repo (`printezy247/website_sam`: `src/config/brand.ts`,
`src/app/globals.css`, `public/brand/`). `app/brand.py` is the single source of
truth for the name, the tokens and every user-facing string.

| Token | Value | Use |
|:--|:--|:--|
| Background | `#050505` | Page ground (near-black) |
| Surface / Surface 2 | `#0b0e14` / `#11151d` | Cards, panels, risk strip |
| Border | `#1e2330` | Hairlines |
| Gold / Gold 2 / Gold deep | `#d4af37` / `#f5d76e` / `#7a4003` | Primary accent, gradients, CTAs |
| Chrome | `#b7c0ce` | The "SAMBANG" half of the wordmark, secondary gradients |
| Win / Loss | `#00c46a` / `#ff4d4f` | Success and free tier / risk and errors |
| Text / Muted | `#f3f4f6` / `#9aa3b2` | Body and secondary text |

Type: **Anton** (OFL, self-hosted at `assets/brand/anton.woff2`) for the italic
wordmark — chrome `SAMBANG` + gold `GOLD` — and display headings; a system sans
stack for body; monospace for numbers. Brand kit in `assets/brand/`: wordmark,
SBG monogram glyph (rotating gold ring), and the hammering-robot mascot (two PNG
frames alternated by CSS).

Effects, all CSS: `.glass`, `.lux` cards whose gold spotlight follows the pointer,
`.lux-gold` with a slow conic beam, `.btn-gold`, `.holo-btn`, `.grid-bg`, a canvas
field of drifting candles behind the hero. Dark-first; `prefers-reduced-motion`
turns every loop off.

Tone: **Bahasa Melayu first, English second.** Short sentences, no hype, the
rank vocabulary from the site (Awam → General → A-Team → Rambo), and the risk
strip on every surface. Product, rank and brand names are never translated.

> The README's 32 SVG assets still carry the earlier navy/cyan palette. They are
> the next thing to regenerate; do not add new assets in the old palette.

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
4. **Every product spec** in `products/product-01..18.md` carries its required
   headings, including `## Dashboard views` alongside `## Commands` — that pair
   is what enforces the two-surface rule in the docs.

Do not hand-roll these checks inline; extend the script instead, so the local
run and the CI run never drift apart.

## Repo layout

```
app/             the Flask app — brand.py (tokens + BM/EN strings), products.py registry, calc.py, tools.py, watch.py, feeds.py, store.py (SQLite: alerts, users, codes), auth.py (Telegram / email code / Google placeholder), mailer.py (SMTP), telegram.py (button-driven bot), views.py, templates/
tests/           surface contract (both halves, all 18), sign-in doors + linking, bot funnel, Gold Watch
assets/          self-hosted animated SVGs (hero, dividers, icons, nav chips, charts)
products/        product-01..18.md — one spec per product
scripts/         check-readme.sh, auto-commit.sh, auto-deploy.sh
wsgi.py          gunicorn entry point
Dockerfile       Fly.io build; fly.toml — app name, port 8080, /data volume for SQLite
.github/         CI/CD workflow
```

## Product conventions

**Every product ships both surfaces** — a 🤖 Telegram half and a 🌐 dashboard
half — on one Telegram account, with the same free tier on each. Shape decides
only which half is **primary** (where the value lands), never whether a half
exists.

`app/products.py` is the registry and the single source of truth. Routes, the
bot command dispatch table, the dashboard index and the tests all read from it,
so a product cannot exist on one surface only without a test failing. Add a
product there first, then write its spec.

No product is paywalled at the door — paid tiers sell scale and automation only,
never basic access.

## Disclaimer

Every user-facing surface carries: **educational research only, not financial
advice, verify every price with your broker.**
