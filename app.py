import uuid
import sqlite3
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

# Load environment variables
load_dotenv()
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from state import AssistantState
from node import coder_node, executor_node, llm

# Load your custom docs (e.g., Python library docs or your project's code)
# vector_store = FAISS.from_documents(chunks, OpenAIEmbeddings())
# retriever = vector_store.as_retriever()


@tool
def python_repl(code: str):
    """Executes python code and returns the output or error. Use this to test your solutions."""
    import sys
    import io
    
    # Capture stdout
    stdout_capture = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = stdout_capture
    
    try:
        # Execute the code
        exec(code, {})
        output = stdout_capture.getvalue()
        return f"Code executed successfully. Output:\n{output}" if output else "Code executed successfully with no output."
    except Exception as e:
        return f"Error executing code: {str(e)}"
    finally:
        sys.stdout = old_stdout


@tool
def lookup_coding_documentation(query: str):
    """Consult official Python or library documentation to find correct usage/syntax."""
    # docs = retriever.get_relevant_documents(query)
    # return "\n".join([d.page_content for d in docs])
    return "Documentation lookup not configured yet. Please set up the retriever first."


# 1. Bind tools to the LLM
llm_with_tools = llm.bind_tools([python_repl, lookup_coding_documentation])

def agent_node(state: AssistantState):
    # Synchronous version
    last_error = state["error_history"][-1] if state["error_history"] else "None"
    # We use 'invoke' (Synchronous Invoke)
    response = llm_with_tools.invoke([
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

# 3. Use the built-in conditional edge with END condition
def should_continue_tools(state: AssistantState):
    """Decide whether to continue or end after tool execution"""
    messages = state.get("messages", [])
    if messages:
        last_message = messages[-1]
        # If the last message doesn't have tool calls, we can end
        if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
            return END
    return "agent"

workflow.add_conditional_edges("agent", tools_condition)
workflow.add_conditional_edges("tools", should_continue_tools)

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
        "metadata": {"task_type": "debugging"},  # Useful for filtering later
        "recursion_limit": 10  # Limit recursion to prevent infinite loops
    }
    
    initial_state = {
        "task": "Create a function to calculate Fibonacci numbers and print the first 10 Fibonacci numbers.",
        "code": "",
        "messages": [],
        "max_iterations": 3,
        "iterations": 0,
        "error_history": [],
        "output_history": []
    }
    
    # Instead of: final_state = app.invoke(initial_state)
    # We use a simple invoke to avoid recursion issues:
    try:
        final_result = app.invoke(initial_state, config=config)
        print("\n--- FINAL RESULT ---")
        print("Messages:")
        if final_result.get("messages"):
            for i, msg in enumerate(final_result["messages"]):
                print(f"Message {i+1}: {msg}")
        print(f"Task: {final_result.get('task', 'N/A')}")
        print(f"Code: {final_result.get('code', 'N/A')}")
    except Exception as e:
        print(f"Error: {e}")