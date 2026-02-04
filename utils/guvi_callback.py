import requests

GUVI_ENDPOINT = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

def send_guvi_callback(payload: dict):
    """
    Sends final honeypot intelligence to GUVI evaluation endpoint.
    """
    try:
        response = requests.post(
            GUVI_ENDPOINT,
            json=payload,
            timeout=5
        )

        return {
            "status": "sent",
            "guviStatusCode": response.status_code
        }

    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }
