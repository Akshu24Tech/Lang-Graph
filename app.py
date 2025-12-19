from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from state import AssistantState
from nodes import coder_node, executor_node

# 1. The Router Function (Video 7 & 8)
def should_continue(state: AssistantState):
    if state["error_history"][-1] == "SUCCESS":
        return "end"
    if state["iterations"] >= state["max_iterations"]:
        return "end"
    return "continue"

# 2. Build the Graph
workflow = StateGraph(AssistantState)

workflow.add_node("coder", coder_node)
workflow.add_node("executor", executor_node)

workflow.set_entry_point("coder")
workflow.add_edge("coder", "executor")

# The Logic Loop
workflow.add_conditional_edges(
    "executor",
    should_continue,
    {
        "continue": "coder",
        "end": END
    }
)

# 3. Add Persistence (Video 9)
memory = InMemorySaver()
app = workflow.compile(checkpointer=memory)

# 4. Run the Project
if __name__ == "__main__":
    config = {"configurable": {"thread_id": "coding_session_1"}}
    initial_state = {
        "task": "Create a list of numbers from 1 to 10 and print only the prime ones.",
        "max_iterations": 3,
        "iterations": 0,
        "error_history": [],
        "output_history": []
    }
    
    final_result = app.invoke(initial_state, config=config)
    print("\n--- FINAL RESULT ---")
    print(final_result["output_history"][-1])