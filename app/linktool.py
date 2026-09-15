"""#13 Link Attribution — the bot commands, the redirect, the dashboard context."""

from flask import current_app

from . import links, store
from .brand import DEFAULT_LANG, t

SLUG = "link-attribution"


def short_url(code):
    return "%s/l/%s" % (current_app.config["PUBLIC_BASE_URL"].rstrip("/"), code)


def _default_url(owner):
    return store.get_setting("broker-comparator", owner, "reflink") if owner else ""


def create_link(owner, channel, url):
    """(link_row, error_key) — enforces the free-tier cap and one link per channel."""
    channel = (channel or "").strip().lstrip("#@")
    if not channel:
        return None, "ui.k_bad"
    existing = store.link_by_channel(owner, channel)
    if existing:
        return existing, "lk.exists"
    if len(store.links_for(owner)) >= links.FREE_LINKS:
        return None, "lk.limit"
    url = (url or "").strip() or _default_url(owner)
    if not url.lower().startswith(("http://", "https://")):
        return None, "lk.no_url"
    code = links.new_code()
    while store.link_by_code(code):
        code = links.new_code()
    link_id = store.add_link(owner, code, channel, url)
    return dict(store.link_by_code(code), id=link_id), None


# --- bot -------------------------------------------------------------------- #

def bot_newlink(args, chat_id=None, lang=DEFAULT_LANG, **_):
    if not args or not chat_id:
        return t("lk.usage", lang)
    link, err = create_link(chat_id, args[0], args[1] if len(args) > 1 else "")
    if err == "lk.exists":
        return t(err, lang, channel=link["channel"], short=short_url(link["code"]))
    if err:
        return t(err, lang, channel=args[0], n=links.FREE_LINKS)
    return t("lk.created", lang, channel=link["channel"], short=short_url(link["code"]), url=link["url"])


def funnel_for(owner, days):
    rows = store.links_for(owner)
    return links.funnel(rows, store.link_events_for(owner, links.since(days)))


def bot_funnel(args, chat_id=None, lang=DEFAULT_LANG, **_):
    days = links.RANGES.get(args[0], 7) if args else 7
    if not chat_id or not store.links_for(chat_id):
        return t("lk.none", lang)
    f = funnel_for(chat_id, days)
    tot = f["total"]
    rate = t("lk.rate", lang, pct=tot["click_to_lot"] * 100) if tot["click_to_lot"] is not None else ""
    out = [t("lk.funnel", lang, days=days, rate=rate, **{k: tot[k] for k in links.STAGES})]
    for r in f["rows"]:
        out.append(t("lk.row", lang, channel=r["channel"], **{k: r[k] for k in links.STAGES}))
    return "\n".join(out)


# --- dashboard -------------------------------------------------------------- #

def dashboard_links(request, user=None):
    from .auth import lang as ui_lang
    lang = ui_lang()
    owner = user["owner"] if user else None
    form = request.form if request.method == "POST" else {}
    days = links.RANGES.get(request.values.get("range", "30"), 30)
    ctx = {"form": form, "owner": owner, "days": days, "ranges": list(links.RANGES), "free": links.FREE_LINKS,
           "notice": None, "error": None, "links": [], "funnel": None, "stages": links.STAGES[1:], "short": short_url,
           "default_url": _default_url(owner)}
    if request.method == "POST" and owner:
        action = form.get("action")
        if action == "create":
            link, err = create_link(owner, form.get("channel", ""), form.get("url", ""))
            if err and err != "lk.exists":
                ctx["error"] = t(err, lang, channel=form.get("channel", ""), n=links.FREE_LINKS)
            elif err == "lk.exists":
                ctx["error"] = t(err, lang, channel=link["channel"], short=short_url(link["code"]))
            else:
                ctx["notice"] = "created"
        elif action == "delete":
            store.delete_link(owner, form.get("id", 0))
        elif action == "stage":
            link = store.link_by_channel(owner, form.get("channel", ""))
            try:
                stage = links.normalise_stage(form.get("stage"))
                count = max(1, int(form.get("count") or 1))
                if link:
                    store.add_link_event(link["id"], stage, count, note="manual")
                    ctx["notice"] = "logged"
            except (links.InputError, ValueError) as exc:
                ctx["error"] = t("ui.k_err", lang, err=exc)
        elif action == "import":
            try:
                rows = links.parse_events_csv(form.get("report", ""))
                n = skipped = 0
                for r in rows:
                    link = store.link_by_channel(owner, r["channel"])
                    if not link or r["stage"] == "click":
                        skipped += 1
                        continue
                    store.add_link_event(link["id"], r["stage"], r["count"], note="import")
                    n += 1
                ctx["notice"] = t("ui.k_imported", lang, n=n, skipped=skipped)
            except links.InputError as exc:
                ctx["error"] = t("ui.k_err", lang, err=exc)
    if owner:
        ctx["links"] = store.links_for(owner)
        ctx["funnel"] = funnel_for(owner, days)
    return ctx


def redirect_target(code):
    """Count the click and hand back the destination, or None."""
    link = store.link_by_code(code)
    if not link:
        return None
    store.add_link_event(link["id"], "click", 1)
    return link["url"]
