"""#16 Overexposure Monitor — the bot snapshot, the warn toggle, the dashboard.

The over-exposure warning stays free for the same reason the drawdown
sentinel's does: it is a risk line, not a convenience. See the note in
`sentineltool`.
"""

from . import exposure, store
from .brand import DEFAULT_LANG, t

SLUG = "exposure-monitor"
ICON = {"ok": "🟢", "watch": "🟡", "over": "🔴"}


def _money(x):
    return "$%s" % format(x, ",.0f")


def summary_lines(r, lang):
    lines = [t("ex.head", lang, icon=ICON[r["state"]], state=t("ex.state_" + r["state"], lang), n=len(r["positions"]),
               true=_money(r["true_risk"]), gross=_money(r["gross"]))]
    lines.append(t("ex.biggest", lang, factor=r["biggest"]["factor"], net=_money(abs(r["biggest"]["net"])),
                   side=t("ex.long" if r["biggest"]["net"] > 0 else "ex.short", lang), pct=r["concentration"] * 100))
    if "stack" in r["flags"]:
        lines.append(t("ex.stack", lang, n=len(r["stack"]["symbols"]), factor=r["stack"]["factor"], syms=", ".join(r["stack"]["symbols"])))
    if "leverage" in r["flags"]:
        lines.append(t("ex.leverage", lang, x=r["leverage"]))
    lines.append(t("ex.costs", lang, spread=_money(r["spread_total"]), swap=_money(abs(r["swap_week_total"]))))
    return lines


def _last(owner):
    row = store.last_run(SLUG, owner) if owner else None
    return row["run"] if row else None


def _snapshot(owner, text, balance=None, lang=DEFAULT_LANG, send=None):
    r = exposure.analyse(exposure.parse_positions(text), balance=balance)
    r["text"], r["balance"] = text, balance
    if owner:
        store.save_run(SLUG, r, owner=owner, label="%d pos · %s" % (len(r["positions"]), r["state"]), metric=r["concentration"])
        if send and r["state"] == "over" and store.get_setting(SLUG, owner, "warn") == "on":
            send(owner, t("ex.push", lang, true=_money(r["true_risk"]), factor=r["biggest"]["factor"], pct=r["concentration"] * 100))
    return r


def bot_exposure(args, chat_id=None, lang=DEFAULT_LANG, **_):
    from .telegram import send_message
    if args and args[0].lower() == "warn":
        if not chat_id:
            return t("ex.usage", lang)
        state = "off" if store.get_setting(SLUG, chat_id, "warn") == "on" else "on"
        store.set_setting(SLUG, chat_id, "warn", state)
        return t("ex.warn_" + state, lang)
    if args:
        try:
            r = _snapshot(chat_id, " ".join(args), lang=lang, send=send_message)
        except ValueError as exc:
            return t("ex.bad", lang, line=exc) + "\n\n" + t("ex.usage", lang)
        return "\n".join(summary_lines(r, lang) + ["", t("scan.disclaimer", lang)])
    r = _last(chat_id)
    if not r:
        return t("ex.none", lang) + "\n\n" + t("ex.usage", lang)
    return "\n".join(summary_lines(r, lang))


def dashboard_exposure(request, user=None):
    from .auth import lang as ui_lang
    from .telegram import send_message
    lang = ui_lang()
    owner = user["owner"] if user else None
    form = request.form if request.method == "POST" else {}
    ctx = {"form": form, "owner": owner, "r": None, "error": None, "icon": ICON, "money": _money, "sample": exposure.SAMPLE,
           "warn": store.get_setting(SLUG, owner, "warn") == "on" if owner else False, "lines": summary_lines}
    if request.method == "POST" and form.get("action") == "warn" and owner:
        store.set_setting(SLUG, owner, "warn", "off" if ctx["warn"] else "on")
        ctx["warn"] = not ctx["warn"]
    text = form.get("positions", "")
    if form.get("action") == "sample":
        text = exposure.SAMPLE
        ctx["form"] = dict(form, positions=text)
    if text.strip():
        try:
            balance = float(form.get("balance")) if form.get("balance") else None
            ctx["r"] = _snapshot(owner, text, balance, lang, send_message)
        except ValueError as exc:
            ctx["error"] = t("ex.bad", lang, line=exc)
    elif owner:
        ctx["r"] = _last(owner)
        if ctx["r"]:
            ctx["form"] = dict(form, positions=ctx["r"].get("text", ""), balance=ctx["r"].get("balance") or "")
    return ctx
