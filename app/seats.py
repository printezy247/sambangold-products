"""Seats — the Rambo rank carrying other people.

A group lead or an IB does not want ten subscriptions. They want their team on
the same tools, under one bill, and they want to take a seat back the day
someone leaves.

A seat is not a new kind of record. It is an ordinary entitlement with
`source="seat"` and a `granted_by` naming the holder who pays for it, so every
question the rest of the app already asks ("what rank is this owner?") answers
correctly without knowing seats exist. Two consequences fall out for free:

* A seat cannot outlive the rank behind it. It carries the holder's expiry, so
  when the holder lapses, the seats lapse on the same tick.
* A seat never outranks its holder. It is granted at the holder's own tier.
"""

from . import store
from .brand import DEFAULT_LANG, t
from .gate import allows, owner_tier
from .tiers import seats_for

FEATURE = "seats"


def _key(holder, member):
    return "seat:%s:%s" % (holder, member)


def capacity(holder_tier):
    return seats_for(holder_tier)


def occupied(holder):
    return store.seats_granted_by(holder)


def free_seats(holder, holder_tier=None):
    holder_tier = holder_tier or owner_tier(str(holder), signed_in=True)
    return max(0, capacity(holder_tier) - len(occupied(holder)))


def _expiry(holder, holder_tier):
    """When the holder's own rank runs out — the seat can last exactly that long.

    None when any grant at that rank has no expiry; otherwise the latest of
    them, because that is the one still standing when the others lapse.
    """
    ends = [row["expires_at"] for row in store.entitlements_for(holder) if row["tier_key"] == holder_tier]
    if not ends or any(e is None for e in ends):
        return None
    return max(ends)


def add(holder, member, holder_tier=None):
    """(seat_rows, error_key). The member gets the holder's rank and expiry."""
    holder, member = str(holder).strip(), str(member).strip()
    holder_tier = holder_tier or owner_tier(holder, signed_in=True)
    if not allows(holder_tier, FEATURE):
        return None, "st.need"
    if not member:
        return None, "st.usage"
    if member == holder:
        return None, "st.self"
    if any(row["owner"] == member for row in occupied(holder)):
        return None, "st.already"
    if free_seats(holder, holder_tier) <= 0:
        return None, "st.full"

    store.grant_entitlement(member, holder_tier, source="seat", external_id=_key(holder, member),
                            expires_at=_expiry(holder, holder_tier), granted_by=holder)
    return occupied(holder), None


def remove(holder, member):
    """Take a seat back. Only the holder who granted it can."""
    holder, member = str(holder).strip(), str(member).strip()
    if not any(row["owner"] == member for row in occupied(holder)):
        return None, "st.unknown"
    store.revoke_entitlement(external_id=_key(holder, member))
    return occupied(holder), None


def sync(holder):
    """Re-point every seat at the holder's current rank and expiry.

    Called after the holder's own rank changes, so a downgrade reaches the
    team instead of leaving the seats above the rank paying for them.
    """
    tier = owner_tier(str(holder), signed_in=True)
    rows = occupied(holder)
    if not allows(tier, FEATURE):
        for row in rows:
            store.revoke_entitlement(external_id=row["external_id"], status="expired")
        return {"kept": 0, "dropped": len(rows)}
    keep = rows[:capacity(tier)]
    for row in rows[len(keep):]:
        store.revoke_entitlement(external_id=row["external_id"], status="expired")
    expires = _expiry(holder, tier)
    for row in keep:
        store.grant_entitlement(row["owner"], tier, source="seat", external_id=row["external_id"],
                                expires_at=expires, granted_by=holder)
    return {"kept": len(keep), "dropped": len(rows) - len(keep)}


# --- bot -------------------------------------------------------------------- #

def bot_seats(args, chat_id=None, lang=DEFAULT_LANG, **_):
    """`/seats` lists them, `/seats add <id>` and `/seats remove <id>` move them."""
    if not chat_id:
        return t("st.usage", lang)
    tier = owner_tier(str(chat_id), signed_in=True)
    if not allows(tier, FEATURE):
        from .gate import upgrade_line
        return "%s\n\n%s" % (upgrade_line(FEATURE, lang), t("gate.where", lang))

    sub = (args[0].lower() if args else "")
    if sub in ("add", "remove") and len(args) > 1:
        rows, err = (add if sub == "add" else remove)(chat_id, args[1])
        if err:
            return t(err, lang, n=capacity(tier))
        return t("st." + ("added" if sub == "add" else "removed"), lang, who=args[1],
                 used=len(rows), total=capacity(tier))

    rows = occupied(chat_id)
    lines = [t("st.head", lang, used=len(rows), total=capacity(tier))]
    lines += ["• <code>%s</code>" % row["owner"] for row in rows] or [t("st.empty", lang)]
    lines += ["", t("st.usage", lang)]
    return "\n".join(lines)


# --- dashboard -------------------------------------------------------------- #

def dashboard_seats(request, user=None):
    owner = (user or {}).get("owner")
    tier = (user or {}).get("rank") or "public"
    ctx = {"allowed": allows(tier, FEATURE), "rows": [], "total": capacity(tier), "error": None}
    if not owner or not ctx["allowed"]:
        return ctx
    if request.method == "POST" and request.form.get("seat_action"):
        action = request.form["seat_action"]
        member = (request.form.get("member") or "").strip()
        _, err = (add if action == "add" else remove)(owner, member, **({"holder_tier": tier} if action == "add" else {}))
        ctx["error"] = err
    ctx["rows"] = occupied(owner)
    return ctx
