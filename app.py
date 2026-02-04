import os
import pickle
from dotenv import load_dotenv

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import List

from agent.llm_agent import generate_reply
from utils.intelligence_extractor import extract_intelligence
from utils.guvi_callback import send_guvi_callback

# ---------------- Load ENV ----------------
load_dotenv()

# ---------------- In-Memory Stores ----------------
SESSION_INTELLIGENCE = {}
SESSION_CONVERSATIONS = {}

# ---------------- App Init ----------------
app = FastAPI(title="Agentic Honeypot API")

# ---------------- Absolute Paths ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "ml", "scam_model.pkl")
VECTORIZER_PATH = os.path.join(BASE_DIR, "ml", "vectorizer.pkl")

# ---------------- Load ML ----------------
with open(MODEL_PATH, "rb") as f:
    scam_model = pickle.load(f)

with open(VECTORIZER_PATH, "rb") as f:
    vectorizer = pickle.load(f)

# ---------------- Data Models ----------------
class Message(BaseModel):
    sender: str
    text: str

class HoneypotRequest(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: List[Message] = []

# ---------------- Scam Detection ----------------
def detect_scam_ml(text: str) -> float:
    X = vectorizer.transform([text])
    return scam_model.predict_proba(X)[0][1]

# ---------------- Domain Keywords ----------------
BANKING_KEYWORDS = [
    "bank", "account", "blocked", "block",
    "verify", "verification",
    "upi", "otp", "kyc",
    "suspend", "suspension",
    "urgent", "immediately",
    "alert", "warning"
]

def banking_keyword_score(text: str) -> int:
    text = text.lower()
    return sum(1 for w in BANKING_KEYWORDS if w in text)

# ---------------- Honeypot Endpoint (SUBMISSION ENDPOINT) ----------------
@app.post("/honeypot")
def honeypot(
    data: HoneypotRequest,
    x_api_key: str = Header(None)
):
    # ---- API KEY AUTH (MANDATORY) ----
    if x_api_key != os.getenv("HONEYPOT_API_KEY"):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )

    ml_score = detect_scam_ml(data.message.text)
    keyword_hits = banking_keyword_score(data.message.text)

    scam_detected = (ml_score > 0.3) or (keyword_hits >= 2)

    # ---- Agent Reply ----
    reply = (
        generate_reply(data.message.text)
        if scam_detected
        else "Okay, thanks."
    )

    # ---- Store Conversation ----
    SESSION_CONVERSATIONS.setdefault(data.sessionId, []).append({
        "sender": data.message.sender,
        "text": data.message.text
    })

    SESSION_CONVERSATIONS[data.sessionId].append({
        "sender": "honeypot",
        "text": reply
    })

    # ---- Intelligence Extraction ----
    extracted_intelligence = {}

    if scam_detected:
        extracted_intelligence = extract_intelligence(data.message.text)

        SESSION_INTELLIGENCE.setdefault(data.sessionId, []).append({
            "message": data.message.text,
            "extracted": extracted_intelligence
        })

    return {
        "status": "success",
        "scamDetected": scam_detected,
        "mlScore": round(ml_score, 3),
        "bankingKeywordHits": keyword_hits,
        "reply": reply,
        "extractedIntelligence": extracted_intelligence
    }

# ---------------- Session Summary (INTERNAL) ----------------
@app.get("/session/{session_id}")
def get_session_summary(session_id: str):
    session_data = SESSION_INTELLIGENCE.get(session_id)

    if not session_data:
        return {
            "status": "not_found",
            "message": "No intelligence found for this session ID."
        }

    phones, upi_ids, urls = set(), set(), set()

    for entry in session_data:
        extracted = entry.get("extracted", {})
        phones.update(extracted.get("phoneNumbers", []))
        upi_ids.update(extracted.get("upiIds", []))
        urls.update(extracted.get("urls", []))

    return {
        "status": "success",
        "sessionId": session_id,
        "totalMessages": len(session_data),
        "conversationHistory": SESSION_CONVERSATIONS.get(session_id, []),
        "aggregatedIntelligence": {
            "phoneNumbers": list(phones),
            "upiIds": list(upi_ids),
            "urls": list(urls)
        },
        "messageLog": session_data
    }

# ---------------- Final GUVI Callback (INTERNAL) ----------------
@app.post("/finalize/{session_id}")
def finalize_session(session_id: str):
    session_data = SESSION_INTELLIGENCE.get(session_id)

    if not session_data:
        return {
            "status": "not_found",
            "message": "No intelligence available for this session."
        }

    phones, upi_ids, urls = set(), set(), set()

    for entry in session_data:
        extracted = entry.get("extracted", {})
        phones.update(extracted.get("phoneNumbers", []))
        upi_ids.update(extracted.get("upiIds", []))
        urls.update(extracted.get("urls", []))

    payload = {
        "sessionId": session_id,
        "scamDetected": True,
        "extractedIntelligence": {
            "phoneNumbers": list(phones),
            "upiIds": list(upi_ids),
            "urls": list(urls)
        },
        "conversationHistory": SESSION_CONVERSATIONS.get(session_id, [])
    }

    callback_result = send_guvi_callback(payload)

    return {
        "status": "success",
        "submittedPayload": payload,
        "callbackResult": callback_result
    }
