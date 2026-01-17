from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from api.engine import QuizEngine
import os, json

# --------------------------------------------------
# Base paths (works locally + Render)
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUESTIONS_DIR = os.path.join(BASE_DIR, "questions")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# --------------------------------------------------
# Load Question Banks
# --------------------------------------------------
QUESTION_BANKS = {}

if not os.path.exists(QUESTIONS_DIR):
    raise RuntimeError("Questions directory not found")

for file in os.listdir(QUESTIONS_DIR):
    if file.endswith(".json"):
        path = os.path.join(QUESTIONS_DIR, file)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Support {"questions": [...]}
            if isinstance(data, dict) and "questions" in data:
                data = data["questions"]
            QUESTION_BANKS[file.replace(".json", "")] = data

# --------------------------------------------------
# Quiz Engine
# --------------------------------------------------
quiz_engine = QuizEngine(QUESTION_BANKS)

# --------------------------------------------------
# FastAPI App
# --------------------------------------------------
app = FastAPI(title="Global Quiz App", version="1.0")

# --------------------------------------------------
# CORS
# --------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# API Router
# --------------------------------------------------
api = APIRouter(prefix="/api")

class Answer(BaseModel):
    answer: str

class StartQuizRequest(BaseModel):
    bank: str
    count: int
    start: int = 0
    end: Optional[int] = None
    mode: str = "test"

# ------------------- API ENDPOINTS -------------------
@api.get("/banks")
def get_banks():
    return {"banks": list(QUESTION_BANKS.keys())}

@api.post("/start")
def start_quiz(data: StartQuizRequest):
    if data.mode not in ("test", "study"):
        raise HTTPException(400, "Mode must be 'test' or 'study'")
    if data.bank not in QUESTION_BANKS:
        raise HTTPException(404, f"Bank '{data.bank}' not found")
    session_id = quiz_engine.start_session(data.bank, data.count, data.start, data.end)
    quiz_engine.sessions[session_id]["mode"] = data.mode
    return {"session_id": session_id}

@api.get("/question/{session_id}")
def get_question(session_id: str):
    question = quiz_engine.get_question(session_id)
    if question is None:
        return {"finished": True}
    return question

@api.post("/answer/{session_id}")
def submit_answer(session_id: str, answer: Answer):
    session = quiz_engine.sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    result = quiz_engine.submit_answer(session_id, answer.answer)
    if session["mode"] == "study":
        q = session["questions"][session["index"] - 1]
        result["correct_answer"] = q["options"][q["answer"]]
    return result

@api.post("/end/{session_id}")
def end_quiz(session_id: str):
    result = quiz_engine.end_session(session_id)
    result["message"] = "Quiz ended. You may restart or choose another bank."
    return result

# --------------------------------------------------
# REGISTER API ROUTER FIRST
# --------------------------------------------------
app.include_router(api)

# --------------------------------------------------
# SERVE FRONTEND (MOUNT LAST)
# --------------------------------------------------
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
