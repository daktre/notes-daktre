#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VAULT = Path(__file__).resolve().parents[1]
INFILE = VAULT / "data" / "zotero_daktre_publications.json"
OUTDIR = VAULT / "publications"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    return s.strip("-") or "untitled"


MAX_STEM = 120  # keep filenames comfortably below macOS limits

def safe_stem(stem: str, key: str) -> str:
    """
    Ensure filename stem isn't too long by truncating and appending a stable hash.
    `key` should be stable (e.g., doi|year|title) so re-runs map to the same file.
    """
    stem = re.sub(r"\s+", "-", stem.strip())
    stem = re.sub(r"[^\w\-\.]", "", stem)
    if len(stem) <= MAX_STEM:
        return stem
    h = hashlib.sha1(key.encode("utf-8")).hexdigest()[:8]
    return f"{stem[:MAX_STEM-9]}-{h}"

def pick_year(item: Dict[str, Any]) -> Optional[int]:
    """Extract publication year from CSL/Better CSL JSON.

    Handles years encoded as int or as strings (e.g., "2010") in date-parts,
    and falls back to several common CSL date fields.
    """
    issued = item.get("issued") or {}
    parts = issued.get("date-parts") or []
    if parts and parts[0] and parts[0][0] is not None:
        y = parts[0][0]
        if isinstance(y, int):
            return y
        if isinstance(y, str):
            m = re.search(r"(19|20)\d{2}", y)
            if m:
                return int(m.group(0))

    raw = issued.get("raw")
    if raw:
        m = re.search(r"(19|20)\d{2}", str(raw))
        if m:
            return int(m.group(0))

    # Additional CSL fallbacks sometimes present in exports
    for k in ("published", "original-date", "event-date", "date", "issued-online", "published-online"):
        v = item.get(k)
        if isinstance(v, dict):
            dp = v.get("date-parts") or []
            if dp and dp[0] and dp[0][0]:
                y = dp[0][0]
                if isinstance(y, int):
                    return y
                if isinstance(y, str):
                    m = re.search(r"(19|20)\d{2}", y)
                    if m:
                        return int(m.group(0))
            raw2 = v.get("raw")
            if raw2:
                m = re.search(r"(19|20)\d{2}", str(raw2))
                if m:
                    return int(m.group(0))
        elif isinstance(v, str):
            m = re.search(r"(19|20)\d{2}", v)
            if m:
                return int(m.group(0))

    return None

def authors_list(item: Dict[str, Any]) -> List[str]:
    out = []
    for a in item.get("author", []) or []:
        family = (a.get("family") or "").strip()
        given = (a.get("given") or "").strip()
        name = " ".join([given, family]).strip() or a.get("literal") or ""
        if name:
            out.append(name)
    return out

def guess_pub_type(csl_type: str) -> str:
    t = (csl_type or "").lower()
    mapping = {
        "article-journal": "journal-article",
        "paper-conference": "presentation",
        "report": "report",
        "chapter": "chapter",
        "book": "book",
        "thesis": "thesis",
        "manuscript": "preprint",
    }
    return mapping.get(t, t or "journal-article")

def doi_url(item: Dict[str, Any]) -> Tuple[str, str]:
    doi = (item.get("DOI") or item.get("doi") or "").strip()
    url = (item.get("URL") or item.get("url") or "").strip()
    if doi and not url:
        url = f"https://doi.org/{doi}"
    return doi, url

def venue(item: Dict[str, Any]) -> str:
    return (item.get("container-title") or item.get("publisher") or "").strip()

def abstract(item: Dict[str, Any]) -> str:
    # Zotero CSL JSON often stores abstract in "abstract"
    return (item.get("abstract") or "").strip()

def existing_frontmatter(md_text: str) -> Dict[str, Any]:
    m = FRONTMATTER_RE.match(md_text)
    if not m:
        return {}
    raw = m.group(1)
    fm: Dict[str, Any] = {}
    key = None
    for line in raw.splitlines():
        if not line.strip():
            continue
        if re.match(r"^\s*-\s+", line) and key:
            fm.setdefault(key, [])
            fm[key].append(line.split("-", 1)[1].strip().strip('"').strip("'"))
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip()
            key = k
            if v == "":
                fm[k] = []
            else:
                v2 = v.strip().strip('"').strip("'")
                if v2.startswith("[") and v2.endswith("]"):
                    inner = v2[1:-1].strip()
                    fm[k] = [p.strip().strip('"').strip("'") for p in inner.split(",") if p.strip()]
                else:
                    fm[k] = v2
    return fm

def render_frontmatter(fm: Dict[str, Any]) -> str:
    def render_list(k: str) -> str:
        vals = fm.get(k) or []
        if not isinstance(vals, list):
            vals = [str(vals)]
        lines = [f"{k}:"]
        for v in vals:
            lines.append(f'  - "{str(v).replace(chr(34), "")}"')
        return "\n".join(lines)

    # keys in order
    keys_scalar = ["type", "title", "year", "pub_type", "venue", "doi", "url", "abstract"]
    keys_list = ["authors", "affiliations", "themes", "keywords", "projects", "geography"]

    lines = ["---"]
    for k in keys_scalar:
        if k in fm and fm[k] not in (None, ""):
            if k == "year":
                lines.append(f"{k}: {fm[k]}")
            else:
                lines.append(f'{k}: "{str(fm[k]).replace(chr(34), "")}"')
        elif k == "year":
            lines.append("year: ")
        elif k in ["doi", "url", "venue", "abstract"]:
            lines.append(f"{k}: \"\"")
    for k in keys_list:
        lines.append(render_list(k))
    lines.append("---")
    return "\n".join(lines)

def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    data = json.loads(INFILE.read_text(encoding="utf-8"))

    if not isinstance(data, list) or not data:
        raise SystemExit(f"No items found in {INFILE}")

    for item in data:
        title = (item.get("title") or "Untitled").strip()
        year = pick_year(item)
        pub_type = guess_pub_type(item.get("type", ""))
        authors = authors_list(item)
        doi, url = doi_url(item)
        zid = str(item.get("id") or "").strip()
        ven = venue(item)
        abs_ = abstract(item)

        # Use DOI if present to make stable filenames; else use year+title slug
        stem_title = slugify(title)
        stem_year = str(year) if year else "na"

        # Human-readable, stable, and unique: year + title + Zotero id
        if zid:
            base = f"{stem_year}-{stem_title}-{zid}"
        else:
            base = f"{stem_year}-{stem_title}"

        base = safe_stem(base, key=f"{doi}|{zid}|{year}|{title}")
        fname = f"{base}.md"
        outpath = OUTDIR / fname

        # If file exists, preserve manual fields like themes/projects/summary if you already added them
        manual_fm: Dict[str, Any] = {}
        manual_body: str = ""
        if outpath.exists():
            txt = outpath.read_text(encoding="utf-8", errors="ignore")
            manual_fm = existing_frontmatter(txt)
            # keep everything after frontmatter as body
            m = FRONTMATTER_RE.match(txt)
            manual_body = txt[m.end():] if m else txt

        fm = {
            "type": "publication",
            "title": title,
            "year": year or "",
            "pub_type": pub_type,
            "authors": authors,
            "affiliations": manual_fm.get("affiliations") or ["Institute of Public Health Bengaluru"],
            "venue": ven,
            "doi": doi,
            "url": url,
            "themes": manual_fm.get("themes") or item.get("themes") or [],
            "keywords": manual_fm.get("keywords") or item.get("keywords") or [],
            "projects": manual_fm.get("projects") or [],
            "geography": manual_fm.get("geography") or item.get("geography") or [],
            "abstract": abs_,
        }

        header = render_frontmatter(fm)

        # Default body if new file
        if not manual_body.strip():
            manual_body = f'\n\n# {title}\n\n**DOI/Link:** {url or ""}\n\n## Notes / Summary\n'

        outpath.write_text(header + "\n" + manual_body.lstrip(), encoding="utf-8")
        print(f"Wrote: {outpath.relative_to(VAULT)}")

if __name__ == "__main__":
    main()