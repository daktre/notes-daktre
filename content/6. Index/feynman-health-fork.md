---
title: "feynman-health: forking an AI research agent for public health and HPSR"
date: 2026-04-01
tags:
  - tools
  - ai-research
  - hpsr
  - open-source
  - project
status: seedling
related:
  - "[[AI tools for public health research]]"
  - "[[Health policy and systems research]]"
---
# feynman-health: forking an AI research agent for public health and HPSR

**feynman-health-skills is now live.** Skills for [PubMed](https://claude.ai/chat/pubmed-research.skill) and [HPSR epistemology](https://claude.ai/chat/hpsr-epistemology.skill) are ready to install. See [the GitHub repo](https://github.com/daktre/feynman-health-skills) for installation and usage.

This started as a fork experiment. It's become a working tool. HPSR researchers: try it and report back.

---

## The problem

[Feynman](https://github.com/getcompanion-ai/feynman) is am AI research agent: searches, reads, synthesises, drafts. But its  source layer runs through [AlphaXiv](https://www.alphaxiv.org/) (arXiv, basically). So it knows comp sci, physics, quantitative biology. It does not know whether PubMed exists.

For people doing health policy and systems research, epidemiology, qualitative work, this is unusable. The skills here fix that.

---

## What I built

### Two skills, tested and ready

**`pubmed-research.skill`** — Tells Feynman to query PubMed first. Teaches MeSH term logic, study design appraisal, LMIC relevance weighting.

Test run: [ASHA programme effectiveness](https://notes.daktre.com/6.-Index/Effectiveness-of-India's-ASHA-Programme) — pulled 19 sources (all appropriate: PubMed/PMC/grey, zero arXiv), correctly separated pilot evidence from routine programme findings. [Provenance record](https://notes.daktre.com/6.-Index/Provenance-Record-for-ASHA-Programme-Effectiveness-India) archived.

**`hpsr-epistemology.skill`** — Encodes that qualitative studies, mixed-methods designs, implementation science papers are first-class evidence. Grey literature (WHO, government docs, NHSRC) is primary, not supplementary. Context-sensitivity is a feature.

### What's NOT  ready (yet)

- **Subscription databases** (Embase, Web of Science, CINAHL, Ovid MEDLINE) — out of scope. Free APIs only.
- **PubMed CLI connector** — this is the next big ask. Feynman ships with `alpha` for AlphaXiv; we need the equivalent for PubMed. Needs a developer.
- **New workflows** (`/sysrev`, `/policybrief`, `/appraise`) — code work, separate from skills.

---

## Install and use

Clone the repo and copy skill files into Feynman's skills directory:

```bash
git clone https://github.com/daktre/feynman-health-skills.git
cp feynman-health-skills/*.skill ~/.feynman/agent/skills/
```

Then run Feynman as usual. Skills auto-activate for relevant queries.

```bash
feynman lit "your research question"
feynman deepresearch "your topic"
```

Full details: [GitHub README](https://github.com/daktre/feynman-health-skills).

---

## Roadmap

### Short-term (planned skills)

- `grey-literature.skill` — explicitly prioritise WHO IRIS, MoHFW, NHSRC, NFHS, parliamentary reports
- `reviewer-appraisal.skill` — CASP checklists, Cochrane risk-of-bias, GRADE framing

### Medium-term (needs developer)

- **PubMed CLI connector** — wraps NCBI E-utilities. This unblocks everything.
- WHO IRIS connector (OAI-PMH)
- Cochrane REST API wrapper

### Longer-term

- Local document ingestion (curated Indian health policy materials)
- New workflows

---

## For HPSR researchers

Won't replace protocol-driven systematic reviews (you need Embase, Web of Science, proper screening: use Covidence or Rayyan). But useful for:

- Rapid evidence reviews
- Scoping review preliminary searches
- Grant background sections
- Understanding what's published on a health systems topic
- Separating pilot/special intervention evidence from routine programme findings

---

## Feedback wanted

**From HPSR practitioners:** Does this help? What's missing? What's wrong?

**From developers:** PubMed CLI — interested?

GitHub: [daktre/feynman-health-skills](https://github.com/daktre/feynman-health-skills)

Email: hello@daktre.com

---

## Affiliation

Built at [IPH Bengaluru](https://iph.org.in/) as part of broader work on AI tooling for health systems research.

## See also

- [GitHub repo](https://github.com/daktre/feynman-health-skills)
- [Original Feynman](https://github.com/getcompanion-ai/feynman)
- [ASHA test run](https://notes.daktre.com/6.-Index/Effectiveness-of-India's-ASHA-Programme)
- [Original planning notes](https://claude.ai/chat/a02e1fa5-0376-464b-9197-593fc7890df0#original-planning-below)

---

## Original planning (archived for reference)

The thinking behind this fork, kept here for context and traceability.

### The fork approach

Feynman's agent behaviour runs on skills — Markdown instruction files in `~/.feynman/agent/skills/`. This makes it fork-friendly without touching TypeScript.

The harder part is source access. AlphaXiv gives full-text access, citation chains, Q&A on papers. We need to rebuild that pointing at PubMed, WHO IRIS, Cochrane.

### Planned skills (original list)

A **`grey-literature.md`** skill telling the Researcher to treat WHO reports, MoHFW documents, NHSRC publications, state NHP materials, parliamentary standing committee reports, IIPS data as primary sources.

A **`reviewer-appraisal.md`** skill that replaces default peer review criteria with CASP checklists for qualitative work, Cochrane risk-of-bias logic for trials, and GRADE framing for evidence synthesis.

A **`policy-writer.md`** skill teaching the Writer agent what a policy brief looks like, how a rapid evidence review is structured, how HPSR synthesis papers differ from standard journal articles.

### Planned workflows (original list)

`/sysrev` for systematic review support — PICO formulation, PRISMA-compatible search string generation for PubMed and Cochrane, deduplication, PRISMA flow outline.

`/policybrief` to synthesise evidence into a structured brief — problem statement, evidence summary, policy options, implementation considerations.

`/appraise` applying CASP, GRADE, or ROBINS-I to a supplied document.

`/burden` to aggregate epidemiological data from GBD, NFHS, DLHS, and state health bulletins.

`/greylit` explicitly instructing the Researcher to prioritise institutional and government sources.

`/watch` (already exists) — monitoring new WHO guideline updates, Lancet publications on a topic, MoHFW policy notifications.

### Source connectors (original spec)

The key connector is a `pubmed` CLI tool wrapping NCBI's E-utilities (esearch + efetch). Needs to: search by keyword, MeSH term, date range; retrieve full metadata; pull abstracts and PMIDs.

After that: WHO IRIS connector (OAI-PMH), Cochrane REST API for abstracts and Plain Language Summaries, curated India-specific URL corpus (NFHS, HMIS, NHSRC, MoHFW).

For India-specific content, the realistic approach is a curated URL list that the web search agent is explicitly instructed to prioritise: NFHS, HMIS, NHSRC reports, NITI Aayog health chapters, SRS data. Plus a local PDF ingestion path for frequently-used institutional documents.

Last updated: 2026-04-18 12:34