"""#11 Churn Radar — the bot commands and the dashboard context."""

import datetime as dt

from . import churn, store
from . import gate

NO_CAP = 10 ** 6   # a rank with no client cap still needs a number to slice with
from .brand import DEFAULT_LANG, t

SLUG = "churn-radar"
ICON = {"risk": "🔴", "watch": "🟡", "healthy": "🟢"}


def _flags(c, lang):
    return ", ".join(t("chn.f_" + f, lang) for f in c["flags"]) or "—"


def detail_text(c, lang):
    lines = [t("chn.detail", lang, icon=ICON[c["band"]], band=t("chn.band_" + c["band"], lang), **{k: v for k, v in c.items() if k != "band"})]
    if c["flags"]:
        lines.append("")
        lines.append("<b>%s</b>" % t("chn.do", lang))
        for f in c["flags"]:
            why, do = churn.interventions(lang)[f]
            lines.append("• %s %s" % (why, do))
    return "\n".join(lines)


def bot_ibchurn(args, chat_id=None, lang=DEFAULT_LANG, **_):
    row = store.last_run(SLUG, chat_id) if chat_id else None
    if not row:
        return t("chn.none", lang) + "\n\n" + t("chn.usage", lang)
    run = row["run"]
    if args:
        acc = args[0].lstrip("@")
        c = next((c for c in run["clients"] if c["account"] == acc), None)
        return detail_text(c, lang) if c else t("chn.no_client", lang, account=acc)
    s = run["summary"]
    lines = [t("chn.top", lang, n=s["clients"], as_of=s["as_of"], risk=s["risk"], watch=s["watch"], healthy=s["healthy"],
               at_risk=s["at_risk"], rev=s["revenue_recent"])]
    top = [c for c in run["clients"] if c["band"] != "healthy"][:5] or run["clients"][:3]
    for c in top:
        lines.append(t("chn.row", lang, icon=ICON[c["band"]], account=c["account"], prob=c["prob"], at_risk=c["at_risk"], flags=_flags(c, lang)))
    return "\n".join(lines)


def _text_or_file(request, field):
    text = (request.form.get(field) or "").strip()
    if not text and field in request.files and request.files[field].filename:
        text = request.files[field].read().decode("utf-8-sig", "replace")
    return text


def dashboard_churn(request, user=None):
    from .auth import lang as ui_lang
    lang = ui_lang()
    owner = user["owner"] if user else None
    form = {k: v for k, v in request.form.items()} if request.method == "POST" else {}
    ctx = {"form": form, "run": None, "run_id": None, "error": None, "owner": owner, "runs": [], "icon": ICON,
           "flags": _flags, "interventions": churn.interventions(lang), "free": gate.limit("clients", user=user) or NO_CAP,
           "client": None, "notes": [], "notice": None}
    if request.method == "POST" and form.get("action") == "note" and owner and form.get("account") and form.get("note", "").strip():
        store.add_note(SLUG, owner, form["account"].strip(), form["note"])
        ctx["notice"] = "ok"
    if request.method == "POST" and form.get("action") == "sample":
        form.update({"log": churn.sample_log(), "rate": form.get("rate") or "6", "action": "run"})
        ctx["form"] = form
    if request.method == "POST" and form.get("action") == "run":
        text = form.get("log") or _text_or_file(request, "log")
        form["log"] = text
        try:
            rows = churn.parse_log(text)
            rate = float(form.get("rate") or 6)
            as_of = dt.date.fromisoformat(form["as_of"]) if form.get("as_of") else None
            run = churn.scan_book(rows, rate, as_of)
            ctx["run"] = run
            ctx["run_id"] = store.save_run(SLUG, run, owner=owner, label=run["summary"]["as_of"], metric=run["summary"]["at_risk"])
        except (churn.InputError, ValueError) as exc:
            ctx["error"] = t("ui.n_err", lang, err=exc)
    if ctx["run"] is None and owner:
        last = store.last_run(SLUG, owner)
        if last:
            ctx["run"], ctx["run_id"] = last["run"], last["id"]
    acc = request.args.get("account") or (form.get("account") if form.get("action") == "note" else None)
    if ctx["run"] and acc:
        ctx["client"] = next((c for c in ctx["run"]["clients"] if c["account"] == acc), None)
        if owner and ctx["client"]:
            ctx["notes"] = store.notes_for(SLUG, owner, acc)
    if owner:
        ctx["runs"] = store.runs_for(SLUG, owner)
        ctx["all_notes"] = store.notes_for(SLUG, owner)
    return ctx
