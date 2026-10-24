"""
FastAPI backend for the Voice Chatbot with HITL & Memory.

Reuses your existing src/core/nodes.py logic (remember_node, chat_node) UNCHANGED.
human_review_node's blocking input() is replaced by real HTTP endpoints (/chat, /approve).

Identity: memory now follows a real account (email + password), not a random
per-browser id, so the same person gets the same memory on any device.
Requires DATABASE_URL — same Postgres connection your LTM store already uses.
"""

import base64
import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

# --- Reusing your existing, unmodified logic ---
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.core.nodes import remember_node, chat_node
from src.integrations.db_config import get_ltm_store
from src.integrations.voice_integration import voice_integration
from src.integrations.tavily_integration import (
    create_internship_hunter,
    create_company_researcher,
    create_lead_enricher,
    create_news_monitor,
    create_general_search,
)
from backend.auth import init_users_table, create_user, authenticate_user, create_token, get_current_user_id

app = FastAPI(title="Voice Chatbot HITL API")

# In production, set FRONTEND_ORIGIN to your deployed Vercel URL
# (e.g. https://your-app.vercel.app) instead of leaving this as "*".
allowed_origins = [os.getenv("FRONTEND_ORIGIN", "*")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LTM store: Postgres if DATABASE_URL is set, else in-memory (same as app.py)
ltm_store = get_ltm_store()

# Users table for login/signup — same Postgres DB as LTM
init_users_table()

# Tavily is optional — only wire up if TAVILY_API_KEY is set
try:
    internship_hunter = create_internship_hunter()
    company_researcher = create_company_researcher()
    lead_enricher = create_lead_enricher()
    news_monitor = create_news_monitor()
    general_search = create_general_search()
    TAVILY_AVAILABLE = True
except ValueError:
    TAVILY_AVAILABLE = False


# --- Session state ---
# Keyed by the authenticated user_id (e.g. "user_42"), NOT by a per-browser random id.
# This is what makes memory follow the account across any device/browser.
sessions: dict[str, dict] = {}


def get_session(user_id: str) -> dict:
    if user_id not in sessions:
        sessions[user_id] = {"messages": [], "pending_response": None}
    return sessions[user_id]


def get_stored_memory_texts(user_id: str) -> set[str]:
    """Read current LTM facts for this user, same namespace remember_node uses."""
    namespace = ("user", user_id, "details")
    items = ltm_store.search(namespace)
    return {it.value.get("data", "") for it in items if it.value.get("data")}


# --- Tavily intent routing (mirrors app_with_tavily.py's CLI keyword parsing) ---

def detect_tavily_intent(message: str) -> tuple[str, dict]:
    """Return (route, params). route is 'none' if no web-search intent is detected."""
    lower = message.lower()

    if "internship" in lower:
        return "internship", {"role": "AI/ML"}

    if "news" in lower:
        return "news", {}

    if "research" in lower and "company" in lower:
        words = message.split()
        company = None
        for i, w in enumerate(words):
            if w.lower() in ("research", "company") and i + 1 < len(words):
                company = words[i + 1].strip(".,!?")
                break
        return "company", {"company": company or ""}

    if "research" in lower and any(k in lower for k in ("person", "recruiter", "engineer")):
        parts = message.split("research", 1)
        name_part = parts[1].strip() if len(parts) > 1 else ""
        name = name_part.split(" at ")[0].strip() if " at " in name_part else name_part
        company = name_part.split(" at ")[1].strip() if " at " in name_part else None
        return "lead", {"name": name, "company": company}

    # General fallback — makes Tavily usable for any query, not just the 4 fixed flows.
    general_triggers = (
        "search for", "look up", "google", "search the web",
        "what's the latest", "what is the latest", "current price",
        "who is the current", "what's happening with", "find out about",
    )
    if any(trigger in lower for trigger in general_triggers):
        return "general", {"query": message}

    return "none", {}


def format_tavily_results(route: str, data: dict) -> str:
    if route == "internship":
        items = data.get("results", [])[:5]
        lines = [f"- {r.get('title', 'Untitled')}: {r.get('url', '')}" for r in items]
        return "Recent internship listings found:\n" + "\n".join(lines) if lines else "No internship listings found."

    if route == "news":
        items = data.get("news_items", [])[:5]
        lines = [f"- {r.get('title', 'Untitled')}: {r.get('url', '')}" for r in items]
        return "Today's AI/ML news:\n" + "\n".join(lines) if lines else "No news found."

    if route == "company":
        report = data.get("report", {})
        text = report.get("answer") or str(report)[:1200]
        return f"Research on {data.get('company', '')}:\n{text}"

    if route == "lead":
        items = data.get("recent_activity", [])[:5]
        lines = [f"- {r.get('title', 'Untitled')}: {r.get('url', '')}" for r in items]
        return f"Recent activity for {data.get('name', '')}:\n" + "\n".join(lines) if lines else "No recent activity found."

    if route == "general":
        items = data.get("results", [])[:5]
        lines = [f"- {r.get('title', 'Untitled')}: {r.get('content', '')[:200]} ({r.get('url', '')})" for r in items]
        return "Web search results:\n" + "\n".join(lines) if lines else "No results found."

    return ""


def run_tavily_route(route: str, params: dict) -> dict:
    if route == "internship":
        return internship_hunter.find_internships(role=params.get("role", "AI/ML"))
    if route == "news":
        return news_monitor.get_daily_brief()
    if route == "company":
        return company_researcher.research_company(params.get("company", ""))
    if route == "lead":
        return lead_enricher.enrich_lead(params.get("name", ""), company=params.get("company"))
    if route == "general":
        return general_search.quick_search(params.get("query", ""))
    return {}


# --- Auth schemas & endpoints ---

class AuthRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user_id: str


@app.post("/auth/signup", response_model=AuthResponse)
def signup(req: AuthRequest):
    if len(req.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters.")
    try:
        user_id = create_user(req.email, req.password)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return AuthResponse(token=create_token(user_id), user_id=user_id)


@app.post("/auth/login", response_model=AuthResponse)
def login(req: AuthRequest):
    try:
        user_id = authenticate_user(req.email, req.password)
    except ValueError as e:
        raise HTTPException(401, str(e))
    return AuthResponse(token=create_token(user_id), user_id=user_id)


# --- Chat schemas ---

class ChatRequest(BaseModel):
    message: str
    voice_enabled: bool = False
    selected_voice: str = "aura-asteria-en"
    human_review_enabled: bool = True


class ChatResponse(BaseModel):
    status: str  # "pending" (needs approval) or "delivered" (review was off)
    pending_response: Optional[str] = None
    final_response: Optional[str] = None
    audio_base64: Optional[str] = None
    new_memories: list[str] = []
    used_web_search: bool = False


class ApproveRequest(BaseModel):
    approved: bool
    feedback: Optional[str] = None  # required if approved=False
    voice_enabled: bool = False
    selected_voice: str = "aura-asteria-en"


class ApproveResponse(BaseModel):
    status: str  # "delivered" or "regenerated"
    final_response: Optional[str] = None
    pending_response: Optional[str] = None
    audio_base64: Optional[str] = None


# --- Endpoints (all require a valid Bearer token) ---

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, user_id: str = Depends(get_current_user_id)):
    session = get_session(user_id)
    session["messages"].append(HumanMessage(content=req.message))

    used_web_search = False
    generation_messages = session["messages"]
    if TAVILY_AVAILABLE:
        route, params = detect_tavily_intent(req.message)
        if route != "none":
            try:
                raw_results = run_tavily_route(route, params)
                context = format_tavily_results(route, raw_results)
                # Augmented content is used for generation only, never saved into
                # session history, so memory extraction sees only the plain message.
                generation_messages = session["messages"][:-1] + [
                    HumanMessage(content=f"{req.message}\n\n[Web search results]\n{context}")
                ]
                used_web_search = True
            except Exception as e:
                print(f"Tavily route '{route}' failed: {e}")

    state = {
        "messages": generation_messages,
        "thread_id": user_id,
        "pending_response": None,
        "improvement_request": None,
        "human_feedback": None,
    }
    config = {"configurable": {"user_id": user_id}}

    before = get_stored_memory_texts(user_id)
    remember_node(state, config=config, store=ltm_store)
    result = chat_node(state, config=config, store=ltm_store)
    after = get_stored_memory_texts(user_id)
    new_memories = list(after - before)

    session["pending_response"] = result["pending_response"]
    session["messages"] = session["messages"] + result["messages"][-1:]

    if not req.human_review_enabled:
        pending = session["pending_response"]
        session["pending_response"] = None
        audio_b64 = None
        if req.voice_enabled and voice_integration.is_available():
            audio_bytes = voice_integration.text_to_speech(pending, req.selected_voice)
            if audio_bytes:
                audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return ChatResponse(
            status="delivered",
            final_response=pending,
            audio_base64=audio_b64,
            new_memories=new_memories,
            used_web_search=used_web_search,
        )

    return ChatResponse(
        status="pending",
        pending_response=result["pending_response"],
        new_memories=new_memories,
        used_web_search=used_web_search,
    )


@app.post("/approve", response_model=ApproveResponse)
def approve(req: ApproveRequest, user_id: str = Depends(get_current_user_id)):
    session = get_session(user_id)
    pending = session.get("pending_response")
    if not pending:
        raise HTTPException(400, "No pending response for this user")

    if req.approved:
        audio_b64 = None
        if req.voice_enabled and voice_integration.is_available():
            audio_bytes = voice_integration.text_to_speech(pending, req.selected_voice)
            if audio_bytes:
                audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        session["pending_response"] = None
        return ApproveResponse(status="delivered", final_response=pending, audio_base64=audio_b64)

    if not req.feedback:
        raise HTTPException(400, "feedback is required when approved=False")

    improved_prompt = (
        f"Previous answer: {pending}\n\n"
        f"User feedback: {req.feedback}\n\n"
        f"Please improve the answer based on this feedback."
    )
    state = {
        "messages": session["messages"],
        "thread_id": user_id,
        "improvement_request": improved_prompt,
        "human_feedback": req.feedback,
    }
    config = {"configurable": {"user_id": user_id}}
    result = chat_node(state, config=config, store=ltm_store)

    session["pending_response"] = result["pending_response"]
    session["messages"] = session["messages"] + result["messages"]

    return ApproveResponse(status="regenerated", pending_response=result["pending_response"])


@app.get("/health")
def health():
    return {"status": "ok"}


# Mount static frontend so http://localhost:8000 opens the app directly
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")