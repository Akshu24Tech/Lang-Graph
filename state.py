import operator
from typing import TypedDict, Annotated, List, Optional

class AssistantState(TypedDict):
    task: str                        # The user's coding request
    code: str                        # The current version of code
    # Reducers: New errors/outputs are appended to the list, not overwritten
    error_history: Annotated[List[str], operator.add] 
    output_history: Annotated[List[str], operator.add] 
    iterations: Annotated[int, operator.add] 
    max_iterations: int