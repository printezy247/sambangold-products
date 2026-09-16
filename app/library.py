"""Seed data for the team file library: docs/pics/vids that ship in this
repo under `library/`, plus external links (e.g. Sam's shared Drive folder)
that aren't hosted here.

This is internal-team content, not a public download — some of it (the
Gold Recruit Manual, the Field Manual, ...) is sold as a paid ebook on
website_sam. `/team/library/<path>` is gated by `team_required` for
exactly that reason.
"""

import os

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "library")

CATEGORY_DIRS = {"docs": "doc", "pics": "pic", "vids": "vid"}


def _title_from_filename(name):
    return os.path.splitext(name)[0].replace("_", " ").strip()


def _scan(root, source):
    """Every file under root/{docs,pics,vids}/, walked recursively, as seed
    rows keyed by their path relative to `root`."""
    items = []
    for subdir, category in CATEGORY_DIRS.items():
        base = os.path.join(root, subdir)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirs, files in os.walk(base):
            for fname in sorted(files):
                rel = os.path.relpath(os.path.join(dirpath, fname), root).replace(os.sep, "/")
                sub = os.path.relpath(dirpath, base)
                items.append({
                    "category": category,
                    "title": _title_from_filename(fname),
                    "source": source,
                    "url": rel,
                    "tags": "" if sub == "." else sub.replace(os.sep, "/"),
                })
    return items


def scan_repo_files():
    """Everything committed in this repo under library/ — free-tier lead
    magnets, brand assets, the promo video. That relative path is also what
    `/team/library/<path>` serves."""
    return _scan(ROOT, "repo_asset")


def scan_paid_files(paid_root):
    """Paid-tier docs uploaded straight to the Railway volume, never git —
    see Config.PAID_LIBRARY_PATH. Empty list when the path doesn't exist
    (local dev, tests, or before the one-time upload)."""
    return _scan(paid_root, "volume")


# Links to content that lives outside this repo — not scanned, just recorded.
# The 5 paid-tier titles (10 files, EN+BM) live on Sam's Drive at
# ebooks/standard and ebooks/premium — same content that's sold on
# website_sam. Linked directly rather than mirrored anywhere, now that the
# Drive folder's "anyone with the link" permission is Viewer (was Editor —
# fixed 2026-09-17; it briefly allowed anyone with a link to edit or delete
# the actual files, not just read them).
_PAID_EBOOKS = (
    {"title": "7-Step Protocol", "id": "1mHUojqkPy0aQPt8Zfr24X7wpfDiUyYoG"},
    {"title": "Protokol 7 Langkah", "id": "1ePxI4rRu3WfqsC9QGtro0pFTDzXWqicM"},
    {"title": "Gold Trading Field Manual", "id": "1aXzq0XUi2Tno2KDOPOluZyVCfLnAtVld"},
    {"title": "Manual Padang Dagangan Emas", "id": "1ncVqww26WrWpimv1rM71ukHDcHIafcKJ"},
    {"title": "13 Trader Mindset Techniques", "id": "1gBpsxiWgMMVEwsZtXekpgWRlyYYw5XVQ"},
    {"title": "13 Teknik Minda Trader", "id": "1_dwSE9FMEi7SoVHDDjdlTQcE5GVXo8jC"},
    {"title": "Bang Bang News Gold", "id": "1hcFCZZPX00nUwSGl3ynz4aMgmpdkuhi3"},
    {"title": "Gold on News Time", "id": "1nUDCNZlTGvTHq4gZKau36IqgyMQCt1jA"},
)
_PREMIUM_EBOOKS = (
    {"title": "Gold Recruit Manual", "id": "1zd1aOjJ7BZKDheLVoEQtiKpaXwTfNK3f"},
    {"title": "Manual Rekrut Emas", "id": "1bmruZi2gNPV8BZ1ng6OOmkuKCOqnK-5n"},
)


def _drive_file(title, file_id, tags):
    return {"category": "doc", "title": title, "source": "drive",
            "url": "https://drive.google.com/file/d/%s/view" % file_id, "tags": tags}


EXTERNAL_LINKS = (
    {"category": "doc", "title": "Sam's shared Drive folder (all working files)", "source": "drive",
     "url": "https://drive.google.com/drive/folders/1KlzuoDsmWqxNtaTnoctMx4Taj61J-wRg", "tags": "drive"},
    *[_drive_file(e["title"], e["id"], "standard") for e in _PAID_EBOOKS],
    *[_drive_file(e["title"], e["id"], "premium") for e in _PREMIUM_EBOOKS],
)


def seed_data():
    return scan_repo_files() + list(EXTERNAL_LINKS)
