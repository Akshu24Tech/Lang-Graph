import operator
from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage

class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]  # Chat conversation history
    # Simplified HITL features
    pending_response: Optional[str]      # AI response waiting for approval
    human_approval: Optional[bool]       # Whether human approved the response
    approved_responses: Annotated[List[str], operator.add]  # Approved responses
    rejected_responses: Annotated[List[str], operator.add]  # Rejected responses
    human_feedback: Optional[str]        # What user wants to change/add
    improvement_request: Optional[str]   # Formatted request for improvement
    # Voice features
    voice_enabled: bool                  # Whether voice features are active
    selected_voice: str                  # Selected voice model
    audio_responses: Annotated[List[bytes], operator.add]  # Audio versions of responses
    # Session management
    thread_id: str                       # Unique thread identifier
    user_preferences: Optional[dict]     # User preferences and settings