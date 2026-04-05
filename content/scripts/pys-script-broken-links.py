import os
from pathlib import Path
import re
import pandas as pd

VAULT_PATH = Path("/Users/prashanthns/Documents/notes-remote")
BOOKS_DIR = VAULT_PATH / "Library" / "Books"
BOOKSHELF_PATH = VAULT_PATH / "Library" / "Bookshelf.md"

# 1. collect all filenames that actually exist
existing_files = {p.stem: p for p in BOOKS_DIR.glob("*.md")}  # stem = filename without .md

def slugify(title: str) -> str:
    # EXACT same logic you used to create filenames in import_goodreads.py
    t = re.sub(r"[/\\:*?\"<>|]", "", title)
    t = re.sub(r"\s+", " ", t).strip()
    t = t.replace(" ", "-")
    return t

# 2. parse all wiki-links from Bookshelf.md
links = []
with open(BOOKSHELF_PATH, "r", encoding="utf-8") as f:
    for line in f:
        # find all [[...]] segments in this line
        for match in re.finditer(r"\[\[([^\]]+)\]\]", line):
            title_text = match.group(1).strip()
            links.append(title_text)

rows = []

for link_text in links:
    # predicted filename we generated during import
    predicted_slug = slugify(link_text)

    # does that slug actually exist in the books dir?
    exists = predicted_slug in existing_files

    rows.append({
        "link_text": link_text,
        "predicted_slug": predicted_slug,
        "exists_in_books_dir": exists
    })

df = pd.DataFrame(rows).drop_duplicates()

report_path = VAULT_PATH / "Library" / "link_check_report.csv"
df.to_csv(report_path, index=False)

print(f"Report written to {report_path}")
print(df[df["exists_in_books_dir"] == False].head(20))