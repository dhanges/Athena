from langgraph.graph import StateGraph, END
from state import ResearchState
from nodes import planner_node, academic_search_node, github_search_node, ideator_node, chat_node
from langgraph.checkpoint.memory import MemorySaver
wf = StateGraph(ResearchState)

def router(state: ResearchState):
    if state.get("next_step") == "search":
        return "search"
    return "chat"

memory = MemorySaver()
wf.add_node("planner", planner_node)
wf.add_node("academic_search", academic_search_node)
wf.add_node("github_search", github_search_node)
wf.add_node("ideator", ideator_node)
wf.add_node("chatbot", chat_node)
def fork_node(state: ResearchState):
    return state # Does nothing, just a junction

wf.add_node("search_fork", fork_node)

wf.set_entry_point("planner")
wf.add_conditional_edges(
    "planner",
    router,
    {
        "search": "search_fork",
        "chat": "chatbot"
    }
)
wf.add_edge("search_fork", "academic_search")
wf.add_edge("search_fork", "github_search")
wf.add_edge("academic_search", "ideator")
wf.add_edge("github_search", "ideator")

wf.add_edge("ideator", "chatbot")
wf.add_edge("chatbot",END)

gf = wf.compile(checkpointer=memory)
