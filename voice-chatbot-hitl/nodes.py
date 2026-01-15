import os
import uuid
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore
from state import ChatState
from voice_integration import voice_integration

load_dotenv()

# Initialize LLMs
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    api_key=os.getenv("GOOGLE_API_KEY")
)

# Memory extraction LLM (lower temperature for consistent extraction)
memory_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    api_key=os.getenv("GOOGLE_API_KEY")
)


# Memory extraction classes
class MemoryItem(BaseModel):
    text: str = Field(description="Atomic user memory as a short sentence")
    is_new: bool = Field(description="True if this memory is NEW and should be stored. False if duplicate/already known.")

class MemoryDecision(BaseModel):
    should_write: bool = Field(description="Whether to store any memories")
    memories: List[MemoryItem] = Field(default_factory=list, description="Atomic user memories to store")

# Create structured output extractor
memory_extractor = memory_llm.with_structured_output(MemoryDecision)

# System prompt template for personalized responses
SYSTEM_PROMPT_TEMPLATE = """You are a helpful AI assistant with memory capabilities and voice capabilities.
If user-specific memory is available, use it to personalize your responses based on what you know about the user.

Your goal is to provide relevant, friendly, and tailored assistance that reflects the user's preferences, context, and past interactions.

If the user's name or relevant personal context is available, always personalize your responses by:
    – Addressing the user by name (e.g., "Sure, [name]...") when appropriate
    – Referencing known projects, tools, or preferences
    – Adjusting the tone to feel friendly, natural, and directly aimed at the user

Avoid generic phrasing when personalization is possible. For example, instead of "In Python apps..." 
say "Since you prefer Python..."

Use personalization especially in:
    – Greetings and transitions
    – Help or guidance tailored to tools and frameworks the user uses
    – Follow-up messages that continue from past context

Always ensure that personalization is based only on known user details and not assumed.

Keep responses clear, concise, and engaging. Make them conversational and natural for both text and voice interaction.

The user's memory (which may be empty) is provided as: {user_details_content}
"""

# Memory extraction prompt
MEMORY_PROMPT = """You are responsible for updating and maintaining accurate user memory.

CURRENT USER DETAILS (existing memories):
{user_details_content}

TASK:
- Review the user's latest message.
- Extract user-specific info worth storing long-term (identity, stable preferences, ongoing projects/goals).
- For each extracted item, set is_new=true ONLY if it adds NEW information compared to CURRENT USER DETAILS.
- If it is basically the same meaning as something already present, set is_new=false.
- Keep each memory as a short atomic sentence.
- No speculation; only facts stated by the user.
- If there is nothing memory-worthy, return should_write=false and an empty list.
"""

def remember_node(state: ChatState, config: RunnableConfig = None, *, store: BaseStore = None):
    """Extract and store long-term memories from user messages."""
    print("--- EXTRACTING MEMORIES ---")
    
    if not store:
        # If no store provided, skip memory extraction
        return {}
    
    try:
        # Get user_id from config or state
        user_id = None
        if config and "configurable" in config:
            user_id = config["configurable"].get("user_id")
        if not user_id:
            user_id = state.get("thread_id", "default_user")
        
        namespace = ("user", user_id, "details")
        
        # Load existing memories
        existing_items = store.search(namespace)
        existing_texts = [it.value.get("data", "") for it in existing_items if it.value.get("data")]
        user_details_content = "\n".join(f"- {t}" for t in existing_texts) if existing_texts else "(empty)"
        
        # Get latest user message
        messages = state.get("messages", [])
        if not messages:
            return {}
        
        last_message = messages[-1]
        if hasattr(last_message, 'content'):
            last_text = last_message.content
        else:
            last_text = str(last_message)
        
        # Extract memories using LLM
        decision: MemoryDecision = memory_extractor.invoke(
            [
                SystemMessage(content=MEMORY_PROMPT.format(user_details_content=user_details_content)),
                HumanMessage(content=f"USER MESSAGE:\n{last_text}"),
            ]
        )
        
        # Store only new memories
        if decision.should_write:
            for mem in decision.memories:
                if mem.is_new and mem.text.strip():
                    store.put(namespace, str(uuid.uuid4()), {"data": mem.text.strip()})
                    print(f"💾 Stored memory: {mem.text.strip()}")
        
        return {}
        
    except Exception as e:
        print(f"⚠️ Memory extraction error: {str(e)}")
        return {}

def chat_node(state: ChatState, config: RunnableConfig = None, *, store: BaseStore = None):
    """Generate AI response to user message with LTM personalization."""
    print("--- GENERATING AI RESPONSE ---")
    
    try:
        # Get the conversation history
        messages = state.get("messages", [])
        
        # Check if this is a regeneration with feedback
        improvement_request = state.get("improvement_request")
        human_feedback = state.get("human_feedback")
        
        # Load user memories from LTM store for personalization
        user_details_content = ""
        if store:
            try:
                user_id = None
                if config and "configurable" in config:
                    user_id = config["configurable"].get("user_id")
                if not user_id:
                    user_id = state.get("thread_id", "default_user")
                
                namespace = ("user", user_id, "details")
                items = store.search(namespace)
                if items:
                    user_details = [it.value.get("data", "") for it in items if it.value.get("data")]
                    user_details_content = "\n".join(f"- {d}" for d in user_details) if user_details else ""
            except Exception as e:
                print(f"⚠️ Error loading memories: {str(e)}")
                user_details_content = ""
        
        # Add system message for context
        if improvement_request:
            # Use improvement request for regeneration
            system_message = SystemMessage(
                content=f"""You are a helpful AI assistant. The user was not satisfied with your previous response. 
                Please improve your answer based on their feedback: {human_feedback}
                
                Provide a better, more comprehensive response that addresses their concerns.
                
                {f'User context: {user_details_content}' if user_details_content else ''}"""
            )
        else:
            # Use personalized system prompt with LTM context
            system_message = SystemMessage(
                content=SYSTEM_PROMPT_TEMPLATE.format(
                    user_details_content=user_details_content or "(empty)"
                )
            )
        
        # Prepare messages for LLM
        if improvement_request:
            # For regeneration, use the improvement request
            llm_messages = [system_message, HumanMessage(content=improvement_request)]
        else:
            # For new conversations, use full history
            llm_messages = [system_message] + messages
        
        # Generate response
        response = llm.invoke(llm_messages)
        
        return {
            "pending_response": response.content,
            "messages": [response],
            "improvement_request": None  # Clear improvement request after use
        }
        
    except Exception as e:
        error_response = AIMessage(content=f"I apologize, but I encountered an error: {str(e)}")
        return {
            "pending_response": error_response.content,
            "messages": [error_response]
        }

def human_review_node(state: ChatState):
    """Simplified Human-in-the-Loop review of AI response."""
    print("\n" + "="*50)
    print("👤 HUMAN REVIEW")
    print("="*50)
    
    pending_response = state.get("pending_response")
    if not pending_response:
        return {
            "human_approval": False,
            "human_feedback": "No response to review"
        }
    
    print(f"\n🤖 AI Response:")
    print(f"{pending_response}")
    print("-" * 50)
    
    # Voice preview option
    voice_available = voice_integration.is_available()
    if voice_available:
        preview_choice = input("🔊 Play audio preview? (y/n): ").lower().strip()
        if preview_choice == 'y':
            print("🎵 Generating speech...")
            selected_voice = state.get("selected_voice", "aura-asteria-en")
            audio_bytes = voice_integration.text_to_speech(pending_response, selected_voice)
            if audio_bytes:
                print("✅ Audio generated (would play in GUI)")
            else:
                print("❌ Failed to generate audio")
    
    # Simple HITL questions
    while True:
        happy = input("\n😊 Are you happy with this result? (y/n): ").lower().strip()
        
        if happy == 'y':
            return {
                "human_approval": True,
                "approved_responses": [pending_response]
            }
        elif happy == 'n':
            # Ask what to change/add
            changes = input("💭 What would you like to change or add to the answer? ").strip()
            
            if changes:
                # Create improved prompt for regeneration
                improved_prompt = f"Previous answer: {pending_response}\n\nUser feedback: {changes}\n\nPlease improve the answer based on this feedback."
                
                return {
                    "human_approval": False,
                    "rejected_responses": [pending_response],
                    "human_feedback": changes,
                    "improvement_request": improved_prompt
                }
            else:
                # Just regenerate without specific feedback
                return {
                    "human_approval": False,
                    "rejected_responses": [pending_response],
                    "human_feedback": "User not satisfied, regenerating response"
                }
        else:
            print("Please enter 'y' for yes or 'n' for no")

def response_delivery_node(state: ChatState):
    """Deliver approved response to user."""
    print("--- DELIVERING RESPONSE ---")
    
    if state.get("human_approval"):
        approved_responses = state.get("approved_responses", [])
        if approved_responses:
            final_response = approved_responses[-1]  # Get the latest approved response
            
            # Generate audio if voice is enabled
            if state.get("voice_enabled") and voice_integration.is_available():
                selected_voice = state.get("selected_voice", "aura-asteria-en")
                audio_bytes = voice_integration.text_to_speech(final_response, selected_voice)
                if audio_bytes:
                    return {
                        "messages": [AIMessage(content=final_response)],
                        "audio_responses": [audio_bytes]
                    }
            
            return {
                "messages": [AIMessage(content=final_response)]
            }
    
    # If not approved, generate a new response
    return {
        "messages": [AIMessage(content="Let me try a different approach...")]
    }
