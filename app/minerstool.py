"""#18 Miner–Bullion Divergence Screener — the bot digest, single-name readout, weekly push, the dashboard."""

import datetime as dt

from . import miners, store
from .brand import DEFAULT_LANG, t

SLUG = "miner-divergence"
FLAG_ICON = {"decoupled": "🔌", "lagging": "🐢", "leading": "🚀", "squeeze": "🧯", "earnings": "📅"}
DIGEST_N = 6


def _pct(x):
    return ("%+.1f%%" % x) if x is not None else "—"


def _num(x, nd=2):
    return format(x, ".%df" % nd) if x is not None else "—"


def row_line(r, lang):
    icons = "".join(FLAG_ICON[f] for f in r["flags"])
    return t("mn.row", lang, ticker=r["ticker"], res=_pct(r["residual"]), ret=_pct(r["ret_20"]), beta=_num(r["beta"]), icons=icons)


def digest_lines(s, lang):
    lines = [t("mn.head", lang, week=s["week"], spot=format(s["spot"], ",.0f"), n=len(s["rows"]))]
    lines += [row_line(r, lang) for r in s["rows"][:DIGEST_N]]
    lines.append(t("mn.legend", lang))
    if s["errors"]:
        lines.append(t("mn.partial", lang, n=len(s["errors"])))
    lines.append(t("mn.question", lang))
    return lines


def name_lines(r, lang):
    lines = [t("mn.n_head", lang, ticker=r["ticker"], name=r["name"], price=format(r["price"], ",.2f"), kind=t("mn.kind_" + r["kind"], lang))]
    lines.append(t("mn.n_beta", lang, beta=_num(r["beta"]), corr=_num(r["corr"]), beta20=_num(r["beta_20"]), corr20=_num(r["corr_20"])))
    lines.append(t("mn.n_move", lang, ret=_pct(r["ret_20"]), gold=_pct(r["gold_20"]), explained=_pct(r["explained"]), res=_pct(r["residual"])))
    if r["aisc"]:
        lines.append(t("mn.n_margin", lang, aisc=format(r["aisc"], ","), spot=format(r["spot"], ",.0f"), margin=format(r["margin"], ","), pct=_pct(r["margin_pct"]), asof=r["aisc_as_of"]))
    else:
        lines.append(t("mn.n_noaisc_" + ("etf" if r["kind"] == "etf" else "royalty"), lang))
    if r["earnings"]:
        lines.append(t("mn.n_earnings", lang, date=r["earnings"], days=r["earnings_in"]))
    for f in r["flags"]:
        lines.append(FLAG_ICON[f] + " " + t("mn.f_" + f, lang, res=_pct(r["residual"]), corr=_num(r["corr_20"]), pct=_pct(r["margin_pct"]), days=r["earnings_in"]))
    lines.append(t("mn.question", lang))
    return lines


def _screen():
    return miners.screen(miners.history())


def bot_miners(args, chat_id=None, lang=DEFAULT_LANG, **_):
    if args and args[0].lower() == "weekly":
        if not chat_id:
            return t("mn.usage", lang)
        state = "off" if store.get_setting(SLUG, chat_id, "weekly") == "on" else "on"
        store.set_setting(SLUG, chat_id, "weekly", state)
        return t("mn.weekly_" + state, lang)
    try:
        s = _screen()
    except miners.FeedError as exc:
        return t("mn.down", lang, err=str(exc)[:80])
    if args:
        ticker = args[0].upper().lstrip("$")
        r = next((r for r in s["rows"] if r["ticker"] == ticker), None)
        if not r:
            return t("mn.unknown", lang, ticker=ticker, universe=", ".join(u["ticker"] for u in miners.UNIVERSE))
        return "\n".join(name_lines(r, lang) + ["", t("scan.disclaimer", lang)])
    return "\n".join(digest_lines(s, lang) + ["", t("scan.disclaimer", lang)])


def check_weekly(send, today=None):
    """Monday digest to every chat that switched it on, once per ISO week. Called by the five-minute checker; never raises."""
    today = today or dt.date.today()
    if today.weekday() != 0:
        return 0
    owners = store.owners_by_setting(SLUG, "weekly", "on")
    if not owners:
        return 0
    week = miners.week_key(today)
    try:
        s = miners.screen(miners.history(), today)
    except Exception:  # noqa: BLE001 — a dead feed must not break the checker
        return 0
    pushed = 0
    for owner in owners:
        if store.get_setting(SLUG, owner, "weekly_sent") == week:
            continue
        lang = store.tg_lang(owner) or DEFAULT_LANG
        send(owner, "\n".join(digest_lines(s, lang)))
        store.set_setting(SLUG, owner, "weekly_sent", week)
        pushed += 1
    return pushed


def svg_chart(chart, width=720, height=220):
    """Name (gold colour) and bullion (chrome) rebased to 100, inline SVG."""
    if len(chart) < 2:
        return ""
    vals = [v for p in chart for v in p[1:]]
    lo, hi = min(vals) - 2, max(vals) + 2
    t0, t1 = chart[0][0], chart[-1][0]
    pad = 44

    def x(ts):
        return pad + (ts - t0) / max(1, t1 - t0) * (width - pad - 10)

    def y(v):
        return height - 20 - (v - lo) / (hi - lo) * (height - 30)

    def line(idx, colour):
        return '<polyline points="%s" fill="none" stroke="%s" stroke-width="2"/>' % (" ".join("%.1f,%.1f" % (x(p[0]), y(p[idx])) for p in chart), colour)

    return ('<svg viewBox="0 0 %d %d" width="100%%" role="img" style="max-width:100%%;height:auto">' % (width, height)
            + '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#9aa3b2" stroke-dasharray="4 4"/>' % (x(t0), y(100), x(t1), y(100))
            + line(2, "#b7c0ce") + line(1, "#f5d76e")
            + ''.join('<text x="2" y="%.1f" font-size="10" fill="#9aa3b2" font-family="monospace">%.0f</text>' % (y(v) + 3, v) for v in (lo + 2, 100, hi - 2))
            + '</svg>')


def dashboard_miners(request, user=None):
    from .auth import lang as ui_lang
    lang = ui_lang()
    owner = user["owner"] if user else None
    sort = request.args.get("sort", "residual")
    ctx = {"s": None, "error": None, "sort": sort, "rows": [], "detail": None, "svg": None, "icon": FLAG_ICON,
           "pct": _pct, "num": _num, "lines": name_lines, "owner": owner, "universe": miners.UNIVERSE,
           "weekly": store.get_setting(SLUG, owner, "weekly") == "on" if owner else False}
    if request.method == "POST" and request.form.get("action") == "weekly" and owner:
        store.set_setting(SLUG, owner, "weekly", "off" if ctx["weekly"] else "on")
        ctx["weekly"] = not ctx["weekly"]
    try:
        ctx["s"] = _screen()
    except miners.FeedError as exc:
        ctx["error"] = t("mn.down", lang, err=str(exc)[:120])
        return ctx
    ctx["rows"] = miners.sort_rows(ctx["s"]["rows"], sort)
    ticker = (request.args.get("ticker") or "").upper()
    if ticker:
        ctx["detail"] = next((r for r in ctx["s"]["rows"] if r["ticker"] == ticker), None)
        if ctx["detail"]:
            ctx["svg"] = svg_chart(ctx["detail"]["chart"])
    return ctx
