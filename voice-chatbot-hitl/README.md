# 🎤 Voice-Enabled Chatbot with Human-in-the-Loop & Web Intelligence

An intelligent, voice-first chatbot assistant combining **FastAPI**, **LangGraph workflows**, **Deepgram voice technology**, **Tavily search intelligence**, and a **Human-in-the-Loop (HITL)** review gate. 

This version features **Account Authentication**, allowing your long-term memories to securely follow your profile across different browsers and devices.

---

## 🌟 Key Features

* **🗣️ Voice-First Experience**: Transcribe speech in real-time (Deepgram Nova-2) and hear bot replies read aloud using premium text-to-speech (Deepgram Aura).
* **👤 Human-in-the-Loop (HITL)**: Rest easy knowing the AI won't hallucinate. Approve or request adjustments to replies before they are delivered to the chat.
* **🔐 Secure Account-Based Memory (LTM)**: Long-term memory is linked directly to your email/password credentials (`bcrypt` + `pyjwt` Bearer token auth). Sign up once, and retrieve your memories from any device.
* **🌐 Tavily Search Intelligence**: Performs target web research **only when needed**:
  * **Internships**: Finds active AI/ML internships.
  * **Company Research**: Performs deep-dives into company news and info.
  * **Lead Enrichment**: Pulls up recent background and posts of a person.
  * **News Monitor**: Summarizes latest AI/ML news briefs.
  * **General Search**: Dynamic Google-like search for real-time facts.

---

## 🏗️ Architecture & Design

```mermaid
flowchart TD
    subgraph Frontend [Browser Client]
        A[Login / Sign Up Screen] -->|JWT Token Auth| B[Chat Interface]
        B -->|Voice Input| STT[Deepgram Nova-2 STT]
        STT -->|Transcribed Prompt| C[POST /chat Request]
        B -->|Text Input| C
        
        C -->|HTTP Response| D{Review Toggle?}
        D -->|Enabled: status='pending'| Gate[HITL Gate: Approve / Reject]
        Gate -->|Approve| Approve[POST /approve: approved=True]
        Gate -->|Reject + Feedback| Reject[POST /approve: approved=False + Feedback]
        D -->|Disabled: status='delivered'| Delivery[Display Message + Play TTS Audio]
        Approve --> Delivery
        Reject --> C
    end

    subgraph Backend [FastAPI Server / Render]
        C --> Auth[JWT Token Validator]
        Auth -->|Read user_id| Intent{Tavily Search Intent?}
        Intent -->|Yes: Matches Intent| Tavily[Tavily Search Run]
        Tavily -->|Inject Context| LGraph[LangGraph State Workflow]
        Intent -->|No| LGraph
        
        subgraph LangGraph State Workflow [LangGraph State Workflow]
            LGraph --> Remember[Remember Node: Extract & Save LTM]
            Remember --> Chat[Chat Node: Generate Response with LTM]
        end
    end

    subgraph Storage [Database / Render]
        Auth <--> UsersDB[(Users Credentials Table)]
        Remember <--> LTMStore[(LTM Store: PostgresStore)]
        Chat <-- Fetch User Memory --> LTMStore
    end
```

---

## 📁 Repository Structure

```
voice-chatbot-hitl/
├── backend/
│   ├── __init__.py         # Makes backend folder a proper Python package
│   ├── auth.py             # User signup/login logic, password hashing, JWT security
│   └── main.py             # FastAPI App, CORS, intent classification, and API routes
├── frontend/
│   ├── index.html          # Dynamic UI featuring Auth portals, chat log, and audio players
│   └── vercel.json         # Static routing config for Vercel
├── src/
│   ├── core/
│   │   ├── nodes.py        # LangGraph nodes (Chat, Remember)
│   │   └── state.py        # Conversation state structure
│   ├── integrations/
│   │   ├── db_config.py    # Database connection manager (Postgres/InMemory Store fallback)
│   │   ├── voice_integration.py   # Deepgram TTS & STT processing
│   │   └── tavily_integration.py  # Tavily API endpoints & search models
│   └── utils/
│       └── memory_utils.py # Long-term memory utility functions
├── render.yaml             # Render Blueprint specification (one-click deployment)
├── requirements.txt        # Backend dependencies
└── .env                    # Environment keys (ignored by git - never commit this!)
```

---

## 🚀 Local Development

### 1. Prerequisites
Install all required libraries locally:
```bash
pip install -r requirements.txt fastapi uvicorn bcrypt pyjwt
```

### 2. Configure Environment (`.env`)
Create a `.env` file at the root of the project with your API keys:
```env
GOOGLE_API_KEY=your_gemini_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
TAVILY_API_KEY=your_tavily_api_key (optional)
JWT_SECRET_KEY=some-long-random-string-for-security
DATABASE_URL=postgresql://user:password@localhost:5442/postgres?sslmode=disable (optional)
```
*Note: If no `DATABASE_URL` is configured, login/signup features will prompt you to configure Postgres. Memory will automatically fallback to InMemoryStore.*

### 3. Run the Server
```bash
uvicorn backend.main:app --reload --port 8000
```
Verify the server is running by opening `http://localhost:8000/health`.

### 4. Chat!
Open [frontend/index.html](file:///E:/Ghost%20OS/projects/Lang-Graph/voice-chatbot-hitl/frontend/index.html) in your browser. Register a new account or sign in to start chatting with persistent memory!

---

## 🌐 Tavily Intent Triggers (On-Demand Search)

To prevent unwanted API queries, Tavily web searches are strictly triggered by action-oriented phrasing:
* **Internships**: *"Find AI/ML internships"* or *"search for internships"*
* **News**: *"What is the latest news about Google?"* or *"news today"*
* **Company**: *"Research company NVIDIA"* or *"profile company Anthropic"*
* **Lead Enrichment**: *"Enrich lead Sam Altman at OpenAI"*
* **General Search**: *"Google current price of Bitcoin"* or *"search the web for X"*

---

## ☁️ Going Live (Production Deployment)

### 1. Deploy the Backend on Render
FastAPI + LangGraph + Postgres require a persistent connection, which is best served on Render.
1. Push your repository to your GitHub account.
2. In Render: **New → Blueprint**, and link this repository.
3. Render reads `render.yaml` and initializes both a **Web Service** and a **Postgres Database** automatically.
4. Input your secrets in the Render dashboard:
   - `GOOGLE_API_KEY`
   - `DEEPGRAM_API_KEY`
   - `JWT_SECRET_KEY`
   - `TAVILY_API_KEY`
5. Note your deployed web service URL (e.g. `https://your-backend.onrender.com`).

### 2. Deploy the Frontend on Vercel
1. Update Vercel's target API URL in `frontend/index.html` line 653:
   ```javascript
   const API = "https://your-backend.onrender.com";
   ```
2. In Vercel: **New Project** → import your repository.
3. **Important**: Set the **Root Directory** to `frontend` in your Vercel project configuration.
4. Select **Other** as the Framework Preset (no build steps).
5. Deploy to receive your live web client URL (`https://your-project.vercel.app`).

### 3. Lock down CORS Security
Once your Vercel URL is live, add it to your Render dashboard as an environment variable:
```env
FRONTEND_ORIGIN=https://your-project.vercel.app
```
Restart your Render service. This locks down your backend so only your official frontend client can request chat processing!