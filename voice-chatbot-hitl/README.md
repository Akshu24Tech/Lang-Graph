# Voice-Enabled Chatbot with HITL 🎤

An intelligent conversational AI chatbot built with LangGraph, featuring **Human-in-the-Loop (HITL)** approval workflow and **Deepgram voice integration**.

## 🚀 Key Features

### 🎤 Voice Integration (Powered by Deepgram)
- **Voice Input**: Speak to the chatbot instead of typing
- **Voice Output**: AI responses converted to natural speech
- **Voice Commands**: Control HITL approval with voice ("approve", "reject", "read")
- **Multiple Voice Models**: Choose from 10+ different voices (male/female)
- **Real-time Processing**: Low-latency speech-to-text and text-to-speech

### 👤 Human-in-the-Loop (HITL)
- **Response Review**: All AI responses require human approval before delivery
- **Edit Responses**: Modify AI responses before sending
- **Voice Approval**: Use voice commands for hands-free approval
- **Rejection Handling**: Regenerate responses when rejected
- **Feedback Collection**: Collect human feedback for improvement

### 💬 Enhanced Chat Experience
- **Persistent Conversations**: Maintain chat history across sessions
- **Audio Playback**: Play any message as audio
- **Voice Commands**: Control the interface with voice
- **Real-time Interface**: Streamlit-based responsive UI
- **Session Management**: Clear chat, view statistics

## 🏗️ Architecture

Built using the same LangGraph patterns from your existing codebase:

### Workflow Nodes:
1. **Chat Node**: Generates AI responses using OpenAI GPT
2. **Human Review Node**: HITL approval with voice commands
3. **Response Delivery Node**: Delivers approved responses with optional audio

### Workflow Flow:
```
User Input → AI Response → 👤 Human Review → Approved Response → User
                              ↑
                         Voice Commands
                         Audio Preview
```

## 🛠️ Setup

### 1. Install Dependencies
```bash
cd voice-chatbot-hitl
pip install -r requirements.txt
```

### 2. Configure API Keys
The `.env` file is already configured with your keys:
```env
# OpenAI API Key
OPENAI_API_KEY=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

# Deepgram API Key (for voice features)
DEEPGRAM_API_KEY=4d5f51e7be5f3bc361ecfb80c2f8a6099d3f85f5
```

### 3. Run the Application

**Streamlit Interface (Recommended):**
```bash
streamlit run streamlit_voice_chatbot.py
```

**Command Line Interface:**
```bash
python app.py
```

## 🎯 Usage

### Voice Features:
1. **Voice Input**: Click the microphone button to speak your message
2. **Voice Commands**: During HITL review, say:
   - "Approve" → Approve the response
   - "Reject" → Reject and regenerate
   - "Read" → Play audio preview
3. **Audio Responses**: Click 🔊 to hear any message as speech

### HITL Workflow:
1. Type or speak your message
2. AI generates a response
3. **Review Required**: Response appears for approval
4. **Options**:
   - ✅ Approve: Send response to chat
   - ❌ Reject: Generate new response
   - ✏️ Edit: Modify before approval
   - 🔊 Preview: Hear response as audio
   - 🎤 Voice Command: Use voice to approve/reject

### Voice Models Available:
- **Female**: aura-asteria-en, aura-luna-en, aura-stella-en, aura-athena-en, aura-hera-en
- **Male**: aura-orion-en, aura-arcas-en, aura-perseus-en, aura-angus-en, aura-orpheus-en

## 📁 Project Structure

```
voice-chatbot-hitl/
├── app.py                      # CLI interface with HITL
├── streamlit_voice_chatbot.py  # Streamlit web interface
├── state.py                    # Chat state management
├── nodes.py                    # LangGraph workflow nodes
├── voice_integration.py        # Deepgram voice integration
├── requirements.txt            # Dependencies
├── .env                       # API keys (configured)
└── README.md                  # This file
```

## 🔧 Features Inherited from Your Codebase

### From `chatbot-in-langgraph-main/`:
1. **LangGraph StateGraph Architecture** - Workflow orchestration
2. **Message Management** - Chat history and state handling
3. **Streamlit Patterns** - UI components and session management
4. **Error Handling** - Graceful error recovery

### From `x-post-agent/`:
1. **HITL Implementation** - Human approval workflow
2. **Voice Integration** - Deepgram TTS/STT functionality
3. **State Management** - Complex state with reducers
4. **Conditional Workflows** - Smart routing based on approval

## 🎤 Voice Commands Reference

### During HITL Review:
- **"Approve"** / **"Yes"** / **"Accept"** → Approve response
- **"Reject"** / **"No"** / **"Try again"** → Reject response
- **"Read"** / **"Play"** / **"Listen"** → Audio preview
- **"Edit"** / **"Modify"** → Enter edit mode

### General Chat:
- Use the microphone button for voice input
- All text can be converted to speech
- Voice commands work in real-time

## 🔒 Safety & Privacy

- **Human Oversight**: All AI responses reviewed before delivery
- **Voice Processing**: Audio processed securely via Deepgram API
- **No Storage**: Voice data not stored locally
- **API Security**: Secure API key management
- **Error Handling**: Graceful fallbacks when voice features fail

## 🚀 Advanced Features

### Customization Options:
- **Voice Model Selection**: Choose preferred voice
- **Auto-play Responses**: Automatically play AI responses
- **HITL Toggle**: Enable/disable human review
- **Session Management**: Clear chat, view statistics

### Integration Ready:
- **Database Storage**: Easy to add conversation persistence
- **User Authentication**: Ready for multi-user deployment
- **Analytics**: Track approval rates and voice usage
- **Custom Commands**: Extend voice command vocabulary

## 🎯 Use Cases

1. **Accessibility**: Voice interface for users with disabilities
2. **Hands-free Operation**: Voice-controlled chat for busy environments
3. **Quality Control**: HITL ensures high-quality responses
4. **Audio Content**: Generate audio versions of conversations
5. **Training**: Human feedback improves AI responses over time

This chatbot combines the best of both worlds: the conversational AI capabilities from your existing chatbot with the advanced HITL and voice features from the X Post Agent, creating a comprehensive voice-enabled assistant with human oversight.