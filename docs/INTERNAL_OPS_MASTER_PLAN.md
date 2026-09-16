# Internal Ops: Telegram bot + dashboard for Sam's CEO & team

A second, internal-only surface on top of this repo — separate from the
customer-facing `@samproducts_bot` and 18-tool suite — for Sam's CEO, HODs
and Executives to run the business: tasks, a weekly/monthly calendar, a
docs/pics/vids library, and one combined product roadmap across both of
Sam's repos (`sambangold-products` here, and `website_sam`).

## Decisions already made

| Question | Decision |
|---|---|
| Where does this live? | Inside `sambangold-products` (this repo), not a new repo and not `website_sam`. |
| Hosting | Railway, not Fly.io — Fly's free-tier machines kept auto-suspending. Migrated in Phase 0. |
| Team bot | A **second, dedicated Telegram bot** — its own token, separate from `@samproducts_bot` — so internal traffic never mixes with customer traffic. |
| Dashboard auth | Reuse the existing passwordless doors (Telegram Login Widget + 8-digit email code) plus a `team_role` grant on top, **not** a new password system — this repo has no password field anywhere by design ("three doors, no passwords" in `auth.py`). A role is granted to an existing account, the same way a customer rank is granted. |
| Product roadmap scope | **Both** product lines combined: this repo's 18 SaaS tools + `website_sam`'s digital-product catalog (indicators, ebooks, copier, signals), in one Apple-style status grid. |
| `sambangold-products` status conflict | Fixed in Phase 0 — see below. |
| File storage | Existing repo assets (`assets/brand/`) + the local `D:\SamBangGold` folder's docs/pics/vids + a shared Google Drive folder, surfaced as links (no file re-hosting). |
| Reminders | Telegram only for now — no email. |
| Roles | `ceo`, `hod_sales`, `hod_marketing` = full access. `executive` = browse/download only, no create/edit anywhere. |

## Phase 0 — Cleanup + hosting migration (done, this session)

- Fixed 7 product specs (`products/product-10.md`..`16.md`) whose status
  badge said `PROPOSED` while `app/products.py` (the real source of truth)
  and the doc's own body text already described them as live/shipped.
- Migrated deploy target from Fly.io to Railway: `Dockerfile` now reads
  Railway's injected `$PORT`, added `railway.json` (build + `/healthz`
  healthcheck + restart policy), removed `fly.toml` and the CI Fly deploy
  job, updated `CLAUDE.md`/README/brand assets accordingly.

**Manual step still needed (Railway has no API token in this environment,
so this can't be automated further):** connect this GitHub repo to a
Railway project — Dashboard → New Project → Deploy from GitHub repo →
`printezy247/sambangold-products`, branch `master`. Then, one-time:
1. Add a **Volume** mounted at `/data` (Settings → Volumes) so SQLite
   survives restarts — mirrors the old Fly volume.
2. Set service variables: `TELEGRAM_BOT_TOKEN`, `FLASK_SECRET_KEY`,
   `PUBLIC_BASE_URL` (the Railway domain), `ADMIN_TELEGRAM_ID`,
   `TASK_TOKEN`, `DATABASE_PATH=/data/sambangold.db`, plus SMTP/Stripe vars
   if those features are wanted live.
3. Run `flask --app wsgi set-webhook` once (Railway's shell, or locally
   with the same env vars) so Telegram routes updates to the new URL.

After that, every push to `master` that passes CI redeploys automatically —
which is what makes "auto git ops to main → Railway auto-deploys per phase"
work for every phase below.

## Phase 1 — Data foundation, roles, roadmap, tasks (done, this session)

- `store.py`: `team_roles`, `tasks`, `roadmap_items`, `notify_prefs` tables.
- `teamauth.py`: `team_required` / `team_admin_required` / `ceo_required`
  decorators. Executives get read-only everywhere.
- `roadmap.py`: seeds the combined roadmap (18 tools here, all `launched`,
  + 8 rows for `website_sam`'s catalog). Re-seeding never overwrites a
  status a human already set.
- `teamviews.py` + `templates/team/`: `/team/roadmap`, `/team/tasks`,
  `/team/people` (CEO-only role grants) — working dashboard pages, gated,
  tested (25 new tests, 593 total passing).
- `flask team-seed`: run once after deploy. Seeds the roadmap and grants
  the first CEO role to `ADMIN_TELEGRAM_ID` if no team roles exist yet.

**What a CEO/HOD/Executive can do right now, once deployed:** sign in the
normal way (Telegram or email), and if they hold a team role, a **Team**
link appears in the nav → roadmap grid with live/developing status across
both product lines, and a task list they can add to and advance (CEO/HODs)
or just read (Executives).

## Phase 2 — Calendar view + file/doc library

- `tasks` already has `due_at`; add a `/team/calendar` view with a
  week/month toggle (URL param `?view=week|month`, default week), grouping
  existing tasks by due date — no new schema needed.
- `file_items` table (`category`: doc/pic/vid, `source`: drive/repo_asset,
  `url`, `tags`) + `/team/files` browse page, filterable by category.
  Seed rows from: `assets/brand/` (this repo), the local `D:\SamBangGold`
  folder's `docs/`, `pics/`, `vids/` (needs those to be hosted somewhere
  linkable — see open question below), and the shared Google Drive folder.
- **Open question for Sam:** the Drive folder link provided
  (`drive.google.com/drive/folders/1KlzuoDsm...`) isn't readable by this
  session's Drive connector yet (`Incompatible auth server` on first try).
  Either share it with a service account this app can authenticate as, or
  keep files there and just store deep-links (simplest — no API needed,
  works today) and skip live folder-sync for now.

## Phase 3 — Dedicated internal Telegram bot

- New bot via @BotFather (**you create this** — bot creation needs your
  Telegram account, it can't be automated): e.g. `@sambanggold_team_bot`.
  Env vars `TEAM_BOT_TOKEN`, `TEAM_BOT_USERNAME`, webhook at
  `/webhook/teambot`.
- `teambot.py`, mirroring `telegram.py`'s structure: `/start` → role check
  → menu (max 3 buttons per screen, per this repo's UX rule): 📋 Tasks /
  📅 Calendar / 📁 Files. Admin-only: `/promote`, `/people`, `/broadcast`.
- Same `store.py` functions the dashboard already uses — no duplicate logic.

## Phase 4 — Reminders (Telegram only)

- `flask team-digest` CLI command: due-today + overdue tasks, posted to
  each team member's DM and/or the shared group, respecting
  `notify_prefs` (already in the Phase 1 schema).
- Triggered the same way `check-alerts` already is — a scheduled hit
  (`TASK_TOKEN`-authenticated POST) from GitHub Actions `schedule:` cron
  or Railway's own cron, since there's no external scheduler wired up yet.
- Inline buttons on each reminder: "Open in dashboard" deep link, and a
  toggle for `notify_prefs` per user.

## Phase 5 — Polish

- Dashboard settings page for `notify_prefs`.
- CSV/PDF export for tasks and roadmap (mirrors existing patterns in
  `rebatetool.py` / `mctool.py`).
- i18n pass: team ops strings currently exist in both `ms`/`en` in
  `brand.py`, but only the essentials — expand as real usage surfaces gaps.

## Why this shape

Every phase is additive: new tables, new blueprint, new bot — nothing in
the customer-facing 18-tool suite changes behavior, so the existing 568
tests keep passing untouched (verified — they do, at every step above).
Each phase lands as its own commit(s) on `master`, so Railway redeploys
incrementally rather than in one large, harder-to-verify jump.
