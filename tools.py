import os
import arxiv
import requests 
import time
from github import Github
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv(override=True)

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
github_client = Github(os.getenv("GITHUB_TOKEN"))


def search_papers(query: str, limit: int = 5, min_year: int = 2020, min_citations: int = 5):
    """
    Searches Semantic Scholar Public Tier.
    Includes quality filters and a basic rate-limit retry.
    """
    endpoint = "https://api.semanticscholar.org/graph/v1/paper/search"
    
    fields = "title,authors,year,citationCount,url,abstract,externalIds,tldr"
    
    params = {
        "query": query,
        "limit": limit + 5, 
        "fields": fields,
        "year": f"{min_year}-"
    }

    for attempt in range(3):
        try:
            response = requests.get(endpoint, params=params, timeout=15)
            
            if response.status_code == 429:
                print(f"Public Tier Rate Limit hit. Retrying in {attempt + 2}s...")
                time.sleep(attempt + 2)
                continue
                
            response.raise_for_status()
            data = response.json().get("data", [])
            
            filtered = [
                p for p in data 
                if p.get("citationCount", 0) >= min_citations or p.get("year", 0) >= 2025
            ]
            return filtered[:limit]

        except Exception as e:
            print(f"Search Error: {e}")
            break
            
    return []
    
def search_github(query: str, max_results: int = 5):
    try:
        enhanced_query = f"{query} stars:>10 fork:true" 
        repositories = github_client.search_repositories(query=enhanced_query, sort="stars")
        projects = []
        for i, repo in enumerate(repositories):
            if i >= max_results: break
            projects.append({
                "type": "Repository",
                "title": repo.name,
                "owner": repo.owner.login,
                "stars": repo.stargazers_count,
                "url": repo.html_url,
                "description": repo.description[:200] if repo.description else ""
            })
        return projects
    except Exception as e:
        print(f"GitHub Search Error: {e}")
        return []
    
def get_bibtex(doi: str):
    if not doi: return "No DOI available"
    url = f"https://doi.org/{doi}"
    headers = {"Accept": "application/x-bibtex"} 
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        return response.text if response.status_code == 200 else ""
    except:
        return "Service Timeout"

def general_web_search(query: str):
    return tavily.search(query=query, search_depth="advanced")
