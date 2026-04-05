---
title: Bookshelf building
date: 2025-10-26
tags:
  - obsidian
  - bookshelf
  - workflow
  - digital-garden
created: 2025-10-26T19:35
updated: 2025-10-26T20:03
---

## 📗 Bookshelf building  
*Notes from the process of bringing my Goodreads library into Obsidian*

This note is a record of the process (and a few lessons) from migrating my [Goodreads](https://www.goodreads.com/user/show/597552-prashanth-nuggehalli-srinivas) library into my Obsidian vault to create a living, searchable bookshelf that I can link, annotate, and grow inside my own digital garden. The idea is to have my reading history and reflections co-exist with the rest of my notes.... the field notes, essays, papers, and the messy everyday fragments that sit in Obsidian. 

But doing this required a bit of tinkering. Goodreads, Markdown, and Obsidian Publish dont automatically handshake...


### 🧩 The idea

Nothing original here. Just gathed from online reading. Each book would be a Markdown note with YAML metadata on top (title, author, ISBN, year, rating, etc.), saved under `Library/Books/`.  

A single index file, `Library/Bookshelf.md`, would then display a table with all these books — including links to the individual notes and (eventually) book covers.

The whole thing would render neatly on [notes.daktre.com](https://notes.daktre.com) via *Obsidian Publish*.


### ⚙️ What you’ll need

If you’re attempting this, a few things help:

- Basic familiarity with your terminal (navigating folders, running commands).  
- A working Python 3 installation (macOS comes with one, or install via `brew install python`).  
- Comfort with running small Python scripts and reading error messages.  
- A text editor that shows hidden files.... you’ll be dealing with something called `.venv` which I didnt fully understand save that it creates a small environment within which to run pandas and the works that do the magic and gives us Markdown front matter.  
- Usual coders/learners perseverance....

Most of the code below was co-written and debugged with ChatGPT (GPT-5). It handled most of the tedious bits: generating scripts, fixing regular expressions, and translating errors from the terminal into working solutions. But without the coder's eye and mind, the code is word salad, so dont over-depend on CGPT!


### 🪜 Step 1. Export from Goodreads

In Goodreads:
```
Profile → My Books → Tools → Export Library
```

You’ll get a CSV file (`goodreads_library_export.csv`).  
Keep this safe. It’s the only way to get your data out cleanly.


### 🪄 Step 2. Convert CSV → Markdown notes

Create a working folder (outside your vault first if you prefer):

```bash
mkdir "Obsidian goodreads bookshelf"
cd "Obsidian goodreads bookshelf"
python3 -m venv .venv
source .venv/bin/activate
pip install pandas
```

Then I wrote some bad code ...then asked for help with thinking it thorugh and did some CGPT-based code back and forth to get soething that creates individual book entries

```python
# import_goodreads.py
import pandas as pd
from pathlib import Path
import re

BOOKS_DIR = Path("/Users/<yourname>/Documents/notes-remote/Library/Books")
BOOKS_DIR.mkdir(parents=True, exist_ok=True)

def slugify(title):
    t = re.sub(r"[^\w\s-]", "", title)
    t = re.sub(r"\s+", "-", t.strip())
    return t

df = pd.read_csv("goodreads_library_export.csv")

for _, row in df.iterrows():
    title = row["Title"]
    slug = slugify(title)
    md_path = BOOKS_DIR / f"{slug}.md"

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(f'Title: "{title}"\n')
        f.write(f"Author: {row['Author']}\n")
        f.write(f"Year: {row.get('Original Publication Year','')}\n")
        f.write(f"ISBN13: {row.get('ISBN13','')}\n")
        f.write(f"Rating: {int(row.get('My Rating',0))}\n")
        f.write(f"Status: {row.get('Exclusive Shelf','')}\n")
        f.write("---\n\n")
        f.write(f"![[attachments/{slug}.jpg|height=120]]\n\n")
        f.write(row.get("My Review",""))
```

Run it:

```bash
python import_goodreads.py
```

It should print:
```
✅ Done.
- Wrote 600+ book notes into /Library/Books
- Rebuilt bookshelf index at /Library/Bookshelf.md
```


### 🧱 Step 3. Fixing links and building the Bookshelf table

Initially, the table looked fine in Obsidian but broke on Publish.  
Colons and brackets in book titles made half the links dead.  
This part took a few iterations and multiple helper scripts (5 iteratiosn!).

The eventual stable setup:

1. Each file lives under `/Library/Books/<slug>.md`
2. The `Bookshelf.md` index links like `[[slug]]`
3. Cover embeds look like `![[attachments/<slug>.jpg]]` (no sizing pipes like `|height=120`, since they break Markdown tables in Publish - this was one of the reasons for many iterations & eventually these pipes pushed stuff to different columns and had broken the table)

The final rebuild script (`rebuild_bookshelf_from_files_final.py`) simply walks through the books folder and generates a clean, Publish-safe table.

```python
title_cell = f"[[{b['file_stem']}]]"
year_cell = str(b['year']).replace('.0', '')
```

The fixing of the table script was heavily relied for CGPT.....was just not able to debug with my level of familirity....


### 🧠 Step 4. Dealing with dead links

Even after cleanup, some titles didn’t link correctly.  
To catch them, a small diagnostic script (`link_check_report.py`) looped through the table, tested every `[[title]]`, and flagged mismatches.  Once the mismatched slugs were found, they could be automatically corrected with another patch script.  

This process sounds tedious, but once the scripts were written, re-running them took seconds.


### 🖼️ Step 5. Adding covers

This was the most satisfying part.

```python
# fetch_covers.py
import requests, yaml, re
from pathlib import Path

BOOKS_DIR = Path("/Users/<yourname>/...path/Library/Books")
ATT_DIR = BOOKS_DIR.parent / "attachments"
ATT_DIR.mkdir(exist_ok=True)

for md in BOOKS_DIR.glob("*.md"):
    text = md.read_text(encoding="utf-8")
    m = re.search(r"ISBN13:\s*(\d+)", text)
    if not m: continue
    isbn = m.group(1)
    url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false"
    r = requests.get(url)
    if r.status_code == 200:
        with open(ATT_DIR / f"{md.stem}.jpg", "wb") as f:
            f.write(r.content)
            print("Saved cover for", md.stem)
```

Run it inside your venv:
```bash
pip install requests
python fetch_covers.py
```

After a few minutes, the bookshelf fills up with actual book jackets.  
Famous titles almost always have covers. Some Indian or obscure academic ones don’t... those can be added manually by dropping a JPG with the same filename as the book note.

### 🧰 Step 6. Publish

In *Obsidian Publish*, make sure:
- `publish.css` exists in the root (for custom styles)
- all the new `/Library/Books/` and `/Library/attachments/` files are included

Then hit **Review changes → Publish all**.

You might need to hard refresh (`Shift + Reload`) on Safari or add a version query (`?v=1001`) to see new CSS or covers. For quite a while this simple thing threw me off!

### 🧩 Reflections

The point of this was never to rebuild Goodreads ....it was to make my reading life part of the same thinking space where everything else lives.  What’s exciting about this approach is that it’s *interlinkable*.  A note about governance or fieldwork can now directly link to a book note...and over time, reading notes can branch into reflections, essays, or even teaching slides.  It’s messy and alive, not static.

### 🪞 Credits & nudges for others

All the code here was co-written with ChatGPT (GPT-5), iteratively debugged, step by step.  
It’s worth repeating: you don’t need to be a programmer to do this — but you do need to be willing to tinker a little, read your terminal output, and not panic at errors.  

If you’re trying this yourself, start small.... maybe import ten books first.  
Once your pipeline works, the rest will follow.


**Related:** [[Bookshelf]] 

---
Last updated: 2025-12-30 16:02

---
Last updated: 2025-12-30 16:03
