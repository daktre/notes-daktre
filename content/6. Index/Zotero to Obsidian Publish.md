# Zotero → Obsidian Publish: Publications Pipeline
### notes-remote vault · notes.daktre.com

This README documents the **complete pipeline** for publishing academic publications from Zotero to a public digital garden. It is written to be self-contained — if you give this file to an AI assistant, it should be able to help you recreate or maintain the entire system from scratch.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Repository Structure](#2-repository-structure)
3. [Prerequisites & One-Time Setup](#3-prerequisites--one-time-setup)
4. [The Four Enrichment Scripts](#4-the-four-enrichment-scripts)
5. [Full Pipeline: First-Time Run](#5-full-pipeline-first-time-run)
6. [Routine Update (New Publications)](#6-routine-update-new-publications)
7. [Obsidian Publish Notes](#7-obsidian-publish-notes)
8. [Script Reference](#8-script-reference)
9. [Controlled Vocabularies](#9-controlled-vocabularies)
10. [Troubleshooting](#10-troubleshooting)
11. [Architecture Decisions & History](#11-architecture-decisions--history)

---

## 1. System Overview

**The problem this solves:** Zotero exports publications with Google Scholar URLs by default. This pipeline enriches those exports with real DOIs, PubMed links, abstracts, keywords, AI-generated themes, and geography tags — then publishes them as a browseable digital garden.

**Source of truth:** Zotero collection (curated list of authored/co-authored works)

**Published site:** https://notes.daktre.com (Obsidian Publish, site ID: `daktre-notes`)

**Public landing page:** https://notes.daktre.com/3.+Resources/Publications

### Data flow

```
Zotero collection
      │
      ▼
data/zotero_daktre_publications.json    ← Zotero export (CSL JSON)
      │
      ▼
scripts/enrich_dois.py                  ← Step 1–3: DOI + PMID + abstract + keywords
      │
      ▼
scripts/tag_themes.py                   ← Step 4: AI theme + geography tagging
      │
      ▼
scripts/zotero_to_obsidian.py           ← Generates publications/*.md
      │
      ▼
scripts/build_pubs_index.py             ← Generates _generated/publications/* + assets/pubs_index.json
      │
      ▼
git push → Obsidian Publish UI → notes.daktre.com
```

---

## 2. Repository Structure

```
notes-remote/                          ← vault root (iCloud-synced Obsidian vault)
│
├── data/
│   ├── zotero_daktre_publications.json           ← PRIMARY INPUT (Zotero export)
│   └── zotero_daktre_publications_backup.json    ← Auto-backup (created by enrich script)
│
├── scripts/
│   ├── enrich_dois.py          ← Steps 1–3: DOI/PMID/abstract/keyword enrichment
│   ├── tag_themes.py           ← Step 4: AI theme + geography tagging (Claude API)
│   ├── zotero_to_obsidian.py   ← Converts enriched JSON → one .md per publication
│   └── build_pubs_index.py     ← Builds browse pages + JSON index
│
├── publications/               ← GENERATED: one .md per publication (132+ files)
│   └── YYYY-title-slug-popXXXXX.md
│
├── _generated/
│   └── publications/           ← GENERATED: browse pages
│       ├── by-theme-index.md
│       ├── by-theme-*.md       ← one per theme (24 themes)
│       └── by-year-YYYY.md     ← one per year (2005–present)
│
├── assets/
│   └── pubs_index.json         ← GENERATED: machine-readable index of all publications
│
├── 3. Resources/
│   └── Publications.md         ← MANUAL: public landing page (do not delete)
│
├── .venv/                      ← Python virtual environment (not committed)
├── .gitignore
└── README.md                   ← this file
```

**Rules:**
- Never manually edit anything in `publications/` or `_generated/` — these are fully regenerated each run
- The only manually maintained file in this pipeline is `3. Resources/Publications.md`
- `data/zotero_daktre_publications.json` is overwritten by Zotero export + enrichment scripts

---

## 3. Prerequisites & One-Time Setup

### 3.1 Software required

- **Zotero 8+** — https://zotero.org (for managing and exporting publications)
- **Python 3.10+** — comes with macOS, or install via Homebrew: `brew install python3`
- **Git** — for version control and pushing to GitHub
- **Obsidian Desktop** — with the vault open and Obsidian Publish configured
- **Obsidian Publish** — paid subscription, site ID: `daktre-notes`

### 3.2 API keys needed

| Service | Purpose | Where to get |
|---------|---------|--------------|
| Anthropic API | AI theme/geography tagging in `tag_themes.py` | https://console.anthropic.com → API Keys |
| NCBI/PubMed API (optional) | Faster PubMed lookups in `enrich_dois.py` | https://www.ncbi.nlm.nih.gov/account/ |

**Cost:** Theme tagging for ~132 papers costs under $0.10 using Claude Sonnet. Top up $5 at console.anthropic.com — that will last many update cycles.

### 3.3 Python virtual environment (one-time)

macOS uses a Homebrew-managed Python that blocks system-wide pip installs. Use a virtual environment:

```bash
cd /path/to/notes-remote      # vault root
python3 -m venv .venv
source .venv/bin/activate
pip install anthropic
echo ".venv/" >> .gitignore
```

**Every time you open a new terminal session**, reactivate the venv before running scripts:
```bash
source .venv/bin/activate
```

### 3.4 Set your Anthropic API key

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Or add to your shell profile (`~/.zshrc`) to make it permanent:
```bash
echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.zshrc
```

### 3.5 Configure script settings

In `scripts/enrich_dois.py`, set your email near the top:
```python
CROSSREF_MAILTO = "your@email.com"   # gives you CrossRef "polite pool" access
PUBMED_API_KEY  = ""                 # optional, paste NCBI key here if you have one
```

---

## 4. The Four Enrichment Scripts

### Step 1–3: `scripts/enrich_dois.py`

**What it does, in one pass:**

**Step 1 — CrossRef DOI search**
- For each item missing a DOI, queries the CrossRef API (`api.crossref.org`) by title + first author
- Accepts match if CrossRef relevance score ≥ 5.0 AND title word-overlap ≥ 60%
- Writes DOI to `item["DOI"]` and sets `item["URL"]` to `https://doi.org/<DOI>`

**Step 2 — CrossRef full record**
- For each item with a DOI, fetches the full CrossRef record
- Extracts abstract (stripping JATS XML tags) and author-supplied keywords
- Only populates if field is currently empty (never overwrites)

**Step 3 — PubMed lookup**
- For each item with a DOI, queries PubMed eSearch API: DOI → PMID
- Fetches full PubMed XML record: extracts abstract (with section labels), MeSH terms, author keywords
- Stores PMID in `item["PMID"]`
- Abstract falls back to PubMed if CrossRef didn't have one

**URL priority logic:**
1. DOI → `https://doi.org/<DOI>`
2. PMID → `https://pubmed.ncbi.nlm.nih.gov/<PMID>/`
3. Any non-Scholar URL already present
4. Google Scholar URL (last resort fallback)

**Re-run safe:** Items that already have a DOI skip Step 1. Items with an existing abstract skip abstract fetch. Safe to run multiple times.

**Runtime:** ~5–8 minutes for 132 items (rate-limited: 0.5s between CrossRef calls, 0.35s between PubMed calls)

---

### Step 4: `scripts/tag_themes.py`

**What it does:**
- Reads enriched JSON (after `enrich_dois.py`)
- For each publication, sends title + abstract (truncated to 1200 chars) to Claude API
- Claude assigns themes and geography tags from **controlled vocabularies** (see Section 9)
- Only assigns tags that exist exactly in the controlled lists — never invents new ones
- Writes `item["themes"]` and `item["geography"]` back to JSON

**Model:** `claude-sonnet-4-20250514`

**Re-run safe:** Skips items that already have both `themes` and `geography` set. If interrupted (e.g. API credits run out), just top up and re-run — it resumes from where it left off.

**Runtime:** ~2–3 minutes for 132 items

---

### `scripts/zotero_to_obsidian.py`

**What it does:**
- Reads the enriched JSON
- For each item, generates one `.md` file in `publications/`
- Filename format: `YYYY-title-slug-zoteroID.md` (e.g. `2024-health-policy-processes-pop00089.md`)
- Filenames are stable across re-runs (based on Zotero ID + title hash)
- If a file already exists, preserves manually-added content in the body (Notes/Summary section)
- Reads themes/geography/keywords from the JSON (not just from existing .md files)

**Frontmatter written:**
```yaml
---
type: "publication"
title: "..."
year: 2024
pub_type: "journal-article"
venue: "..."
doi: "10.xxxx/..."
url: "https://doi.org/10.xxxx/..."
abstract: "..."
authors:
  - "Prashanth N S"
affiliations:
  - "Institute of Public Health Bengaluru"
themes:
  - "Health systems and policy"
  - "Health equity"
keywords:
  - "..."
projects: []
geography:
  - "Karnataka"
  - "India"
---
```

---

### `scripts/build_pubs_index.py`

**What it does:**
- Scans all `publications/*.md` files
- Extracts YAML frontmatter from each
- Writes:
  - `assets/pubs_index.json` — machine-readable index (used for future dashboards)
  - `_generated/publications/by-year-YYYY.md` — one page per year
  - `_generated/publications/by-theme-index.md` — index of all themes with paper counts
  - `_generated/publications/by-theme-*.md` — one page per theme listing all papers

**The by-theme pages only populate if `themes:` fields are non-empty in the .md files.** This is why `tag_themes.py` must run before `zotero_to_obsidian.py`, and `zotero_to_obsidian.py` must correctly read themes from the JSON (not just from existing .md files).

---

## 5. Full Pipeline: First-Time Run (or Clean Rebuild)

Use this when rebuilding from scratch or after significant changes.

### Step 1 — Export from Zotero

1. Open Zotero
2. Navigate to your publications collection
3. File → Export Collection → Format: **CSL JSON**
4. Save to: `data/zotero_daktre_publications.json` (overwrite existing)

Verify the export:
```bash
python3 - <<'PY'
import json
d = json.load(open("data/zotero_daktre_publications.json"))
print(f"Items exported: {len(d)}")
PY
```

### Step 2 — Activate virtual environment

```bash
cd /path/to/notes-remote
source .venv/bin/activate
```

### Step 3 — Run DOI/PMID/abstract enrichment

```bash
python3 scripts/enrich_dois.py
```

This overwrites `data/zotero_daktre_publications.json` in-place and saves a backup to `data/zotero_daktre_publications_backup.json`.

After it completes, verify:
```bash
python3 - <<'PY'
import json, re
d = json.load(open("data/zotero_daktre_publications.json"))
doi   = sum(1 for x in d if x.get("DOI"))
pmid  = sum(1 for x in d if x.get("PMID"))
abs_  = sum(1 for x in d if x.get("abstract"))
kw    = sum(1 for x in d if x.get("keywords"))
scholar = sum(1 for x in d if "scholar.google" in (x.get("URL") or ""))
print(f"Total: {len(d)} | DOIs: {doi} | PMIDs: {pmid} | Abstracts: {abs_} | Keywords: {kw} | Scholar URLs remaining: {scholar}")
PY
```

### Step 4 — Run AI theme/geography tagging

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 scripts/tag_themes.py
```

After it completes, verify:
```bash
python3 - <<'PY'
import json
d = json.load(open("data/zotero_daktre_publications.json"))
themed = sum(1 for x in d if x.get("themes"))
geo    = sum(1 for x in d if x.get("geography"))
print(f"Items with themes: {themed} | Items with geography: {geo}")
PY
```
Both numbers should equal total item count.

### Step 5 — Clean old generated files

```bash
rm publications/*.md
rm -rf _generated/
```

> **Why delete?** Previous runs may have used slightly different filename schemes, creating duplicates. A clean regeneration guarantees one file per paper with no orphans.

### Step 6 — Generate publication notes

```bash
python3 scripts/zotero_to_obsidian.py
```

Verify a sample file has themes populated:
```bash
head -30 publications/$(ls publications/ | head -1)
```
You should see `themes:` with values, not empty.

### Step 7 — Generate browse pages and index

```bash
python3 scripts/build_pubs_index.py
```

Verify the by-theme index has content:
```bash
wc -l _generated/publications/by-theme-index.md
cat _generated/publications/by-theme-index.md
```
Should show 24+ themes with paper counts.

### Step 8 — Commit and push

```bash
git add -A
git commit -m "Full publication rebuild: $(date '+%Y-%m-%d')"
git push
```

### Step 9 — Publish in Obsidian

1. Open Obsidian Desktop (vault: notes-remote)
2. Click the **paper plane icon** (Publish changes)
3. In the dialog, ensure these are all selected:
   - `publications/` (all .md files) — should show as New or Changed
   - `_generated/publications/` (all browse pages)
   - `assets/pubs_index.json`
   - `3. Resources/Publications.md` (if changed)
4. Also check the **Delete** section — select any stale remote files to remove
5. Click **Publish**

> **Important:** Git push does NOT update Obsidian Publish. You must use the Obsidian UI every time.

---

## 6. Routine Update (New Publications)

When you have one or more new publications to add:

### Step 1 — Add to Zotero and re-export

Add the paper(s) to your Zotero collection, then export:
- File → Export Collection → CSL JSON → `data/zotero_daktre_publications.json`

### Step 2 — Run enrichment (only processes new items)

```bash
cd /path/to/notes-remote
source .venv/bin/activate
export ANTHROPIC_API_KEY=sk-ant-...

python3 scripts/enrich_dois.py    # skips items already enriched
python3 scripts/tag_themes.py     # skips items already tagged
```

### Step 3 — Regenerate and publish

```bash
rm publications/*.md
rm -rf _generated/
python3 scripts/zotero_to_obsidian.py
python3 scripts/build_pubs_index.py
git add -A && git commit -m "Add new publication(s): $(date '+%Y-%m-%d')"
git push
```

Then Publish in Obsidian UI.

**Total time: ~5 minutes** (most of which is the enrichment APIs running).

---

## 7. Obsidian Publish Notes

- **Site ID:** `daktre-notes`
- **Custom domain:** `notes.daktre.com`
- **Git push ≠ Publish.** Always use the Obsidian Publish UI after pushing.
- **Stale files:** If you see old/duplicate content online, check the Delete section in the Publish dialog and remove orphaned files.
- **Rendering:** Obsidian Publish renders entirely client-side in JavaScript. Page content may appear blank in simple web fetches — use a real browser to check.
- **By-theme pages:** These load correctly but the content starts below the fold — scroll down if they appear blank.

**Public URLs:**
- Landing page: `https://notes.daktre.com/3.+Resources/Publications`
- By-theme index: `https://notes.daktre.com/_generated/publications/by-theme-index`
- By-theme page: `https://notes.daktre.com/_generated/publications/by-theme-health-equity` (etc.)
- By-year page: `https://notes.daktre.com/_generated/publications/by-year-2024` (etc.)

---

## 8. Script Reference

### `scripts/enrich_dois.py`

| Config variable | Default | Description |
|----------------|---------|-------------|
| `INPUT_JSON` | `data/zotero_daktre_publications.json` | Input/output path |
| `BACKUP_JSON` | `data/zotero_daktre_publications_backup.json` | Backup created before enrichment |
| `CROSSREF_MAILTO` | `your@email.com` | **Change this.** Your email for CrossRef polite pool |
| `PUBMED_API_KEY` | `""` | Optional NCBI key (raises rate limit 3→10 req/sec) |
| `CROSSREF_SCORE_MIN` | `5.0` | Minimum CrossRef relevance score to accept a DOI match |
| `TITLE_OVERLAP_MIN` | `0.6` | Minimum word-overlap fraction to accept a DOI match |
| `SLEEP_CROSSREF` | `0.5` | Seconds between CrossRef requests |
| `SLEEP_PUBMED` | `0.35` | Seconds between PubMed requests |

**APIs used:**
- `https://api.crossref.org/works?query.title=...&query.author=...` — DOI search
- `https://api.crossref.org/works/<DOI>` — full record (abstract + keywords)
- `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` — DOI→PMID
- `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi` — full PubMed record

**No external packages required** — uses Python 3 stdlib only.

---

### `scripts/tag_themes.py`

| Config variable | Default | Description |
|----------------|---------|-------------|
| `INPUT_JSON` | `data/zotero_daktre_publications.json` | Input/output path |
| `BACKUP_JSON` | `data/zotero_daktre_publications_pretheme_backup.json` | Backup before tagging |
| `MODEL` | `claude-sonnet-4-20250514` | Claude model to use |
| `SLEEP_SEC` | `0.3` | Seconds between API calls |
| `THEMES` | (list of 24) | Controlled vocabulary for themes — edit as needed |
| `GEOGRAPHIES` | (list of 10) | Controlled vocabulary for geography — edit as needed |

**Requires:** `pip install anthropic` and `ANTHROPIC_API_KEY` environment variable.

**Cost:** ~$0.05–0.10 per full run of 132 papers.

---

### `scripts/zotero_to_obsidian.py`

**Key behaviour:**
- Filename: `YYYY-{title-slug}-{zotero-id}.md`
- Long filenames are safely truncated with a stable hash suffix (macOS 255-char limit)
- Reads `themes`, `keywords`, `geography` from JSON item (not just from existing .md)
- Preserves body content (Notes/Summary section) if file already exists
- Affiliations default to `["Institute of Public Health Bengaluru"]` unless manually set in existing .md

---

### `scripts/build_pubs_index.py`

**Outputs:**
- `assets/pubs_index.json` — array of all publications with all metadata fields + `search` blob
- `_generated/publications/by-year-YYYY.md` — listings per year, newest-first
- `_generated/publications/by-theme-index.md` — index with counts per theme
- `_generated/publications/by-theme-{slug}.md` — listings per theme, newest-first

**Note:** By-theme pages are only generated for themes that actually appear in publication frontmatter. If themes are empty, by-theme pages will be empty or missing.

---

## 9. Controlled Vocabularies

These are the exact lists used by `tag_themes.py`. Edit them in the script before running if you want to add/rename/remove categories. **Re-tag after any changes** (delete `themes` and `geography` fields from JSON first, or add new tags manually).

### Themes (24)

```
Health equity
Tribal and Adivasi health
Child health and nutrition
Maternal health
Non-communicable diseases
Infectious and zoonotic diseases
COVID-19
One Health
Health systems and policy
Primary health care
Access to medicines
Capacity building
Universal health coverage
Governance and patient rights
Tobacco control
Mental health
Antimicrobial resistance
Research methods
Biodiversity and ecology
Child development and neurodevelopment
Sickle cell and rare diseases
Gender and social determinants
Community participation
Global health
```

### Geographies (10)

```
Karnataka
Kerala
Tamil Nadu
Assam
South India
India
South Asia
Sub-Saharan Africa
Low- and middle-income countries
Global
```

---

## 10. Troubleshooting

### "themes: []" in generated .md files despite JSON having themes

**Cause:** `zotero_to_obsidian.py` was only reading themes from existing .md files, not from the JSON.

**Fix:** In `scripts/zotero_to_obsidian.py`, ensure these lines read from BOTH sources:
```python
"themes":   manual_fm.get("themes")   or item.get("themes")   or [],
"keywords": manual_fm.get("keywords") or item.get("keywords") or [],
"geography":manual_fm.get("geography")or item.get("geography")or [],
```

---

### by-theme-index is empty or tiny

**Cause:** Either (a) `tag_themes.py` didn't complete, or (b) themes are empty in .md files (see above).

**Fix:**
1. Check JSON: `python3 -c "import json; d=json.load(open('data/zotero_daktre_publications.json')); print(sum(1 for x in d if x.get('themes')), 'items have themes')`
2. If 0 → re-run `tag_themes.py`
3. If >0 → re-run `zotero_to_obsidian.py` and `build_pubs_index.py`

---

### DOI enrichment finds 0 DOIs

**Cause:** CrossRef API is likely unreachable (network restriction in some environments).

**Fix:** Run `enrich_dois.py` on your local machine, not in a sandboxed environment.

**Verify connectivity:** `curl -s "https://api.crossref.org/works?query=test&rows=1" | head -50`

---

### Duplicate .md files in publications/

**Cause:** Previous pipeline runs used a different filename scheme.

**Fix:** `rm publications/*.md && rm -rf _generated/` then regenerate.

---

### "externally-managed-environment" pip error on macOS

**Cause:** macOS Homebrew Python blocks system-wide pip installs.

**Fix:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install anthropic
```

---

### Obsidian Publish shows old/stale content after push

**Cause:** Git push doesn't update Obsidian Publish.

**Fix:** Open Obsidian → Publish changes → check the **Delete** section for stale files → Publish.

---

### tag_themes.py fails with "credit balance too low"

**Fix:** Top up at https://console.anthropic.com → Billing. Then re-run — the script skips already-tagged items.

---

### By-theme page content appears blank in browser

**Cause:** Obsidian Publish renders content client-side. Content exists but starts below viewport.

**Fix:** Scroll down. This is normal behaviour — the heading and content are below the fold on initial load.

---

## 11. Architecture Decisions & History

### Why CSL JSON export (not BibTeX)?

Early experiments used BibTeX and Better BibTeX. CSL JSON was chosen because it maps cleanly to the frontmatter fields needed and is natively supported by Zotero without plugins.

### Why not use Zotero plugins for DOI enrichment?

The Zotero DOI Manager plugin (the natural choice) is incompatible with Zotero 8. Rather than wait for plugin updates, the enrichment was moved to standalone Python scripts (`enrich_dois.py`) that call CrossRef and PubMed APIs directly. This is more reliable, auditable, and version-independent.

### Why CrossRef + PubMed (two APIs)?

- **CrossRef** has the widest DOI coverage for journal articles and often has abstracts
- **PubMed** is essential for public health literature specifically — it has structured abstracts, MeSH terms, and PMIDs that CrossRef lacks
- Together they cover ~85–90% of a typical public health publication list

### Why Claude API for theme tagging (not rule-based)?

A rule-based keyword matcher would require extensive manual mapping and would fail on paraphrased titles. Claude can infer themes from context, handle non-English concepts (Adivasi, One Health, etc.), and assign multiple overlapping themes correctly. The controlled vocabulary constraint ensures consistency.

### Why Obsidian Publish (not a custom site)?

The vault already uses Obsidian for note-taking. Obsidian Publish allows the same files to serve as both a private working space and a public site, with zero additional infrastructure. The tradeoff is that publishing requires the Obsidian desktop app — it cannot be automated via CI/CD.

### The Google Scholar URL problem (original issue)

The original Zotero export generated Google Scholar citation URLs for all 132 items because:
1. Papers were imported into Zotero via Google Scholar (not via DOI or PubMed)
2. Zotero stored the Scholar URL as the primary URL
3. The export script faithfully copied that URL to the published site

The fix was `enrich_dois.py`, which looks up proper DOIs from CrossRef and replaces Scholar URLs with `https://doi.org/` links.

---

*Last updated: 2026-03 · Pipeline built with assistance from Claude
