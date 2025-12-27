import sys
import io
from langchain_openai import ChatOpenAI # Using GPT-4o-mini as per Video 8
from langchain_core.messages import SystemMessage, HumanMessage
from state import AssistantState

llm = ChatOpenAI(model="gpt-4o-mini")

def coder_node(state: AssistantState):
    """The Generator: Writes or fixes code based on history."""
    print(f"--- ATTEMPT {state['iterations'] + 1} ---")
    
    # Construct history context for the LLM
    history = ""
    if state['error_history']:
        for i, err in enumerate(state['error_history']):
            history += f"\nAttempt {i+1} failed with error: {err}"

    system_prompt = SystemMessage(content="You are an expert Python developer. Output ONLY raw python code without markdown backticks.")
    user_content = f"Task: {state['task']}\n{history}\n\nPlease fix the code."
    
    response = llm.invoke([system_prompt, HumanMessage(content=user_content)])
    return {"code": response.content.strip(), "iterations": 1}

def executor_node(state: AssistantState):
    """The Evaluator: Runs the code and captures errors."""
    code = state['code']
    # Using a string buffer to capture stdout
    stdout_capture = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = stdout_capture
    
    try:
        # Warning: exec() is used for learning; use Docker in production!
        exec(code, {})
        error = "SUCCESS"
        output = stdout_capture.getvalue()
    except Exception as e:
        error = str(e)
        output = ""
    finally:
        sys.stdout = old_stdout
        
    return {"error_history": [error], "output_history": [output]}