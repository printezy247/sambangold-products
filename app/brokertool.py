"""#12 Broker Comparator — the bot card, the public table, the referral card, the observation form."""

import secrets

from . import brokers, feeds, store
from .brand import DEFAULT_LANG, t

SLUG = "broker-comparator"


def _quote():
    try:
        q = feeds.gold_quote()
        return q, format(q["mid"], ",.2f"), (format(q["spread"], ",.2f") if q["spread"] is not None else "n/a")
    except feeds.FeedError:
        return None, "—", "—"


def ranked(lots=1.0, nights=0, side="long"):
    try:
        obs = store.observations()
    except RuntimeError:          # no app context (the surface-contract test calls handlers bare)
        obs = []
    return brokers.rank(brokers.blend(brokers.SEED, obs), lots, nights, side)


def card_text(lang, lots=1.0, nights=0, owner=None, limit=6):
    _, mid, spread = _quote()
    lines = [t("bc.head", lang, lots=lots, nights=nights, mid=mid, spread=spread)]
    for r in ranked(lots, nights)[:limit]:
        obs = t("bc.obs", lang, n=r["n_obs"]) if r["source"] == "observed" else ""
        lines.append(t("bc.row", lang, rank=r["rank"], name=r["name"], account=r["account"], obs=obs, **r["cost"]))
    url = store.get_setting(SLUG, owner, "reflink") if owner else ""
    lines += ["", t("bc.foot", lang, date=brokers.SEED_DATE, link=t("bc.link", lang, url=url) if url else t("bc.nolink", lang))]
    return "\n".join(lines)


def bot_goldspread(args, chat_id=None, lang=DEFAULT_LANG, **_):
    lots, nights = 1.0, 0
    try:
        if args:
            lots = float(args[0].replace(",", ""))
        if len(args) > 1:
            nights = brokers.parse_holding(args[1])
    except ValueError:
        return t("bc.usage", lang)
    if lots <= 0 or lots > 1000:
        return t("bc.usage", lang)
    return card_text(lang, lots, nights, owner=chat_id)


def dashboard_brokers(request, user=None):
    from .auth import lang as ui_lang
    lang = ui_lang()
    owner = user["owner"] if user else None
    form = request.values
    ctx = {"form": form, "owner": owner, "notice": None, "error": None, "seed_date": brokers.SEED_DATE,
           "reflink": store.get_setting(SLUG, owner, "reflink") if owner else "",
           "refname": store.get_setting(SLUG, owner, "refname") if owner else "",
           "code": store.get_setting(SLUG, owner, "cardcode") if owner else "", "brokers": brokers.SEED}
    if request.method == "POST" and owner and form.get("action") == "reflink":
        store.set_setting(SLUG, owner, "reflink", form.get("reflink", ""))
        store.set_setting(SLUG, owner, "refname", form.get("refname", ""))
        if not ctx["code"]:
            ctx["code"] = secrets.token_urlsafe(6)
            store.set_setting(SLUG, owner, "cardcode", ctx["code"])
        ctx["reflink"], ctx["refname"], ctx["notice"] = form.get("reflink", "").strip(), form.get("refname", "").strip(), "saved"
    if request.method == "POST" and owner and form.get("action") == "observe":
        key = brokers.find(form.get("broker", ""))
        try:
            spread = float(form.get("spread", ""))
            if not key or not (0 < spread <= 5):
                raise ValueError
            store.add_observation(owner, key, spread, form.get("slippage") or None)
            ctx["notice"] = "observed"
        except ValueError:
            ctx["error"] = t("ui.b_obs_bad", lang)
    try:
        lots = float(form.get("lots", 1) or 1)
        nights = brokers.parse_holding(form.get("nights", "0") or "0")
    except ValueError:
        lots, nights = 1.0, 0
    side = "short" if form.get("side") == "short" else "long"
    ctx.update({"lots": lots, "nights": nights, "side": side, "rows": ranked(lots, nights, side)})
    ctx["quote"], ctx["mid"], ctx["feed_spread"] = _quote()
    return ctx


def card_page(code, lots=1.0, nights=0):
    owner = store.owner_by_setting(SLUG, "cardcode", code)
    if not owner:
        return None
    _, mid, spread = _quote()
    return {"rows": ranked(lots, nights)[:8], "lots": lots, "nights": nights, "mid": mid, "feed_spread": spread,
            "reflink": store.get_setting(SLUG, owner, "reflink"), "refname": store.get_setting(SLUG, owner, "refname"),
            "seed_date": brokers.SEED_DATE}
