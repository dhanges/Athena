# Athena
An agentic research strategist that thinks before it searches — 
planning queries, parallelizing retrieval, and surfacing what 
the research in that area hasn't explored yet.

## The Problem
Research discovery is broken for students and early-stage researchers.
You either drown in papers you can't evaluate, or you miss entire 
subfields because you didn't know the right search terms.

Finding what is yet to be done is harder than finding what has been.
That's the problem Athena solves.

## What It Does
Athena doesn't just search. It strategizes.

1. Plans — constructs 5 optimized queries for both academic 
   literature and open-source technical work
2. Parallelizes — splits queries between an Academic Researcher 
   (Semantic Scholar) and a GitHub Researcher simultaneously
3. Organizes — maintains a live table of papers and projects 
   with titles, authors, links and citations
4. Synthesizes — an Ideation Agent reads across all findings 
   and identifies genuine gaps, unexplored questions, and novel 
   project directions
5. Converses — a Chat Mode lets you dive into any single paper 
   with follow-up questions, in a dynamic loop with the planner

## Architecture
```
[User Research Goal]
        ↓
[Planner Node] ← decides next_step: Search / Chat
   constructs 5 optimized queries
        ↓
[Search Fork]
  /           \
[Academic      [GitHub
Researcher]    Researcher]
Semantic       GitHub
Scholar API    REST API
  \           /
        ↓
[Ideation Agent]
Generates a table of resources with
type, titles, authors, links
Then provides a gap analysis + unexplored questions
+ novel project paths + action plan
        ↓
[Chat Node] ←→ [Planner] (cyclic until END)
ask questions about any retrieved paper. Set a display mode for table and citations.

## Tech Stack
- LangGraph — multi-agent orchestration with parallel search
- Semantic Scholar API — academic paper retrieval
- GitHub REST API — open source project discovery
- Thread-based state persistence — cumulative citations across sessions
- Python

## Getting Started
git clone https://github.com/dhanges/Athena
cd athena
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
add your API keys to .env
python run.py

## What Makes Athena Different
Most research tools retrieve. Athena makes suggestion, plans, maintains your searches so you can simply copy paste BibTex.

The Ideation Agent doesn't summarize what exists —
it identifies the core questions, setting you up for a journey to dicover and build. The gap between what's 
been done in academia and what's been built in open 
source is where novel research lives. Athena finds that gap.

## Future Work
Add more sources for research.
Gamify the research process with random areas and thought provoking ideation.
Allow users select their resources. Semantic Scholar, ArXiv, Business articles/Case studies.
Cross-session memory: remember what you've explored 
across research sessions
Hypothesis scoring: rank novel project paths by 
feasibility and novelty. Right now its just a confidence score
Export to structured literature review document
Integration with Zotero / reference managers
