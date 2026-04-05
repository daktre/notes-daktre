import pandas as pd
import os
from pathlib import Path
import re
import math

########################################
# CONFIG: EDIT THESE TWO PATHS IF NEEDED
########################################

VAULT_PATH = Path.home() / "/Users/prashanthns/Documents/notes-remote"
CSV_PATH = Path.home() / "/Users/prashanthns/Documents/Codebook/Obsidian goodreads bookshelf/goodreads_library_export.csv"

BOOKS_DIR = VAULT_PATH / "Library" / "Books"
ATTACHMENTS_DIR = VAULT_PATH / "Library" / "attachments"
BOOKSHELF_PATH = VAULT_PATH / "Library" / "Bookshelf.md"

# if folders don't exist, create them
BOOKS_DIR.mkdir(parents=True, exist_ok=True)
ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)

########################################
# HELPERS
########################################

def slugify(title: str) -> str:
    # turn book title into safe filename
    t = re.sub(r"[/\\:*?\"<>|]", "", title)  # remove illegal filename chars
    t = re.sub(r"\s+", " ", t).strip()       # collapse whitespace
    t = t.replace(" ", "-")
    return t

def stars(n):
    # convert numeric rating to "⭐⭐⭐"
    try:
        n_float = float(n)
        n_int = int(math.floor(n_float))
        return "⭐" * n_int
    except:
        return ""

########################################
# LOAD CSV
########################################

df = pd.read_csv(CSV_PATH)

# Safety: handle missing optional columns
def safe(row, col):
    return (str(row[col]) if col in row and not (pd.isna(row[col])) else "").strip()

########################################
# GENERATE INDIVIDUAL BOOK FILES
########################################

rows_for_shelf = []  # we'll use this to build Bookshelf.md

for _, row in df.iterrows():
    title = safe(row, "Title")
    if not title:
        continue

    author = safe(row, "Author")
    isbn13 = safe(row, "ISBN13")
    my_rating = safe(row, "My Rating")
    my_review = safe(row, "My Review")
    exclusive_shelf = safe(row, "Exclusive Shelf")  # e.g. read / to-read / currently-reading
    shelves_raw = safe(row, "Bookshelves")          # comma-separated shelves
    date_read = safe(row, "Date Read")
    date_added = safe(row, "Date Added")
    pub_year = safe(row, "Original Publication Year")

    # Normalize status
    # Goodreads shelf names are usually "read", "to-read", "currently-reading"
    status_map = {
        "read": "Read",
        "to-read": "To Read",
        "currently-reading": "Reading"
    }
    status = status_map.get(exclusive_shelf.lower(), exclusive_shelf.title() or "To Read")

    # filename
    file_slug = slugify(title)
    file_path = BOOKS_DIR / f"{file_slug}.md"

    # expected cover path (you can later drop a jpg with this name in attachments/)
    cover_filename = f"{file_slug}.jpg"
    cover_embed_rel = f"attachments/{cover_filename}"

    # YAML front matter
    yaml_block = f"""---
Title: "{title}"
Author: ["{author}"]
Status: {status}
Rating: {my_rating if my_rating != '' else ""}
DateAdded: {date_added}
DateRead: {date_read}
Year: {pub_year}
ISBN13: {isbn13}
Shelves: "{shelves_raw}"
Tags:
  - Book
Cover: "[[{cover_embed_rel}]]"
---
"""

    # Body content for the book note
    body_block = f"""
![[{cover_embed_rel}|height=240]]

## Review
{my_review if my_review else "_(no review yet)_"}

## Reading status
- Status: {status}
- My rating: {my_rating if my_rating else "—"} {stars(my_rating)}
- Date started / added: {date_added if date_added else "—"}
- Date finished: {date_read if date_read else "—"}

## Metadata
- Author: {author}
- Year: {pub_year if pub_year else "—"}
- ISBN13: {isbn13 if isbn13 else "—"}
- Shelves (Goodreads): {shelves_raw if shelves_raw else "—"}
"""

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(yaml_block.strip() + "\n\n" + body_block.strip() + "\n")

    # Save info to later build Bookshelf.md row
    rows_for_shelf.append({
        "title": title,
        "author": author,
        "year": pub_year,
        "status": status,
        "rating_num": my_rating,
        "rating_stars": stars(my_rating),
        "cover_rel": cover_embed_rel,
        "file_slug": file_slug,
    })

########################################
# BUILD THE Bookshelf.md TABLE
########################################

header = """# 📚 Bookshelf

This is an index of books I've tracked or reviewed. Click a title to read notes, highlights, and reflections.

| Cover | Title | Author | Year | Status | Rating |
|:------|:------|:-------|:-----|:-------|:-------|
"""

rows_md = []
for r in rows_for_shelf:
    # Obsidian-style embed for cover, wiki link for title
    row_md = (
        f"| ![[{r['cover_rel']}|height=120]]"
        f" | [[{r['title']}]]"
        f" | {r['author'] if r['author'] else '—'}"
        f" | {r['year'] if r['year'] else '—'}"
        f" | {r['status'] if r['status'] else '—'}"
        f" | {r['rating_stars']} |"
    )
    rows_md.append(row_md)

footer = f"""

_Last updated: script import_
"""

with open(BOOKSHELF_PATH, "w", encoding="utf-8") as f:
    f.write(header + "\n".join(rows_md) + "\n" + footer)

print("✅ Done.")
print(f"- Wrote {len(rows_for_shelf)} book notes into {BOOKS_DIR}")
print(f"- Rebuilt bookshelf index at {BOOKSHELF_PATH}")
print("Next: add cover JPGs in Library/attachments/ with the same slug names, republish, done.")