import gradio as gr
import uuid
import json
from main import gf
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
load_dotenv(override=True)
def run_process(user_input, chat_history, session_id):
    # Ensure session persists
    if not session_id or session_id == []:
        session_id = str(uuid.uuid4())
    
    config = {"configurable": {"thread_id": session_id}}
    
    initial_state = {
        "user_query": user_input,
        "messages": [HumanMessage(content=user_input)],
        "search_queries": [],
        "research_papers": [],
        "github_projects": [],
        "citations": [],
        "final_report": ""
    }

    current_chat = chat_history + [{"role": "user", "content": user_input}, 
                                   {"role": "assistant", "content": "Analyzing your request..."}]
    yield current_chat, session_id

    final_response = ""
    
    for event in gf.stream(initial_state, config, stream_mode="updates"):
        for node_name, state_update in event.items():
            print(f"\n--- NODE: {node_name} ---")
            print(json.dumps({k: v for k, v in state_update.items() if k != "messages"}, indent=2))
            
            if "messages" in state_update:
                final_response = state_update["messages"][-1].content
            
            current_chat = chat_history + [{"role": "user", "content": user_input}, 
                                           {"role": "assistant", "content": f" {node_name.replace('_', ' ').title()}..."}]
            yield current_chat, session_id

    chat_history.append({"role": "user", "content": user_input})
    chat_history.append({"role": "assistant", "content": final_response})
    yield chat_history, session_id

with gr.Blocks(title="Athena") as demo:
    
    session_id = gr.State([])

    gr.Markdown("""
    # Athena: Research Strategist
    ### *Bridging the gap between Academic Theory & Technical Implementation*
    
    **How to use:** Enter a specific technical field (e.g., *'AI applications in FinTech'* or *'Edge AI for Drones'*). 
    Athena will go through **Semantic Scholar** and **GitHub** for you and find research gaps.
    """)
    
    with gr.Row():
        with gr.Column(scale=4):
            chatbot = gr.Chatbot(label="Athena Analysis", height=550)
            msg = gr.Textbox(
                placeholder="Enter a technical research topic...", 
                label="Query",
                info="Pro-tip: Ask for 'all citations' or 'previous papers' to see Athena's persistent memory."
            )
        
        with gr.Column(scale=1):
            gr.Markdown("### Quick Commands")
            cit_btn = gr.Button("Get All BibTeX")
            tab_btn = gr.Button("Show Source Table")
            clear = gr.Button("Reset Session")
            

    msg.submit(run_process, [msg, chatbot, session_id], [chatbot, session_id])
    msg.submit(lambda: "", None, msg)
    
    cit_btn.click(lambda: "give all citations", None, msg).then(
        run_process, [msg, chatbot, session_id], [chatbot, session_id]
    ).then(lambda: "", None, msg)
    
    tab_btn.click(lambda: "give me the full table", None, msg).then(
        run_process, [msg, chatbot, session_id], [chatbot, session_id]
    ).then(lambda: "", None, msg)

    clear.click(lambda: ([], [], str(uuid.uuid4())), None, [chatbot, session_id, msg])

if __name__ == "__main__":
    demo.queue().launch(
        theme=gr.themes.Soft())
