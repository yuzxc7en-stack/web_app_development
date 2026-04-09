# 賽特選房系統 — 系統架構文件 (Architecture)

> **相關文件**：[產品需求文件 (PRD)](PRD.md)
> **狀態**：初版設計

---

## 1. 技術架構說明

為了快速驗證 MVP 範圍並降低初期開發成本，我們選擇基於 Python 生態系的輕量級開發堆疊，採用**傳統後端渲染（Server-Side Rendering, SSR）為主，輔以輕量級 JavaScript Ajax 請求**的模式，這非常適合非重度互動的後台管理介面以及資料呈現型系統。

### 技術選型
* **後端框架：Python + Flask**
  * **原因**：極度輕量、具有高彈性。對於一個包含自動抓取、資料運算（計算停損與勝率評分）的服務而言，Python 原生具備強大的資料處理能力。
* **資料庫：SQLite (搭配 SQLAlchemy 或內建 sqlite3)**
  * **原因**：不需要額外安裝與維護獨立的資料庫伺服器 (如 MySQL, Postgres)。資料直接儲存於本地檔案 (`database.db`)，不僅便於開發，也很適合本項目「可能裝在個人電腦或無伺服器小主機」的預期部署環境。
* **模板引擎：Jinja2**
  * **原因**：Flask 原生內建。負責產生包含動態數據的 HTML 頁面，無須進行複雜的前後端分離 API 設計與串接，可以節省大量的開發時間。
* **前端展示：HTML / Vanilla CSS / Vanilla JavaScript**
  * **原因**：因為專案核心在「後端演算法與自動操作」，前端介面我們採用最單純的網頁三劍客，不再疊加 Vue 或 React 帶來複雜的打包設定 (Webpack / Vite)。

### Flask MVC 模式說明
* **Model (資料模型)**：負責定義 SQLite 中的資料表結構（如用戶設定、房間盤口紀錄、操作日誌），以及寫入與查詢資料的邏輯。
* **View (視圖)**：這裡指的是由 `Jinja2` 渲染出來的 HTML 模板與夾帶的 CSS/JS。它的職責是「呈現從 Controller 處理好傳送過來的最終數據」與「接收使用者點擊操作」。
* **Controller (控制器)**：在 Flask 中即是 `app.route(...)` 路由函式。負責接收前端的請求、轉交給對應 Model 判斷業務邏輯（停損計算、推薦給分）、提取資料，最後告訴 View 渲染哪個頁面並回傳。

---

## 2. 專案資料夾結構

整個專案將按照 Flask 的標準藍圖（Blueprints）或模組化結構組織，保持高內聚低耦合，方便後續擴張。

```text
web_app_development/
├── app/                  ← 應用程式主目錄
│   ├── __init__.py       ← 常規初始化、註冊 db 與 routes
│   ├── models/           ← 資料庫模型 (Model)
│   │   └── schema.py     ← 定義 User, Room, Log, Settings 表結構
│   ├── routes/           ← 所有的 Flask 路由控制器 (Controller)
│   │   ├── auth.py       ← 負責帳號登入/登出
│   │   ├── dashboard.py  ← 負責主控台介面與智能選房清單
│   │   └── api.py        ← 提供給前端 JS 呼叫的輕量 API (例如：取得快爆預警)
│   ├── static/           ← 靜態資源檔案
│   │   ├── css/
│   │   │   └── style.css ← 系統主樣式 (Vanilla CSS 提供介面風格)
│   │   └── js/
│   │       └── main.js   ← 處理頁面互動、或是快爆通知的 polling (輪詢)
│   └── templates/        ← Jinja2 HTML 模板 (View)
│       ├── base.html     ← 共用版型 (Header, Sidebar, Navbar)
│       ├── login.html    ← 登入頁
│       └── index.html    ← 系統首頁 (Dashboard)
├── instance/
│   └── database.db       ← 開發與運行環境自動產生的 SQLite 資料庫
├── docs/                 ← 系統說明與設計文件
│   ├── PRD.md            ← 產品需求文件
│   └── ARCHITECTURE.md   ← 系統架構文件 (本文件)
├── requirements.txt      ← 專案依賴的 Python 套件清單
└── app.py                ← 專案啟動入口 (主流程)
```

---

## 3. 元件關係圖

以下展示使用者從瀏覽器發送請求後，系統內部的資料與流程走向：

```mermaid
graph TD
    Client[瀏覽器 (HTML/JS/CSS)]
    
    subgraph "Flask Web Server應用程式層"
        Router[Flask Route (Controller)]
        Template[Jinja2 Template (View)]
        Algorithm[策略與運算邏輯 (停損/勝率)]
        Model[ORM / Database Models]
    end
    
    DB[(SQLite 資料庫)]
    
    Client -- "1. 點擊介面 / HTTP 連線設定" --> Router
    Router -- "2. 呼叫內部運算" --> Algorithm
    Algorithm -- "3. 讀寫數據" --> Model
    Model -- "4. SQL Query" --> DB
    DB -- "5. 返回查詢實體" --> Model
    Model -- "6. 包裝為物件" --> Algorithm
    Algorithm -- "7. 回傳結果" --> Router
    Router -- "8. 將資料與頁面綁定" --> Template
    Template -- "9. 編譯後回傳 HTML" --> Client
    Client -. "10. AJAX 定期取得快爆預估 (JSON)" .-> Router
```

---

## 4. 關鍵設計決策

1. **單體後端渲染為主，局部採用 Ajax：**
   * **原因**：大部分介面操作（修改目標、停損設定）不需要頻繁即時更新，採用 Jinja2 直接帶資料吐出 HTML 能夠快速完成 MVP。唯獨【功能五：快爆分時提前通知】需要每秒獲取最新警報，針對該功能，前端使用 JavaScript `setInterval()` 結合 Fetch Api，定時向後端 `api.py` 獲取輕量資料。這可以在不導入繁重的 WebSocket 的前提下，滿足小於 5 秒的刷新需求。

2. **採用 SQLite 作為唯一的資料持久層：**
   * **原因**：因為此系統可能會作為玩家私密掛機程式、代操者的工具，需要能獨立地單機運行（本機執行），而無需強制部署於龐雜的雲端資料庫架構。只要備份了 `instance/database.db` 檔案，所有的資金規劃與操作日誌即可完美還原。

3. **Append-Only 操作日誌保證不可篡改性：**
   * **原因**：為了貫徹 PRD 中「穩定出金」、「嚴格風控」的系統目標，當遭遇虧損或停損鎖定時，所有的「變更設定」和「下注預測」都會被寫入 Log 資料表。程式層面不提供 Delete 路由，以確保代操紀錄透明或未來策略回測時不會遺失數據。

4. **分離【內部API】與【網頁渲染】的路由機制：**
   * **原因**：雖然尚未全分離，但把 `api.py` 獨立於 `dashboard.py`，能確保未來如果要引入外部機器人 (如傳送快爆預警到 LINE / Discord webhook)、或是決定升級成全 Ajax 操作時，有一個乾淨的 JSON 數據層可以對接。
