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
[Feynman](https://github.com/getcompanion-ai/feynman) is an open-source AI research agent. It's a CLI tool that (claims to) does literature reviews, deep research briefs, simulated peer review, and paper drafting.  The problem for me is that its entire academic source layer runs through [AlphaXiv](https://www.alphaxiv.org), which is basically a smart interface on top of [arXiv](arxiv.org). So it covers comp sci, physics, maths, quant bio and such. It does not perhaps even know whether PubMed exists.

For people working in public health, [[Health policy and systems research|HPSR]], epidemiology, health systems, or anything qual/soc-sci types, this is not use-able. The tool also has a bunch of workflows (GPU experiment replication, paper-vs-codebase audits) that are completely irrelevant to public health work. So the question is: what would it take to fork this and make it useful for public health folks?

Feynman's agent behaviour runs on "skills" which are basically Markdown instruction files sitting in `~/.feynman/agent/skills/`. When the researcher agent decides how to search, what to prioritise, how to evaluate sources, all of that stuff lives in files we can rewrite. 

The harder part is the source layer itself, which requires building new CLI tool integrations pointing at the right databases. AlphaXiv gives Feynman full-text paper access, citation chains, and Q&A on specific papers, all of that has to be rebuilt pointing at the right databases. But the APIs we need (PubMed E-utilities, WHO IRIS) are free and well-documented. A non-developer like me can edit skills as needed. Might need bit of help from developer to build the source connectors. 

###  Editing the skills 

Two skills writtn in April 2026 and now installed and tested. Both are Markdown instruction files that live in `~/.feynman/agent/skills/` and change how the Researcher agent thinks and searches.

**`pubmed-research`** redirects the agent's source priority away from AlphaXiv/arXiv entirely. It gets the agent to query PubMed first using MeSH terms rather than free-text keyword guessing, how to construct NCBI E-utilities API calls, how to reach Cochrane and medRxiv, and critically how to evaluate study quality by design rather than by citation count. It also flags the geographic relevance problem: don't over-weight high-income country evidence for LMIC questions.

**`hpsr-epistemology`** is probably the more original contribution. It teaches the agent an entirely different epistemological framework: that qualitative evidence is good not fallback; that grey literature (WHO reports, MoHFW documents, NHSRC publications, parliamentary standing committee reports) is primary evidence as well; that implementation questions need CASP/GRADE/ROBINS-I appraisal logic rather than RCT-hierarchy logic, and that context-sensitivity is a feature of HPSR, not to be treated as a weakness. 

Both skills are visible in the output. The first test run on "ASHA programme effectiveness India" produced 19 sources, all from PubMed/PMC, Lancet, BMJ, and NHSRC government reports - zero arXiv papers. The output distinguished between pilot/special intervention evidence (overwhelmingly positive, 77%) and routine programme evidence (mixed, 55% -- negative, 23%), which is exactly the implementation-sensitive framing the `hpsr-epistemology` skill was written to produce. 


Both core skills written and installed. 

**Still to write:**

A **`grey-literature`** skill instructing the Researcher to systematically reach WHO IRIS, NHSRC, IIPS, NITI Aayog health chapters, SRS data, and state NHM materials. 

A **`reviewer-appraisal`** skill replacing the default peer review criteria with CASP checklists for qualitative work, Cochrane risk-of-bias logic for trials, and GRADE framing for evidence synthesis. Makes the `/review` workflow useful for public health peer reviewers.

A **`policy-writer`** skill teaching the Writer agent what a policy brief looks like, how a rapid evidence review is structured, and how HPSR synthesis papers differ from standard journal articles.

### source connectors (needs a developer)

The key connector is a `pubmed` CLI tool wrapping NCBI's E-utilities (esearch + efetch) -- the direct equivalent of the `alpha` CLI Feynman uses for AlphaXiv. Needs to: search by keyword, MeSH term, and date range; retrieve full metadata; pull abstracts and PMIDs. NCBI API is free, no authentication needed for basic use. 

After that: WHO IRIS connector via their OAI-PMH endpoint; Cochrane REST API for abstracts and Plain Language Summaries (full text needs institutional access but the summary layer is free and useful for scoping); India-specific curated URL corpus for NFHS, HMIS, NHSRC, and MoHFW materials.

### new workflows 

Workflows to retire: `/audit` (paper vs codebase is noyt needed ), `/replicate` (GPU experiment replication also irrelevant).

Workflows to add:

`/sysrev` -- PICO formulation, PRISMA-compatible search string generation for PubMed and Cochrane, deduplication scaffolding, PRISMA flow outline. Won't replace [[Covidence]] or Rayyan for the screening phase, but compresses early scoping substantially.

`/policybrief` -- synthesise evidence into a structured brief with problem statement, evidence summary, policy options, implementation considerations.

`/burden` -- aggregate epidemiological data from GBD, NFHS, DLHS, and state health bulletins into a usable summary for grant background sections.

`/greylit` -- explicitly instructs the Researcher to prioritise institutional and government sources over academic journals for a query.

`/watch` already exists in base Feynman and transfers directly -- useful for monitoring WHO guideline updates, new Lancet publications on a topic, MoHFW policy notifications.


## What would make this more than just "Feynman but for PubMed"

A lot of the most important HPSR knowledge is not in text documents at all. It is in datasets (NFHS unit data, HMIS, GBD), legal instruments (Essential Medicines List, Clinical Establishment Act, budget documents), and grey process documents that are not publicly indexed anywhere. A well-designed fork needs a local document repository, a way to feed PDFs and structured data from a curated institutional archive/repo directly into the session. Something like Feynman's session search but seeded with a library of Indian health policy materials. Later-stage feature, but the one that would actually differentiate this from just a better PubMed search tool.

---

## Interim outputs

- [[Effectiveness of India's ASHA Programme]] -- first test run, literature review, 19 sources, all health literature, implementation-sensitive framing visible
- [[Provenance Record for ASHA Programme Effectiveness India]] -- source tracking, verification status, documents skill behaviour
- [[Hospital-based interventions for self-harm in LMIC LIC 2005]]

---

## Follow-up

- [x]  Draft `pubmed-research.md` skill
- [x]  Draft `hpsr-epistemology.md` skill
- [x]  Install and test both skills
- [x]  First test run -- ASHA programme effectiveness
- [ ]  Write `grey-literature.md` skill
- [ ]  Second test run -- NMCR scoping review (using [Implementation Strategies for Maternal Near-Miss Case Reviews in LICs and LMICs protocol](https://wellcomeopenresearch.org/articles/9-247) as reference)
- [ ]  Write `reviewer-appraisal.md` and `policy-writer.md` skills
- [ ]  Explore whether anyone in the HPSR or PH informatics community is working on something similar: worth checking before investing heavily
- [ ]  Look at what [[Elicit]] and [[Consensus]] already do for systematic review support, to avoid reinventing what they do well
- [ ]  Talk to someone with Node.js/Python capacity about the PubMed connector
- [ ]  Decide whether this should be a public GitHub fork from the start or a private experiment first

- [ ] Decide whether this should be a public GitHub fork from the start or a private experiment first

Last updated: 2026-04-13 22:55
