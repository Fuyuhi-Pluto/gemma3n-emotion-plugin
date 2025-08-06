# backend/storage.py
import json
import os
from datetime import datetime

DATA_PATH = "./data/mood_log.json"

def save_mood_entry(input_text, mood, response, multi_moods=None, highlight_keywords=None, intensity=None):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "input": input_text,
        "mood": mood,
        "response": response,
        "multi_moods": multi_moods or [],
        "highlight_keywords": highlight_keywords or [],
        "intensity": intensity if intensity is not None else 0
    }

    if not os.path.exists(DATA_PATH):
        with open(DATA_PATH, "w") as f:
            json.dump([entry], f, ensure_ascii=False, indent=2)
    else:
        with open(DATA_PATH, "r+", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
            data.append(entry)
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.truncate()

def get_mood_history():
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def export_history(records, format="csv"):
    if format == "csv":
        import io, csv
        fieldnames = ["timestamp", "input", "mood", "response", "multi_moods", "highlight_keywords", "intensity"]
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in records:
            # 多标签和高亮词转为字符串
            row = row.copy()
            row["multi_moods"] = ",".join(row.get("multi_moods", []))
            row["highlight_keywords"] = ",".join(row.get("highlight_keywords", []))
            writer.writerow(row)
        return output.getvalue()
    # 可扩展为PDF等
    return ""
