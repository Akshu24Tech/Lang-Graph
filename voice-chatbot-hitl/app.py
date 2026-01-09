from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from state import ChatState
from nodes import chat_node, human_review_node, response_delivery_node, remember_node

def should_continue_after_chat(state: ChatState):
    """Decide whether to continue after AI response generation."""
    if state.get("pending_response"):
        return "human_review"
    return "end"

def should_continue_after_review(state: ChatState):
    """Decide whether to continue after human review."""
    if state.get("human_approval"):
        return "deliver_response"
    else:
        # If rejected, regenerate response
        return "chat"

def should_continue_after_delivery(state: ChatState):
    """End the workflow after response delivery."""
    return "end"

# Build the workflow graph
workflow = StateGraph(ChatState)

# Add nodes
workflow.add_node("remember", remember_node)  # LTM: Extract and store memories
workflow.add_node("chat", chat_node)  # Generate response with LTM context
workflow.add_node("human_review", human_review_node)
workflow.add_node("deliver_response", response_delivery_node)

# Set entry point
workflow.set_entry_point("remember")

# Add edges: remember -> chat (always go to chat after remembering)
workflow.add_edge("remember", "chat")

# Add conditional edges
workflow.add_conditional_edges(
    "chat",
    should_continue_after_chat,
    {
        "human_review": "human_review",
        "end": END
    }
)

workflow.add_conditional_edges(
    "human_review",
    should_continue_after_review,
    {
        "deliver_response": "deliver_response",
        "chat": "chat"  # Regenerate if rejected
    }
)

workflow.add_conditional_edges(
    "deliver_response",
    should_continue_after_delivery,
    {
        "end": END
    }
)

# Add persistence
# STM (Short Term Memory): Conversation history per thread
memory = InMemorySaver()

# LTM (Long Term Memory): Persistent user information across sessions
ltm_store = InMemoryStore()

# Compile with both STM (checkpointer) and LTM (store)
app = workflow.compile(checkpointer=memory, store=ltm_store)

# Main execution
if __name__ == "__main__":
    print("🎤 Voice-Enabled Chatbot with Human-in-the-Loop")
    print("=" * 60)
    
    # Configuration
    # thread_id: For STM (conversation history per thread)
    # user_id: For LTM (persistent user memories across all threads)
    config = {
        "configurable": {
            "thread_id": "voice_chat_session_1",
            "user_id": "user_1"  # Change this to identify different users
        }
    }
    
    while True:
        try:
            # Get user input
            user_input = input("\n💬 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Initial state
            initial_state = {
                "messages": [{"role": "user", "content": user_input}],
                "pending_response": None,
                "human_approval": None,
                "approved_responses": [],
                "rejected_responses": [],
                "human_feedback": None,
                "voice_enabled": True,
                "selected_voice": "aura-asteria-en",
                "audio_responses": [],
                "thread_id": "voice_chat_session_1",
                "user_preferences": {}
            }
            
            # Run the workflow
            result = app.invoke(initial_state, config=config)
            
            # Display final response
            if result.get("messages"):
                final_message = result["messages"][-1]
                if hasattr(final_message, 'content'):
                    print(f"\n🤖 Assistant: {final_message.content}")
                else:
                    print(f"\n🤖 Assistant: {final_message}")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            continue
