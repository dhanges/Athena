import json
import requests
import time
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field
from tools import search_papers, search_github, get_bibtex
from state import ResearchState

from dotenv import load_dotenv
load_dotenv(override=True)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

class IdeationOutput(BaseModel):
    report_markdown: str = Field(description="The full report including Gap Analysis and the Sources Table.")
    gap_confidence: float = Field(description="Score from 0.0 to 1.0 for gap analysis.")
    feasibility_score: float = Field(description="Score from 0.0 to 1.0 for project feasibility.")

class PlannerStructure(BaseModel):
    queries: List[str] = Field(description="A list of 5 search queries.")
    is_search_required: bool = Field(description="True if we need to hit APIs, False if user is just asking about current state.")
    specific_request_type: str = Field(description="e.g., 'table', 'bibtex', 'full', 'detail'")
def planner_node(state: ResearchState):
    """
    Analyzes the user request and generates optimized search queries.
    """
    last_user_input = state["messages"][-1].content if state.get("messages") else state["user_query"]
    system_prompt = SystemMessage(content=(
         """You are a Research Strategist. Your goal is to analyze the user's request. 
    1. If they want a NEW topic: Set 'next_step' to 'search'. Based on keywords in their request to generate 3 HIGHLY SPECIFIC search queries for academic research and 2 search queries for git repositories or code implementation.
    2. If they are asking for a specific format (Table, BibTeX) of EXISTING results: Set 'next_step' to 'chat'.
    3. If they are asking for details on a paper already in the list: Set 'next_step' to 'chat'."""
    ))
    
    user_input = HumanMessage(content=f"Research Request: {state['user_query']}")
    structured_llm = llm.with_structured_output(PlannerStructure) 
    response = structured_llm.invoke([system_prompt, HumanMessage(content=last_user_input)])
    return {
        "search_queries": response.queries if response.is_search_required else [],
        "next_step": "search" if response.is_search_required else "chat",
        "display_mode": response.specific_request_type
    }
    
    

def academic_search_node(state: ResearchState):
    queries = state["search_queries"][:3]
    existing_urls = {p['url'] for p in state.get("research_papers", [])}
    all_papers = []
    all_citations = []
    
    for q in queries:
        results = search_papers(q, limit=3, min_year=2024, min_citations=2)
        time.sleep(1.0)
        if not results:
            continue
        for p in results:
            p_url = p.get("url")
            if p_url and p_url not in existing_urls:
                tldr_obj = p.get("tldr")
                tldr_text = tldr_obj.get("text") if isinstance(tldr_obj, dict) else None
            distilled_paper = {
                "title": p.get("title", "Unknown Title"),
                "author": p.get("authors", [{}])[0].get("name", "Unknown") if p.get("authors") else "Unknown",
                "year": p.get("year"),
                "summary": tldr_text or p.get("abstract", "")[:500] or "No summary available.",
                "url": p.get("url")
            }
            all_papers.append(distilled_paper)
            existing_urls.add(p_url)
            doi = p.get("externalIds", {}).get("DOI") if p.get("externalIds") else None
            if doi:
                bib = get_bibtex(doi)
                if bib and bib not in state.get("citations", []):
                    if bib and "not found" not in bib.lower(): 
                        all_citations.append(bib)
                
    return {
        "research_papers": all_papers,
        "citations": list(set(all_citations))
    }

def github_search_node(state: ResearchState):
    queries = state["search_queries"][-2:]
    existing_repos = {r['url'] for r in state.get("github_projects", [])}
    all_projects = []
    
    for q in queries:
        repos = search_github(q, max_results=3)
        for r in repos:
            if r['url'] not in existing_repos:
                all_projects.append(r)
                existing_repos.add(r['url'])
        
    return {"github_projects": all_projects}
    
    
ideator_llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

def ideator_node(state: ResearchState):
    """
    The 'PhD' node. Synthesizes research and code to find gaps.
    """
    papers_context = json.dumps(state["research_papers"], indent=2)
    github_context = json.dumps(state["github_projects"], indent=2)
    
    system_prompt = (
        "You are a Senior Research Scientist. Review the provided Academic Papers and GitHub Projects.\n"
        "Your task: \n"
        "1. **Gap Analysis**: Identify 3 specific Research Gaps or industry pain points.\n"
        "2. **Source Material Table**: You MUST generate a Markdown table with columns: [Type (Paper/Repository), Title, Author/Owner, Link/URL]. "
        "List every relevant paper and repository found in the context.\n"
        "3. **Novel Project Path**: Suggest a path combining these findings. State the core research question it explores.\n"
        "Be brutally honest with your confidence scores."
    )
    
    context_message = f"User Query: {state['user_query']}\n\n" \
                      f"Papers: {papers_context}\n\n" \
                      f"GitHub: {github_context}"

    structured_ideator = ideator_llm.with_structured_output(IdeationOutput)
    result = structured_ideator.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=context_message)
    ])
    
    return {
        "final_report": result.report_markdown,
        "confidence_scores": {
            "gap_analysis": result.gap_confidence,
            "feasibility": result.feasibility_score
        }
    }

def chat_node(state: ResearchState):
    all_papers = state.get("research_papers", [])
    all_citations = list(set(state.get("citations", [])))
    all_repos = state.get("github_projects", [])
    
    mode = state.get("display_mode", "summary")
    last_msg = state["messages"][-1].content.lower() if state.get("messages") else ""
    
    if mode == "bibtex" or "citation" in last_msg or "bibtex" in last_msg:
        if not all_citations:
            content = "I couldn't find valid DOIs to generate BibTeX."
        else:
            content = "### All BibTeX Citations\n"
            content += "I've compiled the citations for all papers found during this session:\n\n"
            content += "```bibtex\n" + "\n\n".join(all_citations) + "\n```"
            
    elif mode == "table" or "previous" in last_msg or "all papers" in last_msg:
        if not all_papers:
            content = "My research memory is currently empty. What topic should we dive into?"
        else:
            content = "### Complete Research History\n"
            content += "Here is the full list of sources I've gathered across this session:\n\n"
            content += "| Type | Title | Author/Year | Link |\n| :--- | :--- | :--- | :--- |\n"
            for p in all_papers:
                content += f"| Paper | {p['title']} | {p['author']} ({p['year']}) | [View]({p['url']}) |\n"
            for r in all_repos:
                content += f"| Repo | {r['title']} | {r['owner']} | [GitHub]({r.get('url', '#')}) |\n"

    else:
        content = state.get("final_report")
        if not content:
            content = "I'm ready to continue. We can look for more papers, generate BibTeX for the current ones, or start a new topic."

    footer = "\n\n**What's our next move?** (e.g., 'Find more on...', 'Give me citations', or 'Deep dive into paper #...')"
    
    return {"messages": [AIMessage(content=f"{content}{footer}")]}
