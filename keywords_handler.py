
KEYWORDS_FILE = 'keywords.txt'

def load_keywords():
    try:
        with open(KEYWORDS_FILE, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def save_keywords(keywords):
    with open(KEYWORDS_FILE, 'w', encoding='utf-8') as f:
        for keyword in keywords:
            f.write(f"{keyword}\n")
