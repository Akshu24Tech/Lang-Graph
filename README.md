# 🎙️ Voice-Enabled Chatbot & LangGraph Engineering Hub

Welcome! This repository is a comprehensive look at building production-grade AI Agents. It transitions from **fundamental LangGraph research** to a **fully integrated Voice-Enabled Assistant**.

---

## 📂 Repository Structure

| Folder | Focus | Key Concepts Covered |
| --- | --- | --- |
| **[🚀 voice-chatbot-hitl (Main Project)](https://github.com/Akshu24Tech/Lang-Graph/blob/main/voice-chatbot-hitl/)** | **Integration & UI** | LangGraph + Deepgram + Streamlit + Human-in-the-Loop |
| **[🧠 learning-material](https://github.com/Akshu24Tech/Lang-Graph/blob/main/learning-material/)** | **Core Logic** | State Reducers, Conditional Edges, Checkpoints, & Nodes |

---

## 🧠 The LangGraph Learning Lab (Folder 1)

Inside: [`/learning-material`](https://github.com/Akshu24Tech/Lang-Graph/blob/main/learning-material/)

Before building the final application, I broke down the **LangGraph** framework into modular experiments. This folder contains individual files for each milestone:

* **Simple Chains to Graphs:** Transitioning from linear chains to cyclic graphs.
* **State Management:** Deep dive into `Annotated` types and state reducers to handle message history.
* **Conditional Logic:** Implementing routers that decide the next step based on AI output.
* **Persistence & Checkpoints:** How to save a conversation state so an agent can "remember" after a restart.
* **Human-in-the-Loop (HITL):** Implementing the `interrupt` and `approval` logic that powers the final project.

---

## 🚀 The Final Project: Voice Chatbot (Folder 2)

Inside: [`/voice-chatbot-hitl`](https://github.com/Akshu24Tech/Lang-Graph/blob/main/voice-chatbot-hitl/)

This is the culmination of the concepts practiced in the lab. It takes the robust LangGraph logic and wraps it in a **Voice-First** interface with **advanced memory capabilities**.

### **Technical Stack:**

* **Orchestration:** LangGraph (Stateful Multi-Actor applications)
* **Voice AI:** Deepgram Nova-2 (STT) & Aura (TTS)
* **Interface:** Streamlit
* **LLM:** Google Gemini 2.5 Flash
* **Memory System:** STM (Short Term Memory) + LTM (Long Term Memory)
* **Storage:** PostgreSQL (persistent) or InMemory (development)

### **Key Features:**

* 🗣️ **Voice-First Interface** - Speak naturally, listen to responses
* 👤 **Human-in-the-Loop** - Approve every AI response before delivery
* 🧠 **Dual Memory System**:
  - **STM (Short Term Memory)**: Conversation history per session
  - **LTM (Long Term Memory)**: Persistent user information across sessions
* 💾 **Memory Management**: View, search, and delete stored memories
* 🗄️ **PostgreSQL Integration**: Optional persistent storage for LTM
* 🔄 **Smart Personalization**: AI remembers user preferences and context

👉 **[Explore the Full Project README](https://github.com/Akshu24Tech/Lang-Graph/blob/main/voice-chatbot-hitl/README.md)** for installation steps and architectural diagrams.

---

## 🛠️ Skills Demonstrated

* **Agentic Workflows:** Designing complex AI logic that isn't just a simple prompt-response.
* **HITL Design:** Creating systems where humans can intercept and correct AI behavior.
* **Multimodal AI:** Integrating voice and text for better accessibility.
* **Memory Systems:** Implementing dual memory architecture (STM + LTM) for intelligent personalization.
* **Database Integration:** PostgreSQL integration for persistent memory storage.

---

## 🤝 Connect with Me

**Akshu Grewal** *AI/ML & Agentic AI Developer* [akshug2004@gmail.com]

---
