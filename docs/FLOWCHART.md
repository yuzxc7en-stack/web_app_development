# 賽特選房系統 — 系統流程圖與功能對照

> **相關文件**：[產品需求文件 (PRD)](PRD.md)、[系統架構文件 (ARCHITECTURE.md)](ARCHITECTURE.md)
> **狀態**：初版設計

---

## 1. 使用者流程圖 (User Flow)

此流程圖展示了使用者（玩家／代操者）進入系統後的操作路徑，涵蓋登入、查看推薦房間、設定出金與停損，以及遭遇系統警告或停損鎖定時的流程。

```mermaid
flowchart LR
    A([使用者開啟系統網頁]) --> B{是否已登入？}
    B -->|否| C[登入頁面]
    C -->|輸入帳密| D{驗證成功？}
    D -->|失敗| C
    D -->|成功| E[系統主控台 Dashboard]
    B -->|是| E
    
    E --> F[查看智能選房推薦清單]
    E --> G[接收快爆提前通知彈窗]
    E --> H[設定風控參數]
    
    H --> I[設定每日出金目標]
    H --> J[設定停損點/百分比]
    
    F --> K{執行下注 / 自動操作}
    K --> L[系統監控房間與執行策略]
    L --> M{觸發風控或預警條件?}
    M -->|達成出金目標| N[跳出目標達成提示 / 鎖定今日操作]
    M -->|觸發虧損停損點| O[強制停止操作 / 記錄停損並鎖定]
    M -->|偵測到快爆風險| P[觸發頁面跳窗及音效警告]
    M -->|正常| L
    
    N --> Q([使用者選擇登出結算或修改目標])
    O --> Q
    P --> F
```

## 2. 系統序列圖 (Sequence Diagram)

這裡以「使用者設定停損與出金目標，並啟動系統取得即時快爆預警」為例，展示前端瀏覽器、Flask 後端與 SQLite 之間的資料傳遞時序。

```mermaid
sequenceDiagram
    actor User as 使用者
    participant Browser as 瀏覽器 (JS/Ajax)
    participant Flask as Flask (Controller)
    participant Model as 系統資料庫模型
    participant DB as SQLite
    
    User->>Browser: 在介面輸入停損/出金目標並點選「儲存」
    Browser->>Flask: POST /api/settings (設定參數)
    Flask->>Model: 驗證並建立/更新 UserSettings 實體
    Model->>DB: UPDATE settings_table
    DB-->>Model: 成功寫入
    Model-->>Flask: 儲存成功
    Flask-->>Browser: HTTP 200 OK (JSON)
    Browser->>User: 顯示「設定已儲存」
    
    Note over Browser, Flask: 進入監控與快爆預警輪詢階段
    
    loop 每 5 秒自動輪詢一次
        Browser->>Flask: GET /api/monitor/status
        Flask->>Model: 查詢最新開獎數據與計算評分
        Model->>DB: SELECT records, stats
        DB-->>Flask: 回傳歷史數據
        Flask->>Flask: 運算快爆偏差指標與停損檢核
        
        alt 此輪偵測超越快爆閾值
            Flask-->>Browser: 回傳 JSON { alert: true, msg: "房間A有快爆風險！" }
            Browser->>User: 顯示紅色彈窗與播放警告音效
        else 正常狀況
            Flask-->>Browser: 回傳 JSON { alert: false, data: [房間清單與即時勝率] }
            Browser->>User: 更新畫面房間列表清單 UI
        end
    end
```

## 3. 功能清單對照表

對應 PRD 定義的 MVP 範圍與架構設計，以下是具體落實在 Flask 系統內的路由與功能對照。

| 功能描述 | URL 路由路徑 (Route) | HTTP 方法 | 對應的 Controller / 處理模組 | 說明 |
| -------- | ------------------- | --------- | ------------------------ | ---- |
| **登入頁面** | `/login` | GET | `auth.py` | 渲染 `login.html`，提供帳號密碼輸入介面。 |
| **執行登入** | `/login` | POST | `auth.py` | 接收表單，驗證通過寫入 Session 並重導向至主控台。 |
| **登出系統** | `/logout` | GET | `auth.py` | 清除 Session 並導回登入頁。 |
| **首頁與主控台** | `/` 或 `/dashboard` | GET | `dashboard.py` | 渲染 `index.html`，顯示目前設定的停損出金目標及推薦房間清單。 |
| **歷史日誌查詢** | `/logs` | GET | `dashboard.py` | 渲染 `logs.html`，顯示 Append-only 寫入的所有操作與風控觸發紀錄。 |
| **更新風控設定** | `/api/settings` | POST | `strategy.py` | 接收 Ajax 請求，更新資料庫中使用者的出金目標與停損百分比。 |
| **取得快爆分析** | `/api/monitor/status` | GET | `api.py` | 對應前端 `setInterval` 呼叫，運算偏差並回傳 JSON 格式的預警。 |
