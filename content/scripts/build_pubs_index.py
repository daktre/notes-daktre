#!/usr/bin/env python3
"""
Build a JSON index of publications for Obsidian Publish.

- Scans ./publications/**/*.md
- Reads YAML frontmatter
- Writes ./assets/pubs_index.json
- Optionally writes browse pages to ./_generated/publications/
"""

from __future__ import annotations
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VAULT_ROOT = Path(__file__).resolve().parents[1]
PUB_DIR = VAULT_ROOT / "publications"
ASSETS_DIR = VAULT_ROOT / "assets"
OUT_JSON = ASSETS_DIR / "pubs_index.json"
GEN_DIR = VAULT_ROOT / "_generated" / "publications"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

def _safe_list(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i).strip() for i in x if str(i).strip()]
    if isinstance(x, str):
        # allow comma-separated
        parts = [p.strip() for p in x.split(",")]
        return [p for p in parts if p]
    return [str(x).strip()] if str(x).strip() else []

def _safe_int(x: Any) -> Optional[int]:
    if x is None:
        return None
    try:
        return int(str(x).strip())
    except Exception:
        return None

def _slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s or "untitled"

def parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    raw = m.group(1)
    body = text[m.end():]

    # Minimal YAML parser (enough for simple frontmatter).
    # For full YAML, install pyyaml and replace this with yaml.safe_load(raw).
    fm: Dict[str, Any] = {}
    current_key = None
    for line in raw.splitlines():
        if not line.strip():
            continue
        if re.match(r"^\s*-\s+", line) and current_key:
            fm.setdefault(current_key, [])
            fm[current_key].append(line.split("-", 1)[1].strip().strip('"').strip("'"))
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip()
            current_key = k
            if v == "":
                fm[k] = []
            else:
                # strip quotes
                v2 = v.strip().strip('"').strip("'")
                # basic list inline: [a, b]
                if v2.startswith("[") and v2.endswith("]"):
                    inner = v2[1:-1].strip()
                    fm[k] = [p.strip().strip('"').strip("'") for p in inner.split(",") if p.strip()]
                else:
                    fm[k] = v2
    return fm, body

def build_record(note_path: Path) -> Optional[Dict[str, Any]]:
    text = note_path.read_text(encoding="utf-8", errors="ignore")
    fm, body = parse_frontmatter(text)

    if str(fm.get("type", "")).strip().lower() != "publication":
        # allow notes without type, but only if they are in publications/ and have a year/title
        pass

    title = str(fm.get("title") or note_path.stem).strip()
    year = _safe_int(fm.get("year"))
    pub_type = str(fm.get("pub_type") or "").strip()

    if not title:
        return None

    slug = _slugify(f"{year or 'na'}-{title}")
    rel_path = note_path.relative_to(VAULT_ROOT).as_posix()
    link = rel_path  # Obsidian Publish internal link uses path

    authors = _safe_list(fm.get("authors"))
    themes = _safe_list(fm.get("themes"))
    keywords = _safe_list(fm.get("keywords"))
    projects = _safe_list(fm.get("projects"))
    geography = _safe_list(fm.get("geography"))
    affiliations = _safe_list(fm.get("affiliations"))

    doi = str(fm.get("doi") or "").strip()
    url = str(fm.get("url") or "").strip()
    venue = str(fm.get("venue") or "").strip()
    abstract = str(fm.get("abstract") or "").strip()

    # searchable text blob (title + authors + venue + keywords + abstract)
    haystack = " | ".join(
        [title, venue, " ".join(authors), " ".join(themes), " ".join(keywords), abstract]
    ).lower()

    rec = {
        "id": doi if doi else slug,
        "title": title,
        "year": year,
        "pub_type": pub_type,
        "authors": authors,
        "venue": venue,
        "doi": doi,
        "url": url,
        "themes": themes,
        "keywords": keywords,
        "projects": projects,
        "geography": geography,
        "affiliations": affiliations,
        "abstract": abstract,
        "path": rel_path,
        "link": link,
        "search": haystack,
    }
    return rec

def write_browse_pages(pubs: List[Dict[str, Any]]) -> None:
    GEN_DIR.mkdir(parents=True, exist_ok=True)

    # By year
    by_year: Dict[int, List[Dict[str, Any]]] = {}
    for p in pubs:
        if p.get("year"):
            by_year.setdefault(int(p["year"]), []).append(p)
    for y in sorted(by_year.keys(), reverse=True):
        items = sorted(by_year[y], key=lambda r: (r.get("title") or "").lower())
        md = [f"# Publications — {y}", ""]
        for r in items:
            md.append(f"- [[{r['path']}|{r['title']}]] — *{r.get('venue','')}*")
        (GEN_DIR / f"by-year-{y}.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    # By theme
    by_theme: Dict[str, List[Dict[str, Any]]] = {}
    for p in pubs:
        for t in p.get("themes") or []:
            by_theme.setdefault(t, []).append(p)
    # index page
    idx = ["# Publications — by theme", ""]
    for t in sorted(by_theme.keys(), key=lambda s: s.lower()):
        tslug = _slugify(t)
        idx.append(f"- [[_generated/publications/by-theme-{tslug}.md|{t}]] ({len(by_theme[t])})")
    (GEN_DIR / "by-theme-index.md").write_text("\n".join(idx) + "\n", encoding="utf-8")

    for t in sorted(by_theme.keys(), key=lambda s: s.lower()):
        tslug = _slugify(t)
        items = sorted(by_theme[t], key=lambda r: (r.get("year") or 0, (r.get("title") or "").lower()), reverse=True)
        md = [f"# Publications — {t}", ""]
        for r in items:
            y = r.get("year") or ""
            md.append(f"- {y} — [[{r['path']}|{r['title']}]] — *{r.get('venue','')}*")
        (GEN_DIR / f"by-theme-{tslug}.md").write_text("\n".join(md) + "\n", encoding="utf-8")

def main() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    pubs: List[Dict[str, Any]] = []

    for md in sorted(PUB_DIR.rglob("*.md")):
        rec = build_record(md)
        if rec:
            pubs.append(rec)

    # sort newest first
    pubs.sort(key=lambda r: (r.get("year") or 0, (r.get("title") or "").lower()), reverse=True)

    OUT_JSON.write_text(json.dumps(pubs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_JSON} with {len(pubs)} records")

    # also write browse pages
    write_browse_pages(pubs)
    print(f"Wrote browse pages under {GEN_DIR}")

if __name__ == "__main__":
    main()
