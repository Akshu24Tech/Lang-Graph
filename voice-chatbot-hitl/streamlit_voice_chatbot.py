import streamlit as st
import uuid
from audio_recorder_streamlit import audio_recorder
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from state import ChatState
from nodes import chat_node, remember_node
from voice_integration import voice_integration
from db_config import get_ltm_store

# Initialize STM (Short Term Memory) and LTM (Long Term Memory)
if "checkpointer" not in st.session_state:
    st.session_state.checkpointer = InMemorySaver()
if "ltm_store" not in st.session_state:
    # Uses PostgreSQL if DATABASE_URL is set, otherwise falls back to InMemoryStore
    st.session_state.ltm_store = get_ltm_store()

# Create a simple graph for Streamlit: remember -> chat
if "chat_graph" not in st.session_state:
    builder = StateGraph(ChatState)
    builder.add_node("remember", remember_node)
    builder.add_node("chat", chat_node)
    builder.add_edge(START, "remember")
    builder.add_edge("remember", "chat")
    builder.add_edge("chat", END)
    st.session_state.chat_graph = builder.compile(
        checkpointer=st.session_state.checkpointer,
        store=st.session_state.ltm_store
    )

st.set_page_config(page_title="Voice Chatbot with HITL", page_icon="🎤", layout="wide")

def generate_session_id():
    return str(uuid.uuid4())

def initialize_session_state():
    if "session_id" not in st.session_state:
        st.session_state.session_id = generate_session_id()
    if "user_id" not in st.session_state:
        # User ID for LTM (Long Term Memory) - persists across sessions
        # You can change this to identify different users
        st.session_state.user_id = "default_user"
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_response" not in st.session_state:
        st.session_state.pending_response = None
    if "awaiting_approval" not in st.session_state:
        st.session_state.awaiting_approval = False
    if "voice_enabled" not in st.session_state:
        st.session_state.voice_enabled = voice_integration.is_available()
    if "show_feedback_form" not in st.session_state:
        st.session_state.show_feedback_form = False
    if "user_improvement_feedback" not in st.session_state:
        st.session_state.user_improvement_feedback = None
    if "needs_regeneration" not in st.session_state:
        st.session_state.needs_regeneration = False
    if "message_audios" not in st.session_state:
        st.session_state.message_audios = {}
    if "pending_audio" not in st.session_state:
        st.session_state.pending_audio = None
    if "audio_generation_counter" not in st.session_state:
        st.session_state.audio_generation_counter = 0

initialize_session_state()

# Header
st.title("🎤 Voice-Enabled Chatbot with HITL")
st.markdown("### AI Assistant with Human Review & Voice Integration")

# Voice status indicator
if st.session_state.voice_enabled:
    st.success("🎤 Voice features enabled! You can use voice commands and audio responses.")
else:
    st.warning("⚠️ Voice features disabled. Check your Deepgram API key to enable voice functionality.")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Voice settings
    if st.session_state.voice_enabled:
        st.subheader("🎤 Voice Settings")
        
        voice_model = st.selectbox(
            "Voice Model",
            options=[
                "aura-asteria-en",  # Natural female voice
                "aura-luna-en",     # Warm female voice
                "aura-stella-en",   # Confident female voice
                "aura-athena-en",   # Authoritative female voice
                "aura-hera-en",     # Expressive female voice
                "aura-orion-en",    # Deep male voice
                "aura-arcas-en",    # Smooth male voice
                "aura-perseus-en",  # Strong male voice
                "aura-angus-en",    # Friendly male voice
                "aura-orpheus-en"   # Melodic male voice
            ],
            index=0,
            help="Choose the voice for audio responses"
        )
        st.session_state.selected_voice = voice_model
        
        auto_play_responses = st.checkbox(
            "Auto-play AI responses",
            value=False,
            help="Automatically play audio for AI responses"
        )
    
    st.divider()
    
    # HITL settings
    st.subheader("👤 HITL Settings")
    
    hitl_enabled = st.checkbox(
        "Enable Human Review",
        value=True,
        help="Require human approval before showing AI responses"
    )
    
    st.divider()
    
    # Session management
    st.subheader("💬 Session")
    
    # User ID for LTM (can be changed to switch users)
    user_id = st.text_input(
        "User ID (for memory)",
        value=st.session_state.user_id,
        help="This identifies you for long-term memory. Change to switch users."
    )
    st.session_state.user_id = user_id
    
    if st.button("🔄 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_response = None
        st.session_state.awaiting_approval = False
        st.session_state.show_feedback_form = False
        st.session_state.user_improvement_feedback = None
        st.session_state.needs_regeneration = False
        st.session_state.message_audios = {}
        st.session_state.pending_audio = None
        st.rerun()
    
    # Chat statistics
    st.metric("Messages", len(st.session_state.messages))

# Main chat interface
st.subheader("💬 Chat")

# Display chat messages
chat_container = st.container()
with chat_container:
    for i, message in enumerate(st.session_state.messages):
        if isinstance(message, HumanMessage) or (isinstance(message, dict) and message.get("role") == "user"):
            content = message.content if hasattr(message, 'content') else message.get("content", "")
            with st.chat_message("user"):
                st.write(content)
        elif isinstance(message, AIMessage) or (isinstance(message, dict) and message.get("role") == "assistant"):
            content = message.content if hasattr(message, 'content') else message.get("content", "")
            with st.chat_message("assistant"):
                st.write(content)
                
                # Add audio playbook for AI responses
                if st.session_state.voice_enabled:
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        # Create unique audio key for each message
                        message_id = f"msg_{i}_{abs(hash(content))}"
                        button_key = f"play_btn_{message_id}"
                        
                        if st.button(f"🔊 Play", key=button_key):
                            with st.spinner("Generating speech..."):
                                try:
                                    audio_bytes = voice_integration.text_to_speech(content, st.session_state.selected_voice)
                                    if audio_bytes:
                                        st.session_state.message_audios[message_id] = audio_bytes
                                        st.session_state.audio_generation_counter += 1
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Audio generation failed: {str(e)}")
                    
                    # Display audio if available for this specific message
                    message_id = f"msg_{i}_{abs(hash(content))}"
                    if message_id in st.session_state.message_audios:
                        with col2:
                            try:
                                st.audio(st.session_state.message_audios[message_id], format="audio/mp3")
                                clear_key = f"clear_btn_{message_id}"
                                if st.button("❌ Clear Audio", key=clear_key):
                                    if message_id in st.session_state.message_audios:
                                        del st.session_state.message_audios[message_id]
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Audio playback error: {str(e)}")
                                # Clean up corrupted audio
                                if message_id in st.session_state.message_audios:
                                    del st.session_state.message_audios[message_id]

# Pending response review (Simplified HITL)
if st.session_state.awaiting_approval and st.session_state.pending_response:
    st.divider()
    st.subheader("👤 Are you happy with this result?")
    
    with st.container():
        # Display pending response
        with st.chat_message("assistant"):
            st.write(st.session_state.pending_response)
        
        # Voice preview
        if st.session_state.voice_enabled:
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("🔊 Listen", use_container_width=True, key="listen_pending_response"):
                    with st.spinner("Generating speech..."):
                        try:
                            audio_bytes = voice_integration.text_to_speech(
                                st.session_state.pending_response, 
                                st.session_state.selected_voice
                            )
                            if audio_bytes:
                                st.session_state.pending_audio = audio_bytes
                                st.rerun()
                        except Exception as e:
                            st.error(f"Audio generation failed: {str(e)}")
            
            # Display pending audio if available
            if st.session_state.pending_audio:
                with col2:
                    try:
                        st.audio(st.session_state.pending_audio, format="audio/mp3")
                        if st.button("❌ Clear", key="clear_pending_audio"):
                            st.session_state.pending_audio = None
                            st.rerun()
                    except Exception as e:
                        st.error(f"Audio playback error: {str(e)}")
                        st.session_state.pending_audio = None
        
        st.divider()
        
        # Simple happiness check
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("😊 Yes, I'm happy with this!", use_container_width=True, type="primary", key="approve_response"):
                # Add approved response to chat
                st.session_state.messages.append(AIMessage(content=st.session_state.pending_response))
                st.session_state.pending_response = None
                st.session_state.awaiting_approval = False
                st.success("✅ Response approved!")
                st.rerun()
        
        with col2:
            if st.button("😐 No, I want changes", use_container_width=True, key="request_changes"):
                st.session_state.show_feedback_form = True
                st.rerun()
        
        # Feedback form for improvements
        if st.session_state.get('show_feedback_form', False):
            st.divider()
            st.markdown("**💭 What would you like to change or add to the answer?**")
            
            feedback = st.text_area(
                "Your feedback:",
                placeholder="e.g., 'Add more examples', 'Make it shorter', 'Explain in simpler terms', 'Include recent data'...",
                height=100,
                key="user_feedback_input"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Regenerate with feedback", use_container_width=True, type="primary", key="regenerate_with_feedback"):
                    if feedback.strip():
                        # Store feedback for regeneration
                        st.session_state.user_improvement_feedback = feedback
                        st.session_state.pending_response = None
                        st.session_state.awaiting_approval = False
                        st.session_state.show_feedback_form = False
                        st.session_state.needs_regeneration = True
                        st.info("🔄 Regenerating response with your feedback...")
                        st.rerun()
                    else:
                        st.warning("Please provide feedback for improvement")
            
            with col2:
                if st.button("❌ Cancel", use_container_width=True, key="cancel_feedback"):
                    st.session_state.show_feedback_form = False
                    st.rerun()
        
            # Voice command section
            if st.session_state.voice_enabled:
                st.divider()
                st.markdown("**🎤 Voice Commands**")
                st.caption("Say 'yes' to approve or 'no' to request changes")
                
                # Use a unique key for voice commands to prevent conflicts
                voice_command_key = f"voice_cmd_{st.session_state.audio_generation_counter}"
                
                audio_bytes = audio_recorder(
                    text="Voice Command",
                    recording_color="#e74c3c",
                    neutral_color="#34495e",
                    icon_name="microphone",
                    icon_size="1x",
                    key=voice_command_key
                )
                
                if audio_bytes:
                    with st.spinner("Processing voice command..."):
                        try:
                            transcript = voice_integration.speech_to_text(audio_bytes, "audio/wav")
                            
                            if transcript:
                                st.write(f"🎯 Heard: \"{transcript}\"")
                                
                                # Simple voice command processing
                                transcript_lower = transcript.lower()
                                
                                if any(word in transcript_lower for word in ['yes', 'good', 'approve', 'happy', 'fine', 'ok']):
                                    st.session_state.messages.append(AIMessage(content=st.session_state.pending_response))
                                    st.session_state.pending_response = None
                                    st.session_state.awaiting_approval = False
                                    st.success("✅ Voice approved!")
                                    st.rerun()
                                elif any(word in transcript_lower for word in ['no', 'change', 'improve', 'different', 'better']):
                                    st.session_state.show_feedback_form = True
                                    st.info("💭 Please provide feedback for improvement")
                                    st.rerun()
                                elif any(word in transcript_lower for word in ['read', 'play', 'listen', 'hear']):
                                    st.info("🔊 Playing audio...")
                                    try:
                                        audio_bytes = voice_integration.text_to_speech(
                                            st.session_state.pending_response, 
                                            st.session_state.selected_voice
                                        )
                                        if audio_bytes:
                                            st.audio(audio_bytes, format="audio/mp3")
                                    except Exception as e:
                                        st.error(f"Audio generation failed: {str(e)}")
                                else:
                                    st.warning(f"❓ Command not recognized. Say 'yes' to approve or 'no' to request changes.")
                            else:
                                st.error("❌ Could not understand voice command")
                        except Exception as e:
                            st.error(f"Voice processing error: {str(e)}")

# Chat input
if not st.session_state.awaiting_approval:
    st.divider()
    
    # Text input
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.chat_input("Type your message here...")
    
    # Voice input
    if st.session_state.voice_enabled:
        with col2:
            st.markdown("**🎤 Voice Input**")
            
            # Use a unique key for voice input to prevent conflicts
            voice_input_key = f"voice_input_{st.session_state.audio_generation_counter}"
            
            audio_bytes = audio_recorder(
                text="Record",
                recording_color="#e74c3c",
                neutral_color="#34495e",
                icon_name="microphone",
                icon_size="1x",
                key=voice_input_key
            )
            
            if audio_bytes:
                with st.spinner("Converting speech to text..."):
                    try:
                        transcript = voice_integration.speech_to_text(audio_bytes, "audio/wav")
                        if transcript:
                            user_input = transcript
                            st.success(f"🎤 Voice input: \"{transcript}\"")
                    except Exception as e:
                        st.error(f"Speech recognition failed: {str(e)}")
    
    # Process user input
    if user_input:
        # Add user message to chat
        st.session_state.messages.append(HumanMessage(content=user_input))
        
        # Generate AI response
        with st.spinner("AI is thinking..."):
            # Create state for processing
            current_state = {
                "messages": st.session_state.messages,
                "pending_response": None,
                "human_approval": None,
                "approved_responses": [],
                "rejected_responses": [],
                "human_feedback": None,
                "improvement_request": None,
                "voice_enabled": st.session_state.voice_enabled,
                "selected_voice": st.session_state.selected_voice,
                "audio_responses": [],
                "thread_id": st.session_state.session_id,
                "user_preferences": {}
            }
            
            # Check if this is a regeneration with feedback
            if st.session_state.needs_regeneration and st.session_state.user_improvement_feedback:
                # Create improvement request
                improvement_request = f"Previous answer: {st.session_state.pending_response}\n\nUser feedback: {st.session_state.user_improvement_feedback}\n\nPlease improve the answer based on this feedback."
                current_state["improvement_request"] = improvement_request
                current_state["human_feedback"] = st.session_state.user_improvement_feedback
                
                # Reset flags
                st.session_state.needs_regeneration = False
                st.session_state.user_improvement_feedback = None
            
            # Generate response using graph (includes remember node for LTM)
            config = {
                "configurable": {
                    "thread_id": st.session_state.session_id,
                    "user_id": st.session_state.user_id
                }
            }
            result = st.session_state.chat_graph.invoke(current_state, config)
            
            if result.get("pending_response"):
                st.session_state.pending_response = result["pending_response"]
                
                if hitl_enabled:
                    st.session_state.awaiting_approval = True
                else:
                    # Auto-approve if HITL is disabled
                    st.session_state.messages.append(AIMessage(content=result["pending_response"]))
                    st.session_state.pending_response = None
        
        st.rerun()
    
    # Handle regeneration with feedback (when no new user input)
    elif st.session_state.needs_regeneration and st.session_state.user_improvement_feedback:
        with st.spinner("Improving response based on your feedback..."):
            # Create state for regeneration
            current_state = {
                "messages": st.session_state.messages,
                "pending_response": None,
                "human_approval": None,
                "approved_responses": [],
                "rejected_responses": [],
                "human_feedback": st.session_state.user_improvement_feedback,
                "improvement_request": f"Previous answer: {st.session_state.pending_response}\n\nUser feedback: {st.session_state.user_improvement_feedback}\n\nPlease improve the answer based on this feedback.",
                "voice_enabled": st.session_state.voice_enabled,
                "selected_voice": st.session_state.selected_voice,
                "audio_responses": [],
                "thread_id": st.session_state.session_id,
                "user_preferences": {}
            }
            
            # Generate improved response using graph (includes remember node for LTM)
            config = {
                "configurable": {
                    "thread_id": st.session_state.session_id,
                    "user_id": st.session_state.user_id
                }
            }
            result = st.session_state.chat_graph.invoke(current_state, config)
            
            if result.get("pending_response"):
                st.session_state.pending_response = result["pending_response"]
                st.session_state.awaiting_approval = True
            
            # Reset flags
            st.session_state.needs_regeneration = False
            st.session_state.user_improvement_feedback = None
        
        st.rerun()

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>🎤 Voice-Powered Chatbot | 👤 Human-in-the-Loop | 🤖 AI Assistant</p>
    <p><small>Built with LangGraph & Deepgram | Voice Commands & Audio Responses</small></p>
</div>
""", unsafe_allow_html=True)
