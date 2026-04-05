import os
from pathlib import Path
import re
import pandas as pd

# --- CONFIG: update this if path differs ---
VAULT_PATH = Path("/Users/prashanthns/Documents/notes-remote")
BOOKSHELF_PATH = VAULT_PATH / "Library" / "Bookshelf.md"
REPORT_PATH = VAULT_PATH / "Library" / "link_check_report.csv"
BOOKS_DIR = VAULT_PATH / "Library" / "Books"

# 1. load what files actually exist in Library/Books
existing_files = {p.stem: p for p in BOOKS_DIR.glob("*.md")}

# 2. load the link check report
df = pd.read_csv(REPORT_PATH)

# We will build a mapping of:
#   original link text (as it appears now in [[ ... ]])  ->  fixed wiki link [[slug|original text]]
# for all rows, not just the False ones, so we normalize everything consistently.
replacements = {}

for _, row in df.iterrows():
    link_text = str(row["link_text"]).strip()
    predicted_slug = str(row["predicted_slug"]).strip()

    # If predicted_slug actually exists as a file in Library/Books, use that.
    # If it doesn't exist (edge case), we'll fall back to link_text (so we don't break something that was already working).
    if predicted_slug in existing_files:
        fixed_wikilink = f"[[{predicted_slug}|{link_text}]]"
    else:
        # leave as-is (this is likely already working)
        fixed_wikilink = f"[[{link_text}]]"

    replacements[link_text] = fixed_wikilink

# 3. read existing Bookshelf.md into memory
with open(BOOKSHELF_PATH, "r", encoding="utf-8") as f:
    bookshelf_md = f.read()

# 4. Replace every [[...]] with the corrected form
# We'll use a regex that finds [[...]] and swaps based on link_text.
def repl(match):
    original_inner = match.group(1).strip()  # the text inside [[ ... ]]
    if original_inner in replacements:
        return replacements[original_inner]
    else:
        # if somehow we didn't compute a replacement, just return the original
        return f"[[{original_inner}]]"

fixed_md = re.sub(r"\[\[([^\]]+)\]\]", repl, bookshelf_md)

# 5. write back Bookshelf.md (overwrite)
with open(BOOKSHELF_PATH, "w", encoding="utf-8") as f:
    f.write(fixed_md)

print("✅ Bookshelf.md has been patched with slug|title links where possible.")
print("Now republish and test links on the live site.")