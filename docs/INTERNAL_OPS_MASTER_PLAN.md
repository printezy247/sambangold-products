# Internal Ops: Telegram bot + dashboard for Sam's CEO & team

A second, internal-only surface on top of this repo — separate from the
customer-facing `@samproducts_bot` and 18-tool suite — for Sam's CEO, HODs
and Executives to run the business: tasks, a weekly/monthly calendar, a
docs/pics/vids library, an AI-assisted file finder, and one combined
product roadmap across both of Sam's repos (`sambangold-products` here,
and `website_sam`).

## Decisions already made

| Question | Decision |
|---|---|
| Where does this live? | Inside `sambangold-products` (this repo), not a new repo and not `website_sam`. |
| Hosting | Railway, not Fly.io — Fly's free-tier machines kept auto-suspending. Migrated in Phase 0; connected and green as of Phase 2. |
| Team bot | A **second, dedicated Telegram bot** — its own token, separate from `@samproducts_bot` — so internal traffic never mixes with customer traffic. |
| Dashboard auth | Reuse the existing passwordless doors (Telegram Login Widget + 8-digit email code) plus a `team_role` grant on top, **not** a new password system — this repo has no password field anywhere by design ("three doors, no passwords" in `auth.py`). |
| Product roadmap scope | **Both** product lines combined: this repo's 18 SaaS tools + `website_sam`'s digital-product catalog, in one Apple-style status grid. |
| `sambangold-products` status conflict | Fixed in Phase 0. |
| File storage | Free-tier docs + brand assets committed to this **public** repo; anything sold as a paid ebook elsewhere goes on the Railway volume instead, never git — see Phase 2's hard lesson below. |
| Reminders | Telegram only for now — no email. |
| Roles | `ceo`, `hod_sales`, `hod_marketing` = full access. `executive` = browse/download only, no create/edit anywhere. |
| File finder | Local keyword search always on; an optional AI layer (NARA, OpenAI-compatible) explains/ranks the same local results once `NARA_API_KEY`/`NARA_BASE_URL`/`NARA_MODEL` are set. |

## Phase 0 — Cleanup + hosting migration (done)

- Fixed 7 product specs whose status badge said `PROPOSED` while
  `app/products.py` and the doc's own body text already said shipped/live.
- Migrated deploy target from Fly.io to Railway (`railway.json`, `$PORT`-
  aware Dockerfile, dropped `fly.toml` and the CI Fly deploy job).

## Phase 1 — Data foundation, roles, roadmap, tasks (done)

- `store.py`: `team_roles`, `tasks`, `roadmap_items`, `notify_prefs` tables.
- `teamauth.py`: `team_required` / `team_admin_required` / `ceo_required`.
- `roadmap.py`: seeds the combined roadmap. Re-seeding never overwrites a
  status a human already set.
- `/team/roadmap`, `/team/tasks`, `/team/people` (CEO-only role grants).
- `flask team-seed`: seeds the roadmap + file library, grants the first
  CEO role to `ADMIN_TELEGRAM_ID` if no team roles exist yet.

## Phase 2 — Calendar, file library, and a lesson about public repos (done)

- `teamcalendar.py` + `/team/calendar?view=week|month&offset=N`.
- `file_items` table + `/team/files` browse page.
- **What went wrong and got caught before it shipped:** the first pass
  copied Sam's entire local `docs/` folder into the repo, including 5
  titles that are actually sold as paid ebooks on website_sam ($19–$49).
  This repo is **public** — committing them would have let anyone
  download Sam's paid products for free straight from GitHub, regardless
  of the `team_required` gate on the Flask route (that gate only protects
  requests through the deployed app; GitHub serves a public repo's file
  history to anyone, gate or not). Caught by a safety check before the
  push went out; fixed by squash-merging so the bad commit never reached
  `origin`, keeping only the free-tier lead magnets + brand assets in git.
  **Takeaway for every future phase:** before committing any file to this
  repo, check whether it's sold anywhere else first.
- The 5 paid titles instead go through `PAID_LIBRARY_PATH` (Phase 3): a
  Railway volume path, uploaded manually, never git, served through the
  same `team_required` gate.

## Phase 3 — Dedicated internal bot + AI-assisted file search (done)

- `teambot.py`: a second bot, own token (`TEAM_BOT_TOKEN`), own webhook
  (`/webhook/teambot`). Every command checks `store.team_role()` first —
  same table the dashboard reads, so there's exactly one place access is
  granted (`/team/people`, or `/promote` in the bot itself).
  - `/start`, `/whoami`, `/tasks` (mark-done buttons for CEO/HODs),
    `/calendar` (today + this week, link to the full dashboard view),
    `/files` (category picker → list; repo/volume files are sent as real
    Telegram documents via `sendDocument`, Drive links open externally),
    `/people` + `/promote ID role` (CEO-only), `/broadcast` (CEO/HODs,
    posts to `TEAM_GROUP_CHAT_ID`).
- `navchat.py` + `/team/chat`: "ask and locate files" on the dashboard.
  Local keyword search over file titles/tags/categories always works, no
  key needed. When `NARA_API_KEY` + `NARA_BASE_URL` + `NARA_MODEL` are all
  set, the same local matches are handed to an OpenAI-compatible
  chat-completions endpoint for a short explanatory answer on top — the AI
  never invents files outside what local search already found, and any
  network/API failure just means no AI answer that request (search still
  works).
- `config.py`: `PAID_LIBRARY_PATH` (default `/data/library`), `TEAM_BOT_TOKEN`,
  `TEAM_BOT_USERNAME`, `TEAM_GROUP_CHAT_ID`, `NARA_API_KEY`, `NARA_BASE_URL`,
  `NARA_MODEL` — all optional, all default to "off" behavior when unset.

### What's needed from Sam for Phase 3 to go fully live

1. **Create the team bot** via @BotFather (needs your Telegram account —
   can't be automated). Suggest something like `@sambanggold_team_bot`.
   Don't publish its username anywhere public; share it directly with
   CEO/HODs/Executives only.
2. Set `TEAM_BOT_TOKEN` and `TEAM_BOT_USERNAME` as Railway service
   variables, then run `flask --app wsgi team-set-webhook` once.
3. Run `flask --app wsgi team-seed` (if not already) to seed roles/roadmap/
   file library, and grant CEO/HOD/Executive roles to real people via
   `/team/people` on the dashboard or `/promote` in the bot once you (as
   the bootstrap CEO) can reach it.
4. Optional: set `TEAM_GROUP_CHAT_ID` if you want `/broadcast` and the
   Phase 4 daily digest to post into Sam's team group.
5. Optional, when ready: upload the 5 paid-tier PDFs to the Railway
   volume at `PAID_LIBRARY_PATH` (`/data/library/docs/...`), then re-run
   `flask team-seed` — they'll appear in `/team/files` and the bot's
   `/files`, gated the same as everything else, never touching git.
6. Optional: set `NARA_API_KEY` / `NARA_BASE_URL` / `NARA_MODEL` (you
   mentioned providing the key later) to turn on the AI layer on
   `/team/chat`. Local search already works without it.

## Phase 4 — Reminders (Telegram only, not yet built)

- `flask team-digest` CLI command: due-today + overdue tasks, posted to
  each team member's DM and/or `TEAM_GROUP_CHAT_ID`, respecting
  `notify_prefs` (schema already in place since Phase 1).
- Triggered the same way `check-alerts` already is — a scheduled,
  `TASK_TOKEN`-authenticated POST from GitHub Actions `schedule:` cron.
- Inline buttons per reminder: "Open in dashboard", plus a toggle for
  `notify_prefs`.

## Phase 5 — Polish (not yet built)

- Dashboard settings page for `notify_prefs`.
- CSV/PDF export for tasks and roadmap.
- Expand ms/en strings as real usage surfaces gaps.

## Why this shape

Every phase is additive: new tables, new blueprint, new bot — nothing in
the customer-facing 18-tool suite changes behavior, so the original 568
tests keep passing untouched through every phase above (638 total now).
Each phase lands as its own commit(s) on `master`; Railway redeploys
automatically on every push that passes CI.
