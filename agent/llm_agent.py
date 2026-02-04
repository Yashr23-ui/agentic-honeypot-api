import os
from dotenv import load_dotenv

load_dotenv()

SAFE_FALLBACK_REPLY = "I received this message suddenly. Can you explain more?"

SYSTEM_PROMPT = (
    "You are a normal person receiving a suspicious message. "
    "You are not a security expert. "
    "You do not accuse anyone. "
    "You sound confused but cooperative. "
    "You ask simple clarification questions. "
    "Never reveal that you suspect a scam."
)

def generate_reply(user_message: str) -> str:
    # ---------- OpenAI (optional) ----------
    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            max_tokens=50,
            temperature=0.6
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print("⚠️ OpenAI failed:", e)

    # ---------- Gemini (CONFIRMED MODEL) ----------
    try:
        from google import genai

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=SYSTEM_PROMPT + "\nMessage: " + user_message
        )

        return response.text.strip()

    except Exception as e:
        print("⚠️ Gemini failed:", e)

    # ---------- Final fallback ----------
    return SAFE_FALLBACK_REPLY
