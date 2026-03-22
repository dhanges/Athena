from typing import TypedDict, List, Annotated, Dict, Optional
import operator
from langchain_core.messages import BaseMessage

class ResearchState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    user_query: str 
    
    search_queries: List[str] 
    research_papers: Annotated[List[dict], operator.add]
    github_projects: Annotated[List[dict], operator.add]
    citations: Annotated[List[str], operator.add]
    
    final_report: str 
    confidence_scores: Dict[str, float]
    
    next_step: str # Used for conditional edges: "search", "chat", "finalize"
    display_mode: str # "table", "bibtex", "summary", "detail"
    errors: Annotated[List[str], operator.add]
