import uuid
import sqlite3
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from state import AssistantState
from nodes import coder_node, executor_node, llm

# Load your custom docs (e.g., Python library docs or your project's code)
# vector_store = FAISS.from_documents(chunks, OpenAIEmbeddings())
# retriever = vector_store.as_retriever()


@tool
def python_repl(code: str):
    """Executes python code and returns the output or error. Use this to test your solutions."""
    try:
        # We use a simple exec for demo, but better to use PythonREPL from langchain_experimental
        # Logic to capture stdout goes here...
        return "Successfully executed. Result: ..."
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def lookup_coding_documentation(query: str):
    """Consult official Python or library documentation to find correct usage/syntax."""
    docs = retriever.get_relevant_documents(query)
    return "\n".join([d.page_content for d in docs])


# 1. Bind tools to the LLM
llm_with_tools = llm.bind_tools([python_repl, lookup_coding_documentation])

async def agent_node(state: AssistantState):
    # Notice the 'async' keyword
    last_error = state["error_history"][-1] if state["error_history"] else "None"
    # We now use 'ainvoke' (Async Invoke)
    response = await llm_with_tools.ainvoke([
        SystemMessage(content="Expert Python Coder"), 
        HumanMessage(content=state['task'])
    ])
    return {"messages": [response]}

# 1. The Router Function (Video 7 & 8)
def should_continue(state: AssistantState):
    if state["error_history"][-1] == "SUCCESS":
        return "end"
    if state["iterations"] >= state["max_iterations"]:
        return "end"
    return "continue"

# 2. Define the Graph
workflow = StateGraph(AssistantState)
workflow.add_node("agent", agent_node)  # Calls llm_with_tools
workflow.add_node("tools", ToolNode([python_repl, lookup_coding_documentation]))
workflow.set_entry_point("agent")
# 3. Use the built-in conditional edge!
workflow.add_conditional_edges("agent", tools_condition)
# 4. Loop tool results back to the agent for "Reflection"
workflow.add_edge("tools", "agent")

# 3. Add Persistence (Video 9)
# 1. Create the Database file
conn = sqlite3.connect("assistant_memory.db", check_same_thread=False)
# 2. Setup the SQLite Checkpointer
memory = SqliteSaver(conn)
app = workflow.compile(checkpointer=memory)

# To "Resume" an old debugging session:
# old_config = {"configurable": {"thread_id": "some-previous-id"}}
# current_state = app.get_state(old_config)
# # Now we can show the user:
# # 1. The original code
# # 2. All the errors it faced
# # 3. The final working version
# print(current_state.values["code_history"][-1])

# 4. Run the Project
if __name__ == "__main__":
    # When the user starts a new task:
    new_task_id = str(uuid.uuid4())
    # Updated config for invocation
    config = {
        "configurable": {"thread_id": str(uuid.uuid4())},
        "run_name": "Python_Assistant_Task",  # Custom name for LangSmith
        "metadata": {"task_type": "debugging"}  # Useful for filtering later
    }
    
    initial_state = {
        "task": "Create a list of numbers from 1 to 10 and print only the prime ones.",
        "max_iterations": 3,
        "iterations": 0,
        "error_history": [],
        "output_history": []
    }
    
    # Instead of: final_state = app.invoke(initial_state)
    # We use a loop:
    for message_chunk, metadata in app.stream({"task": "Create a function to calculate Fibonacci"}, config, stream_mode="messages"):
        # This will print the code/thinking piece-by-piece as it's generated!
        if message_chunk.content:
            print(message_chunk.content, end="", flush=True)