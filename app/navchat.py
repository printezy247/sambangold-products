""""Ask and locate files" on the team dashboard. Two layers:

1. **Local search** — always on, no API key needed. Scores file_items by
   word overlap against title/tags/category. This alone answers "where's
   the prop firm calculator spec" today.
2. **AI layer** — optional. When `NARA_API_KEY`/`NARA_BASE_URL`/`NARA_MODEL`
   are all set (Config), the top local matches are handed to an
   OpenAI-compatible chat-completions endpoint for a conversational answer
   on top of the same results. Never blocks or breaks the page: any
   network/API/parsing failure just means no AI answer that request.

`NARA_MODEL` is a comma-separated priority list ("free-model,paid-model,...").
Each request works through them in order and stops at the first one that
answers — a rate limit, an outage, a malformed response, or an unavailable
model on one just rotates to the next rather than failing the whole
request. Each model gets up to `NARA_MAX_RETRIES` attempts before moving
on, and the whole rotation is capped by `NARA_TIME_BUDGET_SECONDS` — a hard
wall-clock ceiling well under gunicorn's 30s worker timeout (Dockerfile),
so a long model list can never make the page itself time out. Once the
budget runs out, whatever's left in the list is simply skipped.
"""

import re
import time

import requests

REQUEST_TIMEOUT_SECONDS = 8      # per HTTP attempt
DEFAULT_MAX_RETRIES = 1          # extra attempts per model after the first
DEFAULT_TIME_BUDGET_SECONDS = 20  # whole rotation, all models/retries combined


def _words(text):
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def search_files(query, items, limit=8):
    """Items scored by how many query words appear in title/tags/category.
    Zero-score items are dropped; ties keep the original (category, title)
    order from store.file_items()."""
    q_words = _words(query)
    if not q_words:
        return []
    scored = []
    for it in items:
        haystack = _words(it["title"]) | _words(it.get("tags", "")) | _words(it["category"])
        score = len(q_words & haystack)
        if score:
            scored.append((score, it))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [it for _score, it in scored[:limit]]


def _models(config):
    return [m.strip() for m in (config.get("NARA_MODEL") or "").split(",") if m.strip()]


def configured(config):
    return bool(config.get("NARA_API_KEY") and config.get("NARA_BASE_URL") and _models(config))


def _extract_text(response_json):
    """The reply text, or None if the shape isn't what's expected — covers
    a missing field as cleanly as a null one, so nothing downstream ever
    calls .strip() on a non-string."""
    try:
        content = response_json["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None
    return content.strip() if isinstance(content, str) and content.strip() else None


def _try_model(url, headers, model, messages, timeout):
    """One HTTP attempt. Returns the answer text, or None for any failure
    at all — network, HTTP status, or an unexpected/empty response body.
    Deliberately broad: this is a best-effort convenience layer on top of
    local search, which already answers the request on its own, so no
    failure here should ever be allowed to reach the caller as an
    exception."""
    try:
        r = requests.post(url, headers=headers,
                          json={"model": model, "messages": messages, "max_tokens": 200, "temperature": 0.2},
                          timeout=timeout)
        r.raise_for_status()
        return _extract_text(r.json())
    except Exception:  # noqa: BLE001 — any failure here just means "try the next model"
        return None


def ai_answer(query, matches, config, lang="en"):
    """A short conversational answer grounded in `matches` (already-found
    local results — the AI explains/ranks, it doesn't invent new files).
    Works through NARA_MODEL's priority list, retrying each one up to
    NARA_MAX_RETRIES times, until something answers or the time budget
    runs out. Returns None if unconfigured or nothing answers in time;
    never raises."""
    if not configured(config):
        return None

    max_retries = int(config.get("NARA_MAX_RETRIES") or DEFAULT_MAX_RETRIES)
    time_budget = float(config.get("NARA_TIME_BUDGET_SECONDS") or DEFAULT_TIME_BUDGET_SECONDS)
    timeout = float(config.get("NARA_TIMEOUT_SECONDS") or REQUEST_TIMEOUT_SECONDS)

    listing = "\n".join(
        "%d. %s (%s)%s" % (i + 1, it["title"], it["category"], (" — " + it["tags"]) if it.get("tags") else "")
        for i, it in enumerate(matches)
    ) or "(no local matches found)"
    system = (
        "You help Sam's internal team find files in a docs/pics/vids library. "
        "Answer in %s, in 2-3 short sentences. Only reference files from the numbered "
        "list below — never invent a file that isn't listed. If nothing fits, say so "
        "plainly and suggest rephrasing.\n\nFiles:\n%s"
    ) % ("Bahasa Melayu" if lang == "ms" else "English", listing)
    messages = [{"role": "system", "content": system}, {"role": "user", "content": query}]
    url = config["NARA_BASE_URL"].rstrip("/") + "/chat/completions"
    headers = {"Authorization": "Bearer %s" % config["NARA_API_KEY"]}

    deadline = time.monotonic() + time_budget
    for model in _models(config):
        for _attempt in range(max_retries + 1):
            if time.monotonic() >= deadline:
                return None   # out of time — skip whatever's left in the list
            answer = _try_model(url, headers, model, messages, timeout)
            if answer:
                return answer
    return None
