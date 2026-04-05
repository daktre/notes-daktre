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

def read_book_note(path: Path):
    """
    Read a single book .md file and return structured fields:
    - file_stem (used for linking)
    - title (YAML Title or fallback to stem)
    - author (string)
    - year (string or '—')
    - status (Read / To Read / Reading / —)
    - stars (e.g. ⭐⭐⭐)
    - cover_rel (attachments/...jpg without the |height part)
    """
    text = path.read_text(encoding="utf-8")

    # Extract YAML
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

    # Title
    raw_title = frontmatter.get("Title")
    if isinstance(raw_title, str):
        title = raw_title.strip()
    else:
        title = path.stem

    # Author
    raw_author = frontmatter.get("Author", "")
    if isinstance(raw_author, list):
        author = ", ".join([str(a).strip() for a in raw_author])
    else:
        author = str(raw_author).strip()
    if not author:
        author = "—"

    # Year
    year = str(frontmatter.get("Year", "")).strip() or "—"

    # Status
    status = str(frontmatter.get("Status", "")).strip() or "—"

    # Rating -> stars
    rating_val = str(frontmatter.get("Rating", "")).strip()
    if rating_val.isdigit():
        stars = "⭐" * int(rating_val)
    else:
        stars = ""

    # Find cover embed and strip any |height=... so there's no "|" in table
    # Original body embed looks like:
    # ![[attachments/Some-Book.jpg|height=240]]
    # We'll capture just attachments/Some-Book.jpg
    cover_rel = ""
    cover_match = re.search(r"!\[\[(attachments\/[^\|\]]+)(?:\|[^\]]*)?\]\]", body)
    if cover_match:
        cover_rel = cover_match.group(1)  # just "attachments/Some-Book.jpg"

    return {
        "file_stem": path.stem,
        "title": title,
        "author": author,
        "year": year,
        "status": status,
        "stars": stars,
        "cover_rel": cover_rel
    }

########################################
# MAIN
########################################

books = []
for md_file in BOOKS_DIR.glob("*.md"):
    info = read_book_note(md_file)
    books.append(info)

# Sort alphabetically by title for stable output
books.sort(key=lambda b: b["title"].lower())

header = """# 📚 Bookshelf

This is my reading shelf. Click a title to open notes, highlights, and thoughts about each book.

| Cover | Title | Author | Year | Status | Rating |
|:------|:------|:-------|:-----|:-------|:-------|
"""

rows = []
for b in books:
    # Cover cell: IMPORTANT → no `|height=120` here.
    # We just embed the image without sizing so we don't introduce a "|" into the table cell.
    cover_cell = f"![[{b['cover_rel']}]]" if b["cover_rel"] else ""

    # Title cell: link to file_stem, then human-readable title as plain text.
    # NO alias form `[[file|title]]`, because `|` inside the link broke layout.
    title_cell = f"[[{b['file_stem']}]] {b['title']}"

    author_cell = b["author"]
    year_cell = b["year"]
    status_cell = b["status"]
    rating_cell = b["stars"]

    row_md = (
        f"| {cover_cell} | {title_cell} | {author_cell} | {year_cell} | {status_cell} | {rating_cell} |"
    )
    rows.append(row_md)

footer = "\n_Last updated: rebuilt from files (no sizing pipes)_\n"

BOOKSHELF_PATH.write_text(
    header + "\n".join(rows) + "\n" + footer,
    encoding="utf-8"
)

print("✅ Rebuilt Bookshelf.md with pipe-safe table cells.")
print(f"Rows written: {len(rows)}")
print("Now republish Library/Bookshelf.md and re-check column alignment + labels.")