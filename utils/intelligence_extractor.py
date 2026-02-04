import re

PHONE_REGEX = r"\b(?:\+91)?[6-9]\d{9}\b"

# Source: https://stackoverflow.com/a/59732766
# Author: Tarun Deep Attri (StackOverflow), CC BY-SA 4.0
UPI_REGEX = r"[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}"

URL_REGEX = r"(https?://\S+|www\.\S+)"

def extract_intelligence(text: str) -> dict:
    phones = re.findall(PHONE_REGEX, text)
    upi_ids = re.findall(UPI_REGEX, text)
    urls = re.findall(URL_REGEX, text)

    return {
        "phoneNumbers": list(set(phones)),
        "upiIds": list(set(upi_ids)),
        "urls": list(set(urls))
    }
