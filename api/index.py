import os
import random
from flask import Flask, jsonify, render_template_string, request
import requests

app = Flask(__name__)

# Open Library 官方建議在 User-Agent 附上聯絡信箱（也可在 Vercel 環境變數設定 CONTACT_EMAIL）
CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "0a0qaqtt@gmail.com")
USER_AGENT = f"BookGachaMachine/1.0 ({CONTACT_EMAIL})"

# 扭蛋主題清單
SUBJECTS = [
    {"id": "random", "label": "🎲 隨機驚喜"},
    {"id": "science_fiction", "label": "🚀 科幻"},
    {"id": "mystery", "label": "🔍 推理懸疑"},
    {"id": "fantasy", "label": "🧙 奇幻冒險"},
    {"id": "psychology", "label": "🧠 心理學"},
    {"id": "history", "label": "🏛️ 歷史"},
    {"id": "travel", "label": "✈️ 旅遊"},
    {"id": "philosophy", "label": "💡 哲學"},
]

VALID_SUBJECT_IDS = [s["id"] for s in SUBJECTS if s["id"] != "random"]
SUBJECT_LABELS = {s["id"]: s["label"] for s in SUBJECTS}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>靈感選書扭蛋機</title>
  <style>
    :root {
      --bg: #fdfaf5;
      --card: #ffffff;
      --ink: #2c2a29;
      --muted: #6f6a66;
      --accent: #e06d53;
      --accent-dark: #c4563d;
      --border: #ebe4dc;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Noto Sans TC", "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
      line-height: 1.6;
    }
    .container {
      max-width: 760px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }
    header {
      text-align: center;
      margin-bottom: 28px;
    }
    h1 {
      margin: 0 0 8px;
      font-size: 2rem;
      letter-spacing: 0.04em;
    }
    .subtitle {
      margin: 0;
      color: var(--muted);
      font-size: 0.95rem;
    }
    .panel {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 24px;
      box-shadow: 0 8px 24px rgba(44, 42, 41, 0.05);
      margin-bottom: 24px;
    }
    .subjects {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: center;
      margin-bottom: 22px;
    }
    .subject-btn {
      border: 1px solid var(--border);
      background: #faf6f0;
      color: var(--ink);
      padding: 8px 14px;
      border-radius: 999px;
      cursor: pointer;
      font-size: 0.92rem;
      transition: all 0.18s ease;
    }
    .subject-btn:hover { border-color: var(--accent); }
    .subject-btn.active {
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
      font-weight: 600;
    }
    .gacha-action {
      text-align: center;
    }
    .draw-btn {
      background: var(--accent);
      color: #fff;
      border: none;
      padding: 14px 32px;
      border-radius: 999px;
      font-size: 1.05rem;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 6px 16px rgba(224, 109, 83, 0.28);
      transition: transform 0.15s ease, background 0.15s ease;
    }
    .draw-btn:hover:not(:disabled) {
      background: var(--accent-dark);
      transform: translateY(-1px);
    }
    .draw-btn:disabled {
      opacity: 0.65;
      cursor: not-allowed;
    }
    .capsule {
      display: inline-block;
      font-size: 2.2rem;
      margin-bottom: 8px;
    }
    .shaking {
      animation: shake 0.45s infinite;
    }
    @keyframes shake {
      0%, 100% { transform: rotate(0deg); }
      25% { transform: rotate(-14deg); }
      75% { transform: rotate(14deg); }
    }
    .error-box {
      display: none;
      background: #fff2f0;
      border: 1px solid #ffccc7;
      color: #a8071a;
      padding: 14px 16px;
      border-radius: 12px;
      margin-top: 16px;
      text-align: center;
    }
    .result-card {
      display: none;
      gap: 22px;
      align-items: flex-start;
    }
    .result-card.show {
      display: flex;
    }
    .cover-wrap {
      flex: 0 0 150px;
      width: 150px;
      height: 220px;
      border-radius: 10px;
      overflow: hidden;
      background: #f2ece4;
      border: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 10px;
      color: var(--muted);
      font-size: 0.85rem;
    }
    .cover-wrap img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }
    .book-info { flex: 1; min-width: 0; }
    .badge {
      display: inline-block;
      font-size: 0.8rem;
      background: #f5efe6;
      color: var(--accent-dark);
      padding: 3px 10px;
      border-radius: 999px;
      margin-bottom: 8px;
      font-weight: 600;
    }
    .book-title {
      margin: 0 0 6px;
      font-size: 1.35rem;
      line-height: 1.35;
    }
    .book-meta {
      margin: 0 0 12px;
      color: var(--muted);
      font-size: 0.92rem;
    }
    .tags {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 16px;
    }
    .tag {
      font-size: 0.78rem;
      background: #f3f1ee;
      color: #555;
      padding: 3px 9px;
      border-radius: 6px;
    }
    .card-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .link-btn, .save-btn {
      padding: 8px 14px;
      border-radius: 10px;
      font-size: 0.9rem;
      text-decoration: none;
      cursor: pointer;
      border: 1px solid var(--border);
      background: #fff;
      color: var(--ink);
    }
    .link-btn:hover, .save-btn:hover { border-color: var(--accent); color: var(--accent-dark); }
    .history-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }
    .history-header h2 { margin: 0; font-size: 1.1rem; }
    .clear-btn {
      background: none;
      border: none;
      color: var(--muted);
      cursor: pointer;
      font-size: 0.85rem;
      text-decoration: underline;
    }
    .history-list {
      list-style: none;
      padding: 0;
      margin: 0;
      display: grid;
      gap: 10px;
    }
    .history-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      padding: 10px 12px;
      background: #faf7f2;
      border-radius: 10px;
      font-size: 0.9rem;
    }
    .history-item a {
      color: var(--ink);
      text-decoration: none;
      font-weight: 600;
    }
    .history-item a:hover { text-decoration: underline; }
    .del-btn {
      background: none;
      border: none;
      color: #999;
      cursor: pointer;
      font-size: 0.85rem;
    }
    .empty-tip { color: var(--muted); font-size: 0.9rem; margin: 0; }
    footer {
      text-align: center;
      color: var(--muted);
      font-size: 0.85rem;
      margin-top: 24px;
    }
    footer a { color: var(--accent-dark); }
    @media (max-width: 600px) {
      .result-card.show { flex-direction: column; align-items: center; text-align: center; }
      .tags, .card-actions { justify-content: center; }
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>📚 靈感選書扭蛋機</h1>
      <p class="subtitle">選一個主題，轉出下一本帶給你靈感的書</p>
    </header>

    <section class="panel">
      <div class="subjects" id="subjectList">
        {% for s in subjects %}
          <button type="button" class="subject-btn {% if loop.first %}active{% endif %}" data-id="{{ s.id }}">
            {{ s.label }}
          </button>
        {% endfor %}
      </div>

      <div class="gacha-action">
        <div id="capsuleIcon" class="capsule">💊</div>
        <div>
          <button type="button" id="drawBtn" class="draw-btn">轉一顆扭蛋</button>
        </div>
      </div>

      <div id="errorBox" class="error-box"></div>
    </section>

    <section id="resultPanel" class="panel result-card">
      <div id="coverWrap" class="cover-wrap">無封面圖片</div>
      <div class="book-info">
        <span id="bookSubject" class="badge"></span>
        <h2 id="bookTitle" class="book-title"></h2>
        <p id="bookMeta" class="book-meta"></p>
        <div id="bookTags" class="tags"></div>
        <div class="card-actions">
          <a id="bookLink" class="link-btn" href="#" target="_blank" rel="noopener noreferrer">前往 Open Library 查看</a>
          <button type="button" id="saveBtn" class="save-btn">⭐ 收藏這本書</button>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="history-header">
        <h2>🗂️ 我的收藏與抽書紀錄（最多 10 筆）</h2>
        <button type="button" id="clearHistoryBtn" class="clear-btn">清空紀錄</button>
      </div>
      <ul id="historyList" class="history-list"></ul>
      <p id="emptyTip" class="empty-tip">目前還沒有收藏紀錄，轉一顆扭蛋並點「收藏這本書」試試看吧！</p>
    </section>

    <footer>
      書籍資料來源：<a href="https://openlibrary.org/" target="_blank" rel="noopener noreferrer">Open Library</a>
    </footer>
  </div>

  <script>
    const STORAGE_KEY = "book_gacha_favorites_v1";
    let selectedSubject = "random";
    let currentBook = null;

    const subjectBtns = document.querySelectorAll(".subject-btn");
    const drawBtn = document.getElementById("drawBtn");
    const capsuleIcon = document.getElementById("capsuleIcon");
    const errorBox = document.getElementById("errorBox");
    const resultPanel = document.getElementById("resultPanel");
    const coverWrap = document.getElementById("coverWrap");
    const bookSubject = document.getElementById("bookSubject");
    const bookTitle = document.getElementById("bookTitle");
    const bookMeta = document.getElementById("bookMeta");
    const bookTags = document.getElementById("bookTags");
    const bookLink = document.getElementById("bookLink");
    const saveBtn = document.getElementById("saveBtn");
    const historyList = document.getElementById("historyList");
    const emptyTip = document.getElementById("emptyTip");
    const clearHistoryBtn = document.getElementById("clearHistoryBtn");

    subjectBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        subjectBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        selectedSubject = btn.dataset.id;
      });
    });

    async function drawBook() {
      errorBox.style.display = "none";
      drawBtn.disabled = true;
      drawBtn.textContent = "扭蛋轉動中...";
      capsuleIcon.classList.add("shaking");

      try {
        const res = await fetch(`/api/gacha?subject=${encodeURIComponent(selectedSubject)}`);
        const data = await res.json();
        if (!res.ok || data.error) {
          throw new Error(data.error || "無法取得書籍資料，請稍後再試。");
        }
        currentBook = data;
        renderBook(data);
        drawBtn.textContent = "再轉一次";
      } catch (err) {
        errorBox.textContent = err.message || "連線逾時或發生錯誤，請再試一次。";
        errorBox.style.display = "block";
        drawBtn.textContent = "重新再轉一次";
      } finally {
        drawBtn.disabled = false;
        capsuleIcon.classList.remove("shaking");
      }
    }

    function renderBook(book) {
      bookSubject.textContent = book.subject_label;
      bookTitle.textContent = book.title;
      const yearText = book.first_publish_year ? `・首次出版：${book.first_publish_year}` : "";
      bookMeta.textContent = `作者：${book.authors}${yearText}`;
      bookLink.href = book.openlibrary_url;

      bookTags.innerHTML = "";
      (book.tags || []).forEach(tag => {
        const span = document.createElement("span");
        span.className = "tag";
        span.textContent = tag;
        bookTags.appendChild(span);
      });

      coverWrap.innerHTML = "";
      if (book.cover_url) {
        const img = document.createElement("img");
        img.src = book.cover_url;
        img.alt = book.title;
        img.onerror = () => { coverWrap.textContent = "📖 " + book.title; };
        coverWrap.appendChild(img);
      } else {
        coverWrap.textContent = "📖 " + book.title;
      }

      resultPanel.classList.add("show");
    }

    function loadHistory() {
      try {
        return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
      } catch {
        return [];
      }
    }

    function saveHistory(items) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(items.slice(0, 10)));
      renderHistory();
    }

    function renderHistory() {
      const items = loadHistory();
      historyList.innerHTML = "";
      emptyTip.style.display = items.length ? "none" : "block";

      items.forEach((item, index) => {
        const li = document.createElement("li");
        li.className = "history-item";
        li.innerHTML = `
          <div>
            <a href="${item.openlibrary_url}" target="_blank" rel="noopener noreferrer">${item.title}</a>
            <div style="font-size:0.8rem;color:#6f6a66;">${item.authors}・${item.subject_label}</div>
          </div>
          <button type="button" class="del-btn" data-idx="${index}">刪除</button>
        `;
        historyList.appendChild(li);
      });

      document.querySelectorAll(".del-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          const idx = Number(btn.dataset.idx);
          const items = loadHistory();
          items.splice(idx, 1);
          saveHistory(items);
        });
      });
    }

    saveBtn.addEventListener("click", () => {
      if (!currentBook) return;
      const items = loadHistory().filter(i => i.openlibrary_url !== currentBook.openlibrary_url);
      items.unshift(currentBook);
      saveHistory(items);
    });

    clearHistoryBtn.addEventListener("click", () => {
      localStorage.removeItem(STORAGE_KEY);
      renderHistory();
    });

    drawBtn.addEventListener("click", drawBook);
    renderHistory();
  </script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE, subjects=SUBJECTS)


@app.route("/api/gacha")
def gacha():
    requested = request.args.get("subject", "random").strip().lower()
    chosen_subject = (
        requested if requested in VALID_SUBJECT_IDS else random.choice(VALID_SUBJECT_IDS)
    )

    url = f"https://openlibrary.org/subjects/{chosen_subject}.json"
    try:
        resp = requests.get(
            url,
            params={"limit": 30},
            headers={"User-Agent": USER_AGENT},
            timeout=5,
        )
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException:
        return (
            jsonify({"error": "連線至 Open Library 逾時或失敗，請稍後再試。"}),
            502,
        )

    works = payload.get("works") or []
    if not works:
        return jsonify({"error": "這個主題目前沒有可抽選的書籍，請換個主題試試。"}), 404

    book = random.choice(works)
    authors_list = [a.get("name") for a in book.get("authors", []) if a.get("name")]
    cover_id = book.get("cover_id")
    key = book.get("key", "")

    result = {
        "title": book.get("title", "未命名書籍"),
        "authors": ", ".join(authors_list) if authors_list else "未知作者",
        "first_publish_year": book.get("first_publish_year"),
        "tags": (book.get("subject") or [])[:3],
        "cover_url": f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None,
        "openlibrary_url": f"https://openlibrary.org{key}" if key else "https://openlibrary.org/",
        "subject_label": SUBJECT_LABELS.get(chosen_subject, chosen_subject),
    }

    response = jsonify(result)
    response.headers["Cache-Control"] = "no-store"
    return response
