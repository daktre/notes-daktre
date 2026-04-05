import os
import re
import yaml
import requests
from pathlib import Path

########################################
# CONFIG: update paths if needed
########################################
VAULT_PATH = Path("/Users/prashanthns/Documents/notes-remote")
BOOKS_DIR = VAULT_PATH / "Library" / "Books"
ATTACHMENTS_DIR = VAULT_PATH / "Library" / "attachments"

ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)

########################################
# HELPERS
########################################

def extract_frontmatter(md_text):
    """
    Return (frontmatter_dict, body_text)
    frontmatter_dict will be {} if no YAML.
    """
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", md_text, flags=re.DOTALL)
    if not m:
        return {}, md_text
    yaml_block = m.group(1)
    body = m.group(2)
    try:
        fm = yaml.safe_load(yaml_block) or {}
    except Exception:
        fm = {}
    return fm, body

def clean_isbn(isbn_raw):
    """
    Normalize ISBN13 to digits only (remove spaces, dashes).
    Return '' if unusable.
    """
    if isbn_raw is None:
        return ""
    s = str(isbn_raw).strip()
    # sometimes we get things like '9781234567890.0' from CSV -> strip .0
    s = re.sub(r"\.0$", "", s)
    # remove all non-digit chars
    s = re.sub(r"[^0-9Xx]", "", s)
    # we only attempt fetch if length is 10 or 13 (OpenLibrary works with either)
    if len(s) in (10, 13):
        return s
    return ""

def fetch_cover_for_isbn(isbn):
    """
    Try large first (-L.jpg). If 404, try medium (-M.jpg).
    Return bytes if success, else None.
    """
    urls = [
        f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false",
        f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg?default=false",
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=10)
        except requests.RequestException:
            continue
        if r.status_code == 200 and r.headers.get("Content-Type", "").startswith("image"):
            return r.content
    return None

########################################
# MAIN
########################################

books = list(BOOKS_DIR.glob("*.md"))
downloaded = 0
skipped_existing = 0
skipped_no_isbn = 0
failed_fetch = 0

for book_file in books:
    file_stem = book_file.stem
    cover_path = ATTACHMENTS_DIR / f"{file_stem}.jpg"

    # Skip if we already have a cover
    if cover_path.exists():
        skipped_existing += 1
        continue

    text = book_file.read_text(encoding="utf-8")
    fm, body = extract_frontmatter(text)

    # Get ISBN13 from YAML (fallback: ISBN13, ISBN10, ISBN maybe)
    isbn_candidate = (
        fm.get("ISBN13")
        or fm.get("ISBN10")
        or fm.get("ISBN")
    )

    isbn_clean = clean_isbn(isbn_candidate)

    if not isbn_clean:
        skipped_no_isbn += 1
        continue

    img_bytes = fetch_cover_for_isbn(isbn_clean)
    if img_bytes is None:
        failed_fetch += 1
        continue

    # Save image
    with open(cover_path, "wb") as imgf:
        imgf.write(img_bytes)

    downloaded += 1
    print(f"Saved cover for {file_stem} ({isbn_clean})")

print("-----")
print(f"Downloaded new covers: {downloaded}")
print(f"Skipped (already had cover): {skipped_existing}")
print(f"Skipped (no usable ISBN): {skipped_no_isbn}")
print(f"Failed to fetch cover: {failed_fetch}")
print("Done.")