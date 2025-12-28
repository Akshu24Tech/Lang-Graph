# 🎙️ Voice-Enabled Chatbot & LangGraph Engineering Hub

Welcome! This repository is a comprehensive look at building production-grade AI Agents. It transitions from **fundamental LangGraph research** to a **fully integrated Voice-Enabled Assistant**.

---

## 📂 Repository Structure

| Folder | Focus | Key Concepts Covered |
| --- | --- | --- |
| **[🚀 voice-chatbot-hitl (Main Project)](https://www.google.com/search?q=./voice-chatbot-hitl/)** | **Integration & UI** | LangGraph + Deepgram + Streamlit + Human-in-the-Loop |
| **[🧠 learning-material](https://www.google.com/search?q=./learning-material/)** | **Core Logic** | State Reducers, Conditional Edges, Checkpoints, & Nodes |

---

## 🧠 The LangGraph Learning Lab (Folder 1)

*Inside: [`/learning-material*`](https://www.google.com/search?q=./learning-material/)

Before building the final application, I broke down the **LangGraph** framework into modular experiments. This folder contains individual files for each milestone:

* **Simple Chains to Graphs:** Transitioning from linear chains to cyclic graphs.
* **State Management:** Deep dive into `Annotated` types and state reducers to handle message history.
* **Conditional Logic:** Implementing routers that decide the next step based on AI output.
* **Persistence & Checkpoints:** How to save a conversation state so an agent can "remember" after a restart.
* **Human-in-the-Loop (HITL):** Implementing the `interrupt` and `approval` logic that powers the final project.

---

## 🚀 The Final Project: Voice Chatbot (Folder 2)

*Inside: [`/voice-chatbot-hitl*`](https://www.google.com/search?q=./voice-chatbot-hitl/)

This is the culmination of the concepts practiced in the lab. It takes the robust LangGraph logic and wraps it in a **Voice-First** interface.

### **Technical Stack:**

* **Orchestration:** LangGraph (Stateful Multi-Actor applications)
* **Voice AI:** Deepgram Nova-2 (STT) & Aura (TTS)
* **Interface:** Streamlit
* **LLM:** OpenAI GPT models

👉 **[Explore the Full Project README](https://www.google.com/search?q=./voice-chatbot-hitl/)** for installation steps and architectural diagrams.

---

## 🛠️ Skills Demonstrated

* **Agentic Workflows:** Designing complex AI logic that isn't just a simple prompt-response.
* **HITL Design:** Creating systems where humans can intercept and correct AI behavior.
* **Multimodal AI:** Integrating voice and text for better accessibility.

---

## 🤝 Connect with Me

**Akshu Grewal** *AI/ML Enthusiast & Agentic AI Developer* [akshug2004@gmail.com]

---

*This repository serves as a portfolio of my growth in building reliable, stateful AI agents.*

---*
