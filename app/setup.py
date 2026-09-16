"""My Setup — the answers a tool should never ask twice.

Eighteen tools, and almost every one of them opens by asking the same four
things: which broker, how big the account, which prop firm, how many lots a
month. Someone answers them once, likes the result, comes back a week later and
has to answer them all again. That is the friction that turns a good tool into
a tool nobody returns to.

So the answers live here instead, once per owner, and every surface reads them:

* the dashboard pre-fills the form, so a tool page can answer before anything
  is typed;
* the bot's ``/setup`` command reads and writes the same values with buttons;
* nothing is required — a blank setup behaves exactly as the tools did before.

Two rules keep this safe. A prefill only ever touches a **GET**, and every
dashboard handler that writes gates on ``request.method == "POST"``, so no
prefilled value can trigger a write. And a real answer always wins: a value the
visitor typed is never overwritten by a saved one.
"""

from .brand import DEFAULT_LANG, t

SLUG = "setup"

CHANNELS = (("Telegram", "telegram"), ("WhatsApp", "whatsapp"), ("TikTok", "tiktok"),
            ("Instagram", "instagram"), ("YouTube", "youtube"))


def _firm_options():
    """The prop firms the rule packs actually know. `custom` needs its own numbers."""
    from .sentinel import PACKS
    return tuple((p["name"], key) for key, p in PACKS.items() if key != "custom")


def _broker_options():
    from .brokers import SEED
    return tuple((v["name"], key) for key, v in SEED.items())


def F(key, kind, options=None, lo=None, hi=None, strict=False):
    """One saved answer.

    `strict` means the value must be one of the offered options — a prop firm
    has to match a rule pack to be worth anything. A broker does not: someone
    may well use one the table has never heard of, and refusing their answer
    would be worse than storing it.
    """
    return {"key": key, "kind": kind, "options": options, "lo": lo, "hi": hi, "strict": strict}


FIELDS = (
    F("broker",  "choice", _broker_options),
    F("size",    "number", lo=1, hi=100_000_000),
    F("firm",    "choice", _firm_options, strict=True),
    F("lots",    "number", lo=0, hi=1_000_000),
    F("rate",    "number", lo=0, hi=10_000),
    F("clients", "number", lo=0, hi=1_000_000),
    F("channel", "choice", lambda: CHANNELS, strict=True),
)
BY_KEY = {f["key"]: f for f in FIELDS}
KEYS = tuple(f["key"] for f in FIELDS)


def options_for(field):
    """The buttons for one field. A callable so the broker and firm lists stay
    the same lists the tools themselves use, not a second copy that drifts."""
    opts = field["options"]
    return tuple(opts() if callable(opts) else (opts or ()))


def label(key, lang=DEFAULT_LANG):
    return t("set.f_" + key, lang)


def hint(key, lang=DEFAULT_LANG):
    return t("set.t_" + key, lang)


def show(key, value, lang=DEFAULT_LANG):
    """What the visitor sees: the option's label where there is one, else the raw value."""
    field = BY_KEY.get(key)
    if not field:
        return value
    for text, val in options_for(field):
        if val == value:
            return text
    return value


# --- storage ---------------------------------------------------------------- #

def read(owner):
    """Everything saved for this owner. Empty answers are simply absent."""
    from . import store
    if not owner:
        return {}
    out = {}
    for key in KEYS:
        value = store.get_setting(SLUG, owner, key)
        if value:
            out[key] = value
    return out


def clean(key, raw):
    """One answer, validated. Returns (value, error_key); "" clears the field."""
    field = BY_KEY.get(key)
    if field is None:
        return None, "set.unknown"
    value = (raw or "").strip()
    if not value:
        return "", None
    if field["kind"] == "number":
        try:
            number = float(value.replace(",", "").replace("$", ""))
        except ValueError:
            return None, "set.bad_number"
        if (field["lo"] is not None and number < field["lo"]) or (field["hi"] is not None and number > field["hi"]):
            return None, "set.out_of_range"
        return ("%d" % number) if number == int(number) else ("%g" % number), None
    value = value[:60]
    lowered = value.lower()
    values = [v for _, v in options_for(field)]
    if lowered in values:
        return lowered, None
    if field["strict"]:
        return None, "set.not_an_option"
    return value, None


def save(owner, form):
    """Write the keys present in `form`. Returns (saved, {key: error_key}).

    Only keys the form carries are touched, so one panel can save one field
    without wiping the rest.
    """
    from . import store
    errors = {}
    for key in KEYS:
        if key not in form:
            continue
        value, err = clean(key, form.get(key))
        if err:
            errors[key] = err
            continue
        store.set_setting(SLUG, owner, key, value)
    return read(owner), errors


def clear(owner):
    from . import store
    for key in KEYS:
        store.set_setting(SLUG, owner, key, "")


def filled(owner):
    """How many of the answers are in, out of how many there are."""
    return len(read(owner)), len(KEYS)


# --- prefill ----------------------------------------------------------------- #
#
# Tool form field -> setup key. A tool is absent here when nothing it asks for
# is anything we already know; guessing would be worse than a blank field.

PREFILL = {
    "prop-calculator":       {"size": "size"},
    "ib-revenue-calculator": {"lots": "lots", "rate": "rate", "clients": "clients", "broker": "broker"},
    "monte-carlo-sim":       {"firm": "firm"},
    "broker-comparator":     {"lots": "lots"},
    "drawdown-sentinel":     {"firm": "firm", "balance": "size"},
    "rebate-auditor":        {"rate": "rate"},
    "churn-radar":           {"rate": "rate"},
    "link-attribution":      {"channel": "channel"},
}


def prefill(slug, owner):
    """The form defaults this owner's setup supplies for one tool."""
    saved = read(owner)
    return {field: saved[key] for field, key in PREFILL.get(slug, {}).items() if saved.get(key)}


class _Prefilled:
    """A stand-in for the request whose `values` carry the saved answers.

    Everything else — `method`, `form`, `files`, `args` — is the real request,
    so a handler cannot tell the difference except in the one place it should.
    """

    def __init__(self, request, values):
        object.__setattr__(self, "_request", request)
        object.__setattr__(self, "values", values)

    def __getattr__(self, name):
        return getattr(self._request, name)


def merge(request, slug, owner):
    """The request a dashboard handler should see.

    The real one on a POST, when there is no owner, or when the setup adds
    nothing. Otherwise a wrapper whose `values` fall back to the saved answers
    — typed values always win, so this can only ever fill a gap.
    """
    if request.method != "GET" or not owner:
        return request
    extra = prefill(slug, owner)
    if not extra:
        return request
    from werkzeug.datastructures import MultiDict
    values = MultiDict(request.values)
    added = False
    for field, value in extra.items():
        if not values.get(field):
            values[field] = value
            added = True
    return _Prefilled(request, values) if added else request


def used_by(slug, owner):
    """The setup keys one tool page is actually reading, for the 'we filled
    this in' note. Empty when the page filled in nothing."""
    saved = read(owner)
    return [key for field, key in PREFILL.get(slug, {}).items() if saved.get(key)]


# --- surfaces ----------------------------------------------------------------- #

def lines(owner, lang=DEFAULT_LANG):
    """One readable line per saved answer."""
    saved = read(owner)
    return ["%s: <b>%s</b>" % (label(key, lang), show(key, saved[key], lang)) for key in KEYS if saved.get(key)]


def bot_setup(args, chat_id=None, lang=DEFAULT_LANG, **_):
    """`/setup` reads it back, `/setup key=value ...` writes, `/setup clear` empties it."""
    owner = str(chat_id) if chat_id else ""
    if not owner:
        return t("set.usage", lang)
    if args and args[0].lower() in ("clear", "kosong", "reset"):
        clear(owner)
        return t("set.cleared", lang)
    pairs = {k.strip().lower(): v for k, _, v in (a.partition("=") for a in args) if k.strip().lower() in BY_KEY}
    if args and not pairs:
        return "%s\n\n%s" % (t("set.usage", lang), t("set.keys", lang, keys=", ".join(KEYS)))
    notice = ""
    if pairs:
        _, errors = save(owner, pairs)
        notice = "\n".join(t(err, lang, field=label(key, lang)) for key, err in errors.items()) or t("set.saved", lang)
    body = lines(owner, lang)
    head = t("set.bot_h", lang) if body else t("set.none", lang)
    return "\n".join([p for p in (notice, head) if p] + body + ["", t("set.bot_tail", lang)])


def dashboard_setup(request, user=None):
    """The /setup page and the dashboard card read the same context."""
    from .auth import lang as ui_lang
    lang = ui_lang()
    owner = user["owner"] if user else None
    ctx = {"owner": owner, "fields": FIELDS, "options": options_for, "label": label, "hint": hint,
           "saved": read(owner), "errors": {}, "notice": None, "keys": KEYS}
    if request.method == "POST" and owner:
        if request.form.get("action") == "clear":
            clear(owner)
            ctx.update(saved={}, notice="cleared")
        else:
            saved, errors = save(owner, {k: request.form.get(k) for k in KEYS if k in request.form})
            ctx.update(saved=saved, errors={k: t(v, lang, field=label(k, lang)) for k, v in errors.items()},
                       notice="saved" if not errors else None)
    ctx["done"] = len(ctx["saved"])
    return ctx
