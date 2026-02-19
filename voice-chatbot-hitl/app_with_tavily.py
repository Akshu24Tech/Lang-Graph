"""
Enhanced Voice Chatbot with Tavily Intelligence
Includes internship hunting, company research, lead enrichment, and news monitoring.
"""

import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from src.core.state import ChatState
from src.core.nodes import chat_node, human_review_node, response_delivery_node, remember_node
from src.core.tavily_nodes import (
    tavily_router_node,
    internship_hunter_node,
    company_research_node,
    lead_enrichment_node,
    news_monitor_node
)
from src.integrations.db_config import get_ltm_store

load_dotenv()


def should_use_tavily(state: ChatState):
    """Decide whether to route to Tavily features."""
    tavily_route = state.get("tavily_route", "none")
    if tavily_route and tavily_route != "none":
        return tavily_route
    return "chat"


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
workflow.add_node("remember", remember_node)
workflow.add_node("tavily_router", tavily_router_node)
workflow.add_node("internship_hunter", internship_hunter_node)
workflow.add_node("company_research", company_research_node)
workflow.add_node("lead_enrichment", lead_enrichment_node)
workflow.add_node("news_monitor", news_monitor_node)
workflow.add_node("chat", chat_node)
workflow.add_node("human_review", human_review_node)
workflow.add_node("deliver_response", response_delivery_node)

# Set entry point
workflow.set_entry_point("remember")

# Flow: remember -> tavily_router -> [tavily features OR chat]
workflow.add_edge("remember", "tavily_router")

# Conditional routing from tavily_router
workflow.add_conditional_edges(
    "tavily_router",
    should_use_tavily,
    {
        "internship_hunter": "internship_hunter",
        "company_research": "company_research",
        "lead_enrichment": "lead_enrichment",
        "news_monitor": "news_monitor",
        "chat": "chat"
    }
)

# All Tavily nodes go to chat for final response
workflow.add_edge("internship_hunter", "chat")
workflow.add_edge("company_research", "chat")
workflow.add_edge("lead_enrichment", "chat")
workflow.add_edge("news_monitor", "chat")

# Existing chat flow
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
        "chat": "chat"
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
memory = InMemorySaver()
ltm_store = get_ltm_store()

# Compile with both STM and LTM
app = workflow.compile(checkpointer=memory, store=ltm_store)


# Main execution
if __name__ == "__main__":
    print("🎤 Voice-Enabled Chatbot with Tavily Intelligence")
    print("=" * 60)
    print("Features:")
    print("  🎯 Internship Hunter - Find latest opportunities")
    print("  🏢 Company Research - Deep dive for interviews")
    print("  🔍 Lead Enrichment - Research people for networking")
    print("  📰 News Monitor - Daily AI/ML updates")
    print("=" * 60)
    
    # Configuration
    config = {
        "configurable": {
            "thread_id": "voice_chat_session_1",
            "user_id": "user_1"
        }
    }
    
    print("\n💡 Try commands like:")
    print("  - 'Find AI/ML internships'")
    print("  - 'Research Google for my interview'")
    print("  - 'Get today's AI news'")
    print("  - 'Research John Doe at Microsoft'\n")
    
    while True:
        try:
            # Get user input
            user_input = input("\n💬 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Parse special commands for Tavily features
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
                "user_preferences": {},
                "tavily_route": None,
                "tavily_results": None,
                "target_company": None,
                "lead_name": None,
                "lead_company": None,
                "linkedin_url": None,
                "news_topics": None,
                "company_research": None,
                "lead_data": None,
                "news_brief": None
            }
            
            # Simple command parsing for better UX
            user_lower = user_input.lower()
            
            # Extract company name for research
            if "research" in user_lower and "company" in user_lower:
                # Try to extract company name
                words = user_input.split()
                for i, word in enumerate(words):
                    if word.lower() in ["research", "company"]:
                        if i + 1 < len(words):
                            initial_state["target_company"] = words[i + 1].strip(".,!?")
                            break
            
            # Extract person name for lead enrichment
            if "research" in user_lower and ("person" in user_lower or "recruiter" in user_lower or "engineer" in user_lower):
                # Simple extraction - get name after "research"
                if "research" in user_lower:
                    parts = user_input.split("research", 1)
                    if len(parts) > 1:
                        name_part = parts[1].strip()
                        # Extract name (simple approach)
                        initial_state["lead_name"] = name_part.split("at")[0].strip() if "at" in name_part else name_part
                        if "at" in name_part:
                            initial_state["lead_company"] = name_part.split("at")[1].strip()
            
            # Run the workflow
            print("\n🔄 Processing...")
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
            import traceback
            traceback.print_exc()
            continue
