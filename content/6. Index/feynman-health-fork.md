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

For people working in public health, [[Health policy and systems research|HPSR]], epidemiology, health systems, or anything qual/soc-sci types, this is not use-able. The tool also has a bunch of workflows (GPU experiment replication, paper-vs-codebase audits) that are completely irrelevant to public health work. So the question is: what would it take to fork this and make it actually useful for public health folks?

Feynman's agent behaviour runs on "skills" which are basically Markdown instruction files sitting in `~/.feynman/agent/skills/`. When the researcher agent decides how to search, what to prioritise, how to evaluate sources, all of that logic lives in text files you can rewrite. 

The harder part is the source of the stuff. AlphaXiv gives Feynman full-text paper access, citation chains, and Q&A on specific papers, all of that has to be rebuilt pointing at the right databases. But the APIs we need (PubMed E-utilities, WHO IRIS) are free and well-documented. 

A non-developer like me can edit skills as needed. Might need bit of help from developer to build the source connectors. 

## The plan

###  Edit the skills 

This is where most of the field/discipline-specific intelligence should live. 

A **`pubmed-research.md`** skill that tells the Researcher to query PubMed first, use MeSH terms rather than free-text guessing, and understand that systematic reviews and primary epidemiological studies are different kinds of evidence that get weighted differently.

An **`hpsr-epistemology.md`** skill that teaches the agent that qualitative studies, mixed-methods designs, and implementation science papers are first-class evidence. Right now the tool basically treats anything that isn't a quantitative paper as a fallback web result. That has to change for HPSR work.

A **`grey-literature.md`** skill telling the Researcher to treat WHO reports, MoHFW documents, NHSRC publications, state NHP materials, parliamentary standing committee reports, and IIPS data as primary sources.

A **`reviewer-appraisal.md`** skill that replaces the default peer review criteria with CASP checklists for qualitative work, Cochrane risk-of-bias logic for trials, and GRADE framing for evidence synthesis. The `/review` workflow could then actually be useful for PH peer reviewers.

A **`policy-writer.md`** skill teaching the Writer agent what a policy brief looks like, how a rapid evidence review is structured, and how HPSR synthesis papers differ from standard journal articles.

###  source connectors 

The key connector is a `pubmed` CLI tool wrapping NCBI's E-utilities (esearch + efetch). This would be the direct equivalent of the `alpha` CLI that Feynman uses for AlphaXiv. It needs to: search by keyword, MeSH term, and date range; retrieve full metadata; and pull abstracts and PMIDs. This needs some work.

After that, a [[WHO IRIS]] connector using their OAI-PMH endpoint. The Cochrane REST API for abstracts and Plain Language Summaries is also worth adding. Full text requires institutional access but the summary layer is free and useful for scoping.

For India-specific content, there's no single API. The realistic approach is a curated URL list that the web search agent is explicitly instructed to prioritise: NFHS, HMIS, NHSRC reports, NITI Aayog health chapters, SRS data. Plus a local PDF ingestion path for frequently-used institutional documents that aren't publicly indexed.

### New workflows 

The workflows to retire: `/audit` (paper vs codebase audit), `/replicate` (GPU experiment replication).

The workflows to add:

`/sysrev` for systematic review support -- PICO formulation, PRISMA-compatible search string generation for PubMed and Cochrane, deduplication, PRISMA flow outline. This won't replace Covidence or Rayyan for the screening phase, but it compresses the early scoping work substantially.

`/policybrief` to synthesise evidence into a structured brief -- problem statement, evidence summary, policy options, implementation considerations. Useful for rapid-turnaround work and grant background sections.

`/appraise` applying CASP, GRADE, or ROBINS-I to a supplied document. The Reviewer agent already does something structurally similar; it just needs the skills layer to specify the right frameworks.

`/burden` to aggregate epidemiological data from GBD, NFHS, DLHS, and state health bulletins into a usable summary. Useful for grant writing.

`/greylit` explicitly instructing the Researcher to prioritise institutional and government sources over academic journals for a query.

`/watch` already exists in the base tool and transfers directly -- monitoring new WHO guideline updates, Lancet publications on a topic, or MoHFW policy notifications.

## What would make this more than just "Feynman but for PubMed"

Lot of the important knowledge is in datasets (NFHS unit data, HMIS, GBD), legal instruments (Essential Medicines List, Clinical Establishment Act, budget documents), and grey process documents that aren't publicly indexed anywhere.

Ideally a local document pathway, a way to source PDFs and structured data from a curated institutional repo/archive directly into the session. Something like Feynman's session search but seeded with a maintained library of Indian health policy materials. That's probably a later-stage feature, but it's the thing that would differentiate a useful HPSR tool from one that is just better at finding PubMed papers.

## Follow-up

- [ ] Explore whether anyone else in the HPSR or PH informatics community is already working on something similar - worth checking before investing heavily
- [ ] Draft the `pubmed-research.md` skills file as a proof of concept 
- [ ] Check NCBI E-utilities API documentation for rate limits and authentication requirements
- [ ] Talk to someone with Node.js/Python capacity who might want to build the PubMed connector
- [ ] Look at what [[Elicit]] and [[Consensus]] already do for systematic review support, to avoid reinventing what they do well
- [ ] Identify 3-4 specific research tasks from current work at [[IPH Bengaluru]] that could test whether this fork is actually delivering -- don't evaluate in the abstract
- [ ] Decide whether this should be a public GitHub fork from the start or a private experiment first

Last updated: 2026-04-01 21:32
