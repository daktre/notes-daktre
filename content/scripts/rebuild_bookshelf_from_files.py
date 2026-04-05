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
    Read a single book .md file and return:
    - file_stem (used for linking)
    - title (from YAML Title)
    - author
    - year
    - status
    - stars (⭐⭐⭐ from Rating)
    - cover_rel (attachments/...jpg)
    """
    text = path.read_text(encoding="utf-8")

    # Extract YAML front matter
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
        title = path.stem  # fallback

    # Author (could be list or string)
    raw_author = frontmatter.get("Author", "")
    if isinstance(raw_author, list):
        author = ", ".join([str(a).strip() for a in raw_author])
    else:
        author = str(raw_author).strip()

    # Year
    year = str(frontmatter.get("Year", "")).strip()

    # Status
    status = str(frontmatter.get("Status", "")).strip()

    # Rating -> stars
    rating_val = str(frontmatter.get("Rating", "")).strip()
    stars = ""
    if rating_val.isdigit():
        stars = "⭐" * int(rating_val)

    # Find first cover embed in body
    cover_rel = ""
    cover_match = re.search(r"!\[\[(attachments\/[^\|\]]+)(?:\|[^\]]*)?\]\]", body)
    if cover_match:
        cover_rel = cover_match.group(1)

    return {
        "file_stem": path.stem,  # filename without .md
        "title": title,
        "author": author if author else "—",
        "year": year if year else "—",
        "status": status if status else "—",
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

# Sort alphabetically by title for stable output
books.sort(key=lambda b: b["title"].lower())

header = """# 📚 Bookshelf

This is my reading shelf. Click a title to open notes, highlights, and thoughts about each book.

| Cover | Title | Author | Year | Status | Rating |
|:------|:------|:-------|:-----|:-------|:-------|
"""

rows = []
for b in books:
    # Cover cell
    if b["cover_rel"]:
        cover_cell = f"![[{b['cover_rel']}|height=120]]"
    else:
        cover_cell = ""  # leave blank if no cover yet

    # Title cell:
    # We do NOT use the alias form [[file|Title]] because the "|" inside breaks table layout.
    # Instead we show the internal link, then the human title as plain text.
    # Example: [[Some-File-Name]] Some Book Title
    link_part = f"[[{b['file_stem']}]] {b['title']}"

    author_cell = b["author"]
    year_cell = b["year"]
    status_cell = b["status"]
    rating_cell = b["stars"]

    row_md = (
        f"| {cover_cell} | {link_part} | {author_cell} | {year_cell} | {status_cell} | {rating_cell} |"
    )
    rows.append(row_md)

footer = "\n_Last updated: rebuilt from files_\n"

BOOKSHELF_PATH.write_text(
    header + "\n".join(rows) + "\n" + footer,
    encoding="utf-8"
)

print("✅ Rebuilt Bookshelf.md with stable link format and clean columns.")
print(f"Rows written: {len(rows)}")
print("Now republish Library/Bookshelf.md and test links again.")