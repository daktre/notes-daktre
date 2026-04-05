#!/usr/bin/env python3
"""
Zotero Publication Enrichment Script  (Steps 1–3)
===================================================
For each item in your Zotero export JSON, this script:

  Step 1 — CrossRef search   : find missing DOIs by title + author
  Step 2 — CrossRef full fetch: get abstract + author keywords from DOI
  Step 3 — PubMed fetch       : get PMID, MeSH keywords, abstract fallback

Run from your vault root (same folder as data/ and scripts/):

    python3 enrich_dois.py

Input:  data/zotero_daktre_publications.json
Output: data/zotero_daktre_publications.json   (enriched, in-place)
        data/zotero_daktre_publications_backup.json  (original, kept safe)

Requirements: Python 3 stdlib only — no pip installs needed.
"""

import json
import time
import re
import shutil
import sys
import xml.etree.ElementTree as ET
import urllib.parse
import urllib.request
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
INPUT_JSON  = Path("data/zotero_daktre_publications.json")
BACKUP_JSON = Path("data/zotero_daktre_publications_backup.json")
OUTPUT_JSON = INPUT_JSON   # overwrite in-place

# Your email — CrossRef gives you "polite pool" (higher rate) when identified
CROSSREF_MAILTO = "prashanth.ns@gmail.com"

# NCBI/PubMed API key (optional but raises rate limit from 3→10 req/sec)
# Get one free at: https://www.ncbi.nlm.nih.gov/account/
PUBMED_API_KEY = "b4ededf66386d4fd5beab274ca0ca34d6809"   # leave empty if you don't have one

# Tuning
CROSSREF_SCORE_MIN   = 5.0   # minimum CrossRef relevance score to accept
TITLE_OVERLAP_MIN    = 0.6   # minimum word-overlap fraction to accept match
SLEEP_CROSSREF       = 0.5   # seconds between CrossRef requests
SLEEP_PUBMED         = 0.35  # seconds between PubMed requests (safe for 3/sec)
# ────────────────────────────────────────────────────────────────────────────

STOPWORDS = {
    "a","an","the","of","in","and","for","to","with","on","from","by","at",
    "is","are","was","were","be","been","as","its","it","this","that","their",
    "which","into","or","but","not","than","more","also","between","among",
    "using","based","study","evidence","india","indian","health"
}

# ── Helpers ──────────────────────────────────────────────────────────────────

def title_words(t):
    return set(re.findall(r'\w+', t.lower())) - STOPWORDS

def safe_get(url, timeout=12):
    """GET a URL, return decoded text or None on error."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "ZoteroEnrich/2.0 (mailto:" + CROSSREF_MAILTO + ")"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"        ⚠  HTTP error: {e}")
        return None

def build_best_url(item):
    doi  = item.get("DOI")
    pmid = item.get("PMID")
    url  = item.get("URL", "")
    if doi:
        return f"https://doi.org/{doi}"
    if pmid:
        return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    return url

# ── Step 1: CrossRef search for DOI ──────────────────────────────────────────

def crossref_search_doi(title, authors):
    """Search CrossRef by title+author. Returns DOI string or None."""
    first_author = next((a["family"] for a in authors if a.get("family")), "")
    params = urllib.parse.urlencode({
        "query.title":  title,
        "query.author": first_author,
        "rows": 3,
        "select": "DOI,title,score",
        "mailto": CROSSREF_MAILTO,
    })
    raw = safe_get(f"https://api.crossref.org/works?{params}")
    if not raw:
        return None
    try:
        items = json.loads(raw).get("message", {}).get("items", [])
    except Exception:
        return None
    if not items:
        return None

    top = items[0]
    score    = top.get("score", 0)
    cr_title = " ".join(top.get("title", [""])).lower()
    our_w    = title_words(title)
    cr_w     = title_words(cr_title)
    overlap  = len(our_w & cr_w) / len(our_w) if our_w else 0

    if score >= CROSSREF_SCORE_MIN and overlap >= TITLE_OVERLAP_MIN:
        return top.get("DOI")
    return None

# ── Step 2: CrossRef full record for abstract + keywords ─────────────────────

def crossref_fetch_details(doi):
    """
    Fetch full CrossRef record by DOI.
    Returns dict with keys: abstract (str), keywords (list)
    """
    result = {"abstract": "", "keywords": []}
    encoded = urllib.parse.quote(doi, safe="")
    raw = safe_get(f"https://api.crossref.org/works/{encoded}?mailto={CROSSREF_MAILTO}")
    if not raw:
        return result
    try:
        msg = json.loads(raw).get("message", {})
    except Exception:
        return result

    # Abstract — CrossRef sometimes wraps it in JATS XML tags
    abstract = msg.get("abstract", "")
    if abstract:
        abstract = re.sub(r'<[^>]+>', ' ', abstract).strip()
        abstract = re.sub(r'\s+', ' ', abstract)
        result["abstract"] = abstract

    # Keywords: CrossRef "subject" and "keyword" fields
    kws = msg.get("subject", []) + msg.get("keyword", [])
    result["keywords"] = [k.strip() for k in kws if k.strip()]

    return result

# ── Step 3: PubMed fetch for PMID + abstract fallback + MeSH terms ───────────

def pubmed_fetch(doi):
    """
    Look up a DOI in PubMed.
    Returns dict with: pmid (str), abstract (str), mesh_terms (list)
    """
    result = {"pmid": "", "abstract": "", "mesh_terms": []}

    api_key_param = f"&api_key={PUBMED_API_KEY}" if PUBMED_API_KEY else ""

    # 3a. DOI → PMID via esearch
    doi_encoded = urllib.parse.quote(doi, safe="")
    search_url = (
        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        f"?db=pubmed&term={doi_encoded}[doi]&retmode=json{api_key_param}"
    )
    raw = safe_get(search_url)
    time.sleep(SLEEP_PUBMED)
    if not raw:
        return result

    try:
        ids = json.loads(raw).get("esearchresult", {}).get("idlist", [])
    except Exception:
        return result
    if not ids:
        return result

    pmid = ids[0]
    result["pmid"] = pmid

    # 3b. Fetch full XML record by PMID for abstract + MeSH + author keywords
    fetch_url = (
        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        f"?db=pubmed&id={pmid}&rettype=abstract&retmode=xml{api_key_param}"
    )
    raw_xml = safe_get(fetch_url)
    time.sleep(SLEEP_PUBMED)
    if not raw_xml:
        return result

    try:
        root = ET.fromstring(raw_xml)
    except ET.ParseError:
        return result

    # Abstract (may have labelled sections e.g. BACKGROUND, METHODS)
    abstract_parts = []
    for ab in root.iter("AbstractText"):
        label = ab.get("Label", "")
        text  = (ab.text or "").strip()
        if text:
            abstract_parts.append(f"{label}: {text}" if label else text)
    result["abstract"] = " ".join(abstract_parts)

    # MeSH descriptor names
    mesh = []
    for mh in root.iter("MeshHeading"):
        desc = mh.find("DescriptorName")
        if desc is not None and desc.text:
            mesh.append(desc.text.strip())

    # Author-supplied keywords (KeywordList)
    for kw in root.iter("Keyword"):
        if kw.text:
            mesh.append(kw.text.strip())

    result["mesh_terms"] = list(dict.fromkeys(mesh))  # deduplicate, preserve order

    return result

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if not INPUT_JSON.exists():
        print(f"ERROR: {INPUT_JSON} not found.")
        print("Run this script from your vault root (same folder as 'data/').")
        sys.exit(1)

    # Safety backup
    shutil.copy(INPUT_JSON, BACKUP_JSON)
    print(f"✓ Backup saved → {BACKUP_JSON}")

    data = json.loads(INPUT_JSON.read_text(encoding="utf-8"))
    n    = len(data)
    print(f"✓ Loaded {n} items\n")

    stats = {
        "doi_already": 0, "doi_found": 0, "doi_missing": 0,
        "abstract_found": 0, "pmid_found": 0, "mesh_found": 0
    }

    for i, item in enumerate(data, 1):
        title   = item.get("title", "").strip()
        authors = item.get("author", [])
        prefix  = f"[{i:3}/{n}]"

        if not title:
            print(f"{prefix} — skipping (no title): {item.get('id')}")
            continue

        print(f"{prefix} {title[:70]}")

        # ── Step 1: Resolve DOI ──────────────────────────────────────────────
        doi = item.get("DOI") or item.get("doi")
        if doi:
            stats["doi_already"] += 1
            print(f"         DOI: {doi}  (already present)")
        else:
            doi = crossref_search_doi(title, authors)
            time.sleep(SLEEP_CROSSREF)
            if doi:
                item["DOI"] = doi
                stats["doi_found"] += 1
                print(f"         DOI: {doi}  ✓ found via CrossRef")
            else:
                stats["doi_missing"] += 1
                print(f"         DOI: not found")

        # ── Step 2: CrossRef full details (abstract + keywords) ──────────────
        if doi:
            details = crossref_fetch_details(doi)
            time.sleep(SLEEP_CROSSREF)

            if details["abstract"] and not item.get("abstract"):
                item["abstract"] = details["abstract"]
                stats["abstract_found"] += 1
                print(f"         Abstract: ✓ ({len(details['abstract'])} chars, CrossRef)")

            if details["keywords"]:
                existing = item.get("keywords", [])
                item["keywords"] = list(dict.fromkeys(existing + details["keywords"]))
                print(f"         Keywords: {', '.join(details['keywords'][:5])}")

        # ── Step 3: PubMed (PMID + abstract fallback + MeSH) ────────────────
        if doi:
            pm = pubmed_fetch(doi)

            if pm["pmid"] and not item.get("PMID"):
                item["PMID"] = pm["pmid"]
                stats["pmid_found"] += 1
                print(f"         PMID: {pm['pmid']}  ✓ found via PubMed")

            if pm["abstract"] and not item.get("abstract"):
                item["abstract"] = pm["abstract"]
                stats["abstract_found"] += 1
                print(f"         Abstract: ✓ ({len(pm['abstract'])} chars, PubMed fallback)")

            if pm["mesh_terms"]:
                existing = item.get("keywords", [])
                item["keywords"] = list(dict.fromkeys(existing + pm["mesh_terms"]))
                stats["mesh_found"] += 1
                print(f"         MeSH: {', '.join(pm['mesh_terms'][:4])}")

        # ── Set best URL ─────────────────────────────────────────────────────
        item["URL"] = build_best_url(item)
        print()

    # ── Save enriched JSON ───────────────────────────────────────────────────
    OUTPUT_JSON.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"""
{'='*65}
 Enrichment Summary
{'='*65}
 DOIs already present : {stats['doi_already']}
 DOIs found (CrossRef): {stats['doi_found']}
 DOIs not found       : {stats['doi_missing']}
 Abstracts populated  : {stats['abstract_found']}
 PMIDs found (PubMed) : {stats['pmid_found']}
 MeSH/keyword sets    : {stats['mesh_found']}
 Total items          : {n}
{'='*65}

 Saved enriched JSON → {OUTPUT_JSON}

 Next steps:
   rm publications/*.md
   rm -rf _generated/
   python3 scripts/zotero_to_obsidian.py
   python3 scripts/build_pubs_index.py
   git add -A && git commit -m "Enrich publications: DOI, PMID, abstract, keywords"
   git push
   (then Publish changes in Obsidian UI)
""")

if __name__ == "__main__":
    main()
