import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from state import ChatState
from voice_integration import voice_integration

load_dotenv()

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)

def chat_node(state: ChatState):
    """Generate AI response to user message."""
    print("--- GENERATING AI RESPONSE ---")
    
    try:
        # Get the conversation history
        messages = state.get("messages", [])
        
        # Check if this is a regeneration with feedback
        improvement_request = state.get("improvement_request")
        human_feedback = state.get("human_feedback")
        
        # Add system message for context
        if improvement_request:
            # Use improvement request for regeneration
            system_message = SystemMessage(
                content=f"""You are a helpful AI assistant. The user was not satisfied with your previous response. 
                Please improve your answer based on their feedback: {human_feedback}
                
                Provide a better, more comprehensive response that addresses their concerns."""
            )
        else:
            system_message = SystemMessage(
                content="""You are a helpful AI assistant with voice capabilities. 
                Provide clear, concise, and engaging responses. Keep responses 
                conversational and natural for both text and voice interaction."""
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