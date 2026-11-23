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
