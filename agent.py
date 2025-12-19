from typing import TypedDict, Annotated, List, Literal
from langgraph.graph import StateGraph, END
import operator

# --- 1. Define the State ---
# As per the video: This is the shared memory that flows through the graph.
class GraphState(TypedDict):
    question: str           # The user's input
    generated_code: str     # The code produced by the agent
    execution_output: str   # The result of running the code
    error: Annotated[List[str], operator.add]    # Any error message (if it fails)
    iterations: int         # Safety counter to stop infinite loops

# --- 2. Define the Nodes ---
# As per the video: These are Python functions that modify the State.

def generate_solution(state: GraphState):
    """
    Node: Coder
    Responsibility: Write code.
    """
    print(f"\n--- GENERATING SOLUTION (Iteration: {state.get('iterations', 0)}) ---")
    
    # Mock Logic: In the future, the LLM call goes here.
    # For now, let's simulate generating code.
    generated_code = "print('Hello, LangGraph!')"
    
    # Increment iteration count
    current_iter = state.get("iterations", 0)
    
    return {"generated_code": generated_code, "iterations": current_iter + 1}
    
def evaluate_solution(state: GraphState):
    """
    Node: Executor
    Responsibility: Run the code and check for errors.
    """
    print("--- EXECUTING CODE ---")
    code = state["generated_code"]
    
    # Mock Logic: Simulate execution.
    # Change 'simulate_error = False' to True to see the retry logic work!
    simulate_error = False 
    
    if simulate_error and state.get("iterations", 0) < 2:
        error_msg = "SyntaxError: missing parenthesis"
        print(f"❌ Execution Failed: {error_msg}")
        return {"error": error_msg}
    else:
        output = "Hello, LangGraph!"
        print(f"✅ Execution Success: {output}")
        return {"execution_output": output, "error": None}

def decide_next_step(state: GraphState):
    """
    Conditional Logic (The Router)
    Responsibility: Decide if we should retry or finish.
    """
    error = state.get("error")
    
    if error:
        # If there is an error, go back to generate_solution
        return "retry"
    else:
        # If no error, go to END
        return "end"

# --- 3. Build the Graph ---
# As per the video: Connect nodes with edges.

workflow = StateGraph(GraphState)

# Add Nodes
workflow.add_node("coder", generate_solution)
workflow.add_node("executor", evaluate_solution)

# Set Entry Point
workflow.set_entry_point("coder")

# Add Normal Edges (Coder -> Executor)
workflow.add_edge("coder", "executor")

# Add Conditional Edges (Executor -> ??)
workflow.add_conditional_edges(
    "executor",
    decide_next_step,
    {
        "retry": "coder",
        "end": END
    }
)

# Compile the graph
app = workflow.compile()

# --- 4. Run the Graph ---
if __name__ == "__main__":
    # Initial State
    initial_input = {"question": "Write a python script to print hello world", "iterations": 0}
    
    print("🚀 Starting Agent...")
    
    # Execute the graph
    # We use invoke to run it synchronously
    result = app.invoke(initial_input)
    
    print("\n--- FINAL RESULT ---")
    print(f"Code: {result['generated_code']}")
    print(f"Output: {result['execution_output']}")