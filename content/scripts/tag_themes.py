#!/usr/bin/env python3
"""
Step 4 — AI Theme & Geography Tagging
=======================================
Reads the enriched Zotero JSON (after running enrich_dois.py) and uses
the Claude API to assign controlled-vocabulary themes and geography tags
to each publication based on title + abstract.

Run from your vault root:

    python3 tag_themes.py

Input:  data/zotero_daktre_publications.json   (already enriched)
Output: data/zotero_daktre_publications.json   (in-place, adds themes + geography)
        data/zotero_daktre_publications_pretheme_backup.json

Requirements:
    pip install anthropic
    Set ANTHROPIC_API_KEY environment variable, e.g.:
        export ANTHROPIC_API_KEY=sk-ant-...
"""

import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic package not installed.")
    print("Run: pip install anthropic")
    sys.exit(1)

# ── Config ───────────────────────────────────────────────────────────────────
INPUT_JSON  = Path("data/zotero_daktre_publications.json")
BACKUP_JSON = Path("data/zotero_daktre_publications_pretheme_backup.json")
OUTPUT_JSON = INPUT_JSON

MODEL       = "claude-sonnet-4-20250514"
SLEEP_SEC   = 0.3   # between API calls
# ─────────────────────────────────────────────────────────────────────────────

# ── Controlled Vocabularies ───────────────────────────────────────────────────
#
# Edit these lists if you want to add/remove/rename themes or geographies.
# The AI will ONLY assign tags from these lists — nothing invented.
#
THEMES = [
    "Health equity",
    "Tribal and Adivasi health",
    "Child health and nutrition",
    "Maternal health",
    "Non-communicable diseases",
    "Infectious and zoonotic diseases",
    "COVID-19",
    "One Health",
    "Health systems and policy",
    "Primary health care",
    "Access to medicines",
    "Capacity building",
    "Universal health coverage",
    "Governance and patient rights",
    "Tobacco control",
    "Mental health",
    "Antimicrobial resistance",
    "Research methods",
    "Biodiversity and ecology",
    "Child development and neurodevelopment",
    "Sickle cell and rare diseases",
    "Gender and social determinants",
    "Community participation",
    "Global health",
]

GEOGRAPHIES = [
    "Karnataka",
    "Kerala",
    "Tamil Nadu",
    "Assam",
    "South India",
    "India",
    "South Asia",
    "Sub-Saharan Africa",
    "Low- and middle-income countries",
    "Global",
]
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""You are a precise academic metadata tagger for a public health researcher's publications database.

Your job: given a publication title and abstract, assign the most relevant tags from two controlled lists.

THEMES (assign 1–4 that genuinely apply):
{json.dumps(THEMES, indent=2)}

GEOGRAPHIES (assign 1–3 that genuinely apply, from most specific to most general):
{json.dumps(GEOGRAPHIES, indent=2)}

Rules:
- Only use tags EXACTLY as written in the lists above. No variations, no new tags.
- Be selective — prefer fewer precise tags over many loose ones.
- For geography, prefer the most specific applicable tag (e.g. "Karnataka" over just "India" if Karnataka is mentioned).
- Always include "India" if the study is set in India, even if you also include a state.
- If global or multi-country, use "Global" or "Low- and middle-income countries" as appropriate.
- Respond ONLY with a JSON object, no preamble, no explanation:
  {{"themes": ["...", "..."], "geography": ["...", "..."]}}"""

def tag_item(client, title, abstract):
    """Call Claude to assign themes and geography. Returns (themes, geography) lists."""
    content = f"Title: {title}"
    if abstract:
        # Truncate abstract to keep tokens reasonable
        content += f"\n\nAbstract: {abstract[:1200]}"

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}]
        )
        raw = response.content[0].text.strip()
        # Strip any accidental markdown fences
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        parsed = json.loads(raw)
        themes    = [t for t in parsed.get("themes", [])    if t in THEMES]
        geography = [g for g in parsed.get("geography", []) if g in GEOGRAPHIES]
        return themes, geography
    except Exception as e:
        print(f"        ⚠  API error: {e}")
        return [], []

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
        print("Set it with: export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    if not INPUT_JSON.exists():
        print(f"ERROR: {INPUT_JSON} not found.")
        print("Run enrich_dois.py first, then run this script.")
        sys.exit(1)

    # Backup before tagging
    shutil.copy(INPUT_JSON, BACKUP_JSON)
    print(f"✓ Backup saved → {BACKUP_JSON}")

    data = json.loads(INPUT_JSON.read_text(encoding="utf-8"))
    n    = len(data)
    print(f"✓ Loaded {n} items\n")

    client = anthropic.Anthropic(api_key=api_key)

    stats = {"tagged": 0, "skipped_existing": 0, "failed": 0}

    for i, item in enumerate(data, 1):
        title    = item.get("title", "").strip()
        abstract = item.get("abstract", "").strip()
        prefix   = f"[{i:3}/{n}]"

        if not title:
            print(f"{prefix} — skipping (no title): {item.get('id')}")
            stats["failed"] += 1
            continue

        # Skip if already tagged (re-run safety)
        if item.get("themes") and item.get("geography"):
            print(f"{prefix} ↷ already tagged: {title[:60]}")
            stats["skipped_existing"] += 1
            continue

        print(f"{prefix} {title[:70]}")

        themes, geography = tag_item(client, title, abstract)

        if themes or geography:
            item["themes"]    = themes
            item["geography"] = geography
            stats["tagged"] += 1
            print(f"         Themes   : {', '.join(themes) or '(none)'}")
            print(f"         Geography: {', '.join(geography) or '(none)'}")
        else:
            stats["failed"] += 1
            print(f"         ⚠ tagging failed — themes/geography left empty")

        print()
        time.sleep(SLEEP_SEC)

    # Save
    OUTPUT_JSON.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"""
{'='*65}
 Tagging Summary
{'='*65}
 Tagged successfully  : {stats['tagged']}
 Already had tags     : {stats['skipped_existing']}
 Failed / no title    : {stats['failed']}
 Total items          : {n}
{'='*65}

 Saved tagged JSON → {OUTPUT_JSON}

 Next steps:
   rm publications/*.md
   rm -rf _generated/
   python3 scripts/zotero_to_obsidian.py
   python3 scripts/build_pubs_index.py
   git add -A && git commit -m "Add AI-generated themes and geography tags"
   git push
   (then Publish changes in Obsidian UI)

 TIP: Run this script again at any time to fill gaps — it skips
 items that already have both themes and geography set.
""")

if __name__ == "__main__":
    main()
