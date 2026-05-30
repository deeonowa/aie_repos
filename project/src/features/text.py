
import re


def clean_description(text: str, max_length: int = 8000) -> str:
    text = str(text).strip()
    text = re.sub(r"\s+", " ", text)
    return text[:max_length]
