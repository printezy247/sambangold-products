"""#10 Rebate Reconciliation Auditor — the bot commands and the dashboard context."""

from . import rebate, store
from .brand import DEFAULT_LANG, t


def _num(v):
    return float(str(v).replace(",", "").replace("$", ""))


# --- bot -------------------------------------------------------------------- #

def bot_rebateaudit(args, chat_id=None, lang=DEFAULT_LANG, **_):
    if len(args) >= 3:
        try:
            lots, rate, paid = _num(args[0]), _num(args[1]), _num(args[2])
        except ValueError:
            return t("reb.usage", lang)
        expected = lots * rate
        diff = expected - paid
        label = t("reb.short" if diff > 0.01 else ("reb.over" if diff < -0.01 else "reb.exact"), lang)
        return t("reb.quick", lang, lots=lots, rate=rate, expected=expected, paid=paid, label=label, diff=abs(diff))
    if args:
        return t("reb.usage", lang)
    run = store.last_rebate_run(chat_id) if chat_id else None
    if not run:
        return t("reb.none", lang) + "\n\n" + t("reb.usage", lang)
    return summary_text(run, lang)


def summary_text(row, lang):
    s = row["run"]["summary"]
    return t("reb.summary", lang, broker=row["broker"] or "—", period=row["period"] or "—", expected=s["expected"],
             paid=s["paid"], shortfall=s["shortfall"], flagged=s["flagged"], accounts=s["accounts"],
             missing=s["by_kind"]["missing_account"], rate=s["by_kind"]["silent_rate_change"],
             excluded=s["by_kind"]["excluded_symbol"])


def bot_rebatestatus(args, chat_id=None, lang=DEFAULT_LANG, **_):
    run = store.last_rebate_run(chat_id) if chat_id else None
    if not run:
        return t("reb.none", lang)
    return t("reb.status", lang, period=run["period"] or "—", shortfall=run["run"]["summary"]["shortfall"], id=run["id"])


# --- dashboard -------------------------------------------------------------- #

def _text_or_file(request, field):
    text = (request.form.get(field) or "").strip()
    if not text and field in request.files and request.files[field].filename:
        text = request.files[field].read().decode("utf-8-sig", "replace")
    return text


def dashboard_rebate(request, user=None):
    from .auth import lang as ui_lang
    lang = ui_lang()
    owner = user["owner"] if user else None
    form = dict(request.form) if request.method == "POST" else {}
    form = {k: (v[0] if isinstance(v, list) else v) for k, v in form.items()}
    ctx = {"form": form, "run": None, "run_id": None, "errors": [], "owner": owner, "runs": [],
           "sort": request.args.get("sort", "diff"), "kinds": rebate.KINDS}
    if request.method == "POST" and form.get("action") == "sample":
        form.update({"statement": rebate.SAMPLE_STATEMENT, "log": rebate.SAMPLE_LOG, "rate": rebate.SAMPLE_RATE,
                     "overrides": rebate.SAMPLE_OVERRIDES, "broker": form.get("broker") or "Sample Broker",
                     "period": form.get("period") or "2026-08"})
        ctx["form"] = form
        form["action"] = "run"
    if request.method == "POST" and form.get("action") == "run":
        stmt_text = form.get("statement") or _text_or_file(request, "statement")
        log_text = form.get("log") or _text_or_file(request, "log")
        form["statement"], form["log"] = stmt_text, log_text
        stmt = log = card = None
        try:
            stmt = rebate.parse_csv(stmt_text, need_paid=True)
        except rebate.InputError as exc:
            ctx["errors"].append(t("ui.r_err_stmt", lang, err=exc))
        try:
            log = rebate.parse_csv(log_text)
        except rebate.InputError as exc:
            ctx["errors"].append(t("ui.r_err_log", lang, err=exc))
        try:
            card = rebate.parse_rates(form.get("rate", ""), form.get("overrides", ""), form.get("tiers", ""))
        except rebate.InputError as exc:
            ctx["errors"].append(t("ui.r_err_rate", lang, err=exc))
        if stmt and log and card:
            run = rebate.reconcile(stmt, log, *card)
            run.update({"broker": form.get("broker", "").strip(), "period": form.get("period", "").strip(),
                        "rate": card[0], "overrides": form.get("overrides", "").strip(), "tiers": form.get("tiers", "").strip()})
            ctx["run"] = run
            ctx["run_id"] = store.save_rebate_run(run, owner=owner)
    if ctx["run"]:
        ctx["findings"] = rebate.sort_findings(ctx["run"]["findings"], ctx["sort"], desc=ctx["sort"] not in ("account", "symbol", "kind"))
    if owner:
        ctx["runs"] = store.rebate_runs_for(owner)
    return ctx


def pdf_for(run_id, owner=None, brand="SAMBANGGOLD"):
    row = store.get_rebate_run(run_id)
    if not row or (row["owner"] and row["owner"] != (str(owner) if owner else None)):
        return None, None
    name = "rebate-dispute-%s-%s.pdf" % ((row["broker"] or "broker").replace(" ", "-").lower(), row["period"] or run_id)
    return name, rebate.dispute_pdf(row["run"], brand=brand)
