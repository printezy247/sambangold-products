""""Ask and locate files" on the team dashboard. Two layers:

1. **Local search** — always on, no API key needed. Scores file_items by
   word overlap against title/tags/category. This alone answers "where's
   the prop firm calculator spec" today.
2. **AI layer** — optional. When `NARA_API_KEY`/`NARA_BASE_URL`/`NARA_MODEL`
   are all set (Config), the top local matches are handed to an
   OpenAI-compatible chat-completions endpoint for a conversational answer
   on top of the same results. Never blocks or breaks the page: any
   network/API failure just means no AI answer that request.

`NARA_MODEL` is a comma-separated priority list ("free-model,paid-model,...").
Each request tries them in order and stops at the first one that answers —
a rate limit, an outage, or an unavailable model on one just rotates to the
next rather than failing the whole request.
"""

import re

import requests

TIMEOUT = 15


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


def ai_answer(query, matches, config, lang="en"):
    """A short conversational answer grounded in `matches` (already-found
    local results — the AI explains/ranks, it doesn't invent new files).
    Tries each model in NARA_MODEL's priority order, returning the first
    one that answers. Returns None if unconfigured or every model fails;
    never raises."""
    if not configured(config):
        return None

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

    for model in _models(config):
        try:
            r = requests.post(url, headers=headers,
                              json={"model": model, "messages": messages, "max_tokens": 200, "temperature": 0.2},
                              timeout=TIMEOUT)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except (requests.RequestException, KeyError, IndexError, ValueError, TypeError):
            continue   # this model failed — rotate to the next one in the list
    return None
