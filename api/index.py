"""靈感選書扭蛋機 Flask 應用程式（Vercel Serverless 入口）。"""

import random
import time
from threading import Lock

import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# 請將此信箱改成方便 Open Library 聯絡的信箱；也可用環境變數覆寫。
CONTACT_EMAIL = "your-email@example.com"
USER_AGENT = f"BookGachaMachine/1.0 ({CONTACT_EMAIL})"
API_TIMEOUT_SECONDS = 5
CACHE_SECONDS = 300

SUBJECTS = {
    "science_fiction": "🚀 科幻",
    "mystery": "🔍 推理懸疑",
    "fantasy": "🧙 奇幻冒險",
    "psychology": "🧠 心理學",
    "history": "🏛️ 歷史",
    "travel": "✈️ 旅遊",
    "philosophy": "💡 哲學",
}

# 只在單一 Serverless 執行個體內快取短時間，避免短時間重複查詢。
_cache = {}
_cache_lock = Lock()


def get_subject_books(subject):
    """取得並短暫快取主題書單；外部 API 失敗時交由呼叫端處理。"""
    now = time.monotonic()
    with _cache_lock:
        cached = _cache.get(subject)
        if cached and now - cached[0] < CACHE_SECONDS:
            return cached[1]

    response = requests.get(
        f"https://openlibrary.org/subjects/{subject}.json",
        params={"limit": 30},
        headers={"User-Agent": USER_AGENT},
        timeout=API_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    works = response.json().get("works", [])
    with _cache_lock:
        _cache[subject] = (now, works)
    return works


@app.get("/")
def home():
    return render_template("index.html", subjects=SUBJECTS)


@app.post("/api/draw")
def draw_book():
    """抽出一本 Open Library 回傳的書，並將失敗轉成友善 JSON。"""
    payload = request.get_json(silent=True) or {}
    subject = payload.get("subject", "random")
    if subject == "random":
        subject = random.choice(list(SUBJECTS))
    if subject not in SUBJECTS:
        return jsonify(error="這個主題目前不存在，請重新選擇。"), 400

    try:
        works = get_subject_books(subject)
    except (requests.RequestException, ValueError, TypeError):
        app.logger.exception("Open Library 查詢失敗：%s", subject)
        return jsonify(error="暫時無法取得書籍資料，請稍後再試一次。"), 502

    if not works:
        return jsonify(error="這個主題暫時沒有找到書籍，換個主題再試試吧。"), 404

    book = random.choice(works)
    return jsonify(
        book={
            "key": book.get("key", ""),
            "title": book.get("title") or "未提供書名",
            "authors": [author.get("name", "") for author in book.get("authors", []) if author.get("name")],
            "first_publish_year": book.get("first_publish_year"),
            "subjects": (book.get("subject") or [])[:3],
            "cover_id": book.get("cover_id"),
            "cover_url": f"https://covers.openlibrary.org/b/id/{book['cover_id']}-L.jpg" if book.get("cover_id") else None,
            "subject": subject,
            "subject_label": SUBJECTS[subject],
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
