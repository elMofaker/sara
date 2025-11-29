import json
import os
from config import   PROCESSED_FILE
import openpyxl
from datetime import datetime

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


EXCEL_FILE = "facebook_posts.xlsx"

def save_to_excel(link, text):
    """
    دالة لحفظ رابط البوست والنص وتوقيت الحفظ في ملف إكسيل.
    """
    try:
   
        if not os.path.exists(EXCEL_FILE):
             
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Posts"
            ws.append(["Date", "Post Link", "Post Text"])  
        else:
          
            wb = openpyxl.load_workbook(EXCEL_FILE)
            ws = wb.active

     
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
       
        safe_text = str(text).replace('\x00', '') 

  
        ws.append([date_now, link, safe_text])

   
        wb.save(EXCEL_FILE)
        print(f"📝 تم حفظ البوست في الإكسيل: {link}")

    except Exception as e:
        print(f"❌ خطأ أثناء الحفظ في الإكسيل: {e}")