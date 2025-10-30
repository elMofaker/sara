import json
import os
from config import   PROCESSED_FILE

def remove_duplicate_lines(text):
    seen = set()
    unique_lines = []
    for line in text.splitlines():
        line = line.strip()
        if line and line not in seen:
            unique_lines.append(line)
            seen.add(line)
    return "\n".join(unique_lines)

def normalize_text(txt):
    return txt.replace("\n", " ").strip().lower()

def load_processed():
    if os.path.exists(PROCESSED_FILE):
        try:
            with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return set(data.get("links", [])), set(data.get("texts", []))
        except (json.JSONDecodeError, ValueError):
            return set(), set()
    return set(), set()

# (utils.py)
def save_processed(links, texts):
    with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
        # (تصحيح) يجب حفظ النصوص والروابط معاً
        data_to_save = {
            "links": list(links),
            "texts": list(texts)
        }
        json.dump(data_to_save, f, ensure_ascii=False, indent=2)