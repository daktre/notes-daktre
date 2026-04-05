import os
import re
import yaml
from pathlib import Path

########################################
# CONFIG: update if needed
########################################
VAULT_PATH = Path("/Users/prashanthns/Documents/notes-remote")
BOOKS_DIR = VAULT_PATH / "Library" / "Books"
BOOKSHELF_PATH = VAULT_PATH / "Library" / "Bookshelf.md"

########################################
# HELPERS
########################################

def normalize_year(raw_year):
    """
    Take whatever was in YAML 'Year' and normalize it:
    - If it's like '1995.0', return '1995'
    - If it's '', return '—'
    - Else return as-is (string)
    """
    if raw_year is None:
        return "—"
    y = str(raw_year).strip()
    if y == "":
        return "—"
    # if it's like 1995.0 -> 1995
    m = re.match(r"^(\d+)\.0$", y)
    if m:
        return m.group(1)
    return y

def read_book_note(path: Path):
    """
    Read a single book .md file and return structured fields:
    - file_stem (used for linking)
    - title (YAML Title or fallback to stem)
    - author (string or '—')
    - year (normalized)
    - status (Read / To Read / Reading / —)
    - stars (⭐⭐⭐ from Rating)
    - cover_rel (attachments/...jpg without any |height)
    """
    text = path.read_text(encoding="utf-8")

    # Extract YAML block
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, flags=re.DOTALL)
    if not m:
        frontmatter = {}
        body = text
    else:
        yaml_block = m.group(1)
        body = m.group(2)
        try:
            frontmatter = yaml.safe_load(yaml_block) or {}
        except Exception:
            frontmatter = {}
            body = text

    # Title from YAML
    raw_title = frontmatter.get("Title")
    if isinstance(raw_title, str) and raw_title.strip():
        title = raw_title.strip()
    else:
        title = path.stem  # fallback

    # Author from YAML
    raw_author = frontmatter.get("Author", "")
    if isinstance(raw_author, list):
        author = ", ".join([str(a).strip() for a in raw_author])
    else:
        author = str(raw_author).strip()
    if not author:
        author = "—"

    # Year normalization
    year_val = normalize_year(frontmatter.get("Year", ""))

    # Status
    status_val = str(frontmatter.get("Status", "")).strip()
    status_val = status_val if status_val else "—"

    # Rating -> stars
    rating_val = str(frontmatter.get("Rating", "")).strip()
    if rating_val.isdigit():
        stars = "⭐" * int(rating_val)
    else:
        stars = ""

    # Find cover embed in body and strip any sizing
    cover_rel = ""
    cover_match = re.search(r"!\[\[(attachments\/[^\|\]]+)(?:\|[^\]]*)?\]\]", body)
    if cover_match:
        cover_rel = cover_match.group(1)  # attachments/Some-Book.jpg

    return {
        "file_stem": path.stem,
        "title": title,
        "author": author,
        "year": year_val,
        "status": status_val,
        "stars": stars,
        "cover_rel": cover_rel
    }

########################################
# MAIN BUILD
########################################

books = []
for md_file in BOOKS_DIR.glob("*.md"):
    info = read_book_note(md_file)
    books.append(info)

# Sort alphabetically by title (human title, not stem)
books.sort(key=lambda b: b["title"].lower())

header = """# 📚 Bookshelf

This is my reading shelf. Click a title to open notes, highlights, and thoughts about each book.

| Cover | Title | Author | Year | Status | Rating |
|:------|:------|:-------|:-----|:-------|:-------|
"""

rows = []
for b in books:
    # Cover cell — no pipes in embed to avoid breaking table
    cover_cell = f"![[{b['cover_rel']}]]" if b["cover_rel"] else ""

    # Title cell:
    # Use only the internal link [[file_stem]]
    # Do NOT append human-readable title after it (to avoid visual duplication).
    title_cell = f"[[{b['file_stem']}]]"

    # Other cells
    author_cell = b["author"]
    year_cell = b["year"]
    status_cell = b["status"]
    rating_cell = b["stars"]

    row_md = (
        f"| {cover_cell} | {title_cell} | {author_cell} | {year_cell} | {status_cell} | {rating_cell} |"
    )
    rows.append(row_md)

footer = "\n_Last updated: rebuilt from files (final layout)_\n"

BOOKSHELF_PATH.write_text(
    header + "\n".join(rows) + "\n" + footer,
    encoding="utf-8"
)

print("✅ Rebuilt Bookshelf.md with no duplicate title text and cleaned year.")
print(f"Rows written: {len(rows)}")
print("Now republish and verify final layout + no decimal years.")