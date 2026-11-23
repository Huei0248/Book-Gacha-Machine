# 靈感選書扭蛋機

用 Flask、Jinja2 與原生 JavaScript 製作的繁體中文選書小網站。書籍資料來自免 API Key 的 Open Library Subjects API；收藏與最近 10 筆抽書紀錄保存在瀏覽器 localStorage。

## 專案結構

```text
.
├── api/
│   ├── __init__.py
│   └── index.py          # Flask 應用程式及 Vercel Serverless 入口
├── static/
│   ├── app.js            # 抽書互動、收藏與 localStorage 紀錄
│   └── style.css         # 響應式視覺樣式
├── templates/
│   └── index.html        # Jinja2 繁體中文頁面
├── tests/
│   └── test_app.py       # 使用 mock 的路由與抽書測試
├── requirements.txt
├── requirements-dev.txt
└── vercel.json
```

應用程式放在 `api/index.py`，由 Vercel Python Runtime 提供 Serverless Function；`vercel.json` 將所有路徑交給 Flask。應用不寫入本機檔案或使用資料庫。API 的 User-Agent 聯絡信箱請在 `api/index.py` 的 `CONTACT_EMAIL` 常數替換。

## 本機啟動

需要 Python 3.11 或更新版本。

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m flask --app api.index run --debug
```

瀏覽 http://127.0.0.1:5000 。執行測試：

```powershell
python -m pytest -q
```

## 推送到 GitHub

1. 在 GitHub 建立一個空白 repository（不勾選自動建立 README）。
2. 在專案資料夾執行：

```powershell
git init
git add .
git commit -m "Build Book Gacha Machine"
git branch -M main
git remote add origin https://github.com/<你的帳號>/<repository名稱>.git
git push -u origin main
```

若已由本工具完成初始化與第一次 commit，直接設定 `origin` 並執行 push 即可。將網址中的帳號與 repository 名稱換成自己的資料。

## Vercel 匯入部署

1. 登入 Vercel，選擇 **Add New → Project**，連結 GitHub 並匯入 repository。
2. Framework Preset 使用 **Other**；Root Directory 保持專案根目錄。此專案不需要前端建置命令。
3. 確認 Python Runtime 能讀取 `requirements.txt`，按 **Deploy**。
4. 部署完成後開啟 Vercel 提供的網址。之後推送至 GitHub `main` 分支會觸發新部署。

所有 Open Library HTTP 請求都帶有自訂 User-Agent 並設定 5 秒逾時。短期快取只存在目前執行個體的記憶體，Vercel 執行個體重啟時會清空，使用者資料則只在各自瀏覽器保存。
