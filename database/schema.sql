-- ============================================================================
-- 賽特選房系統 — SQLite 資料庫建表語法
-- ============================================================================
-- 此檔案包含所有資料表的 CREATE TABLE 語句
-- 可直接在 SQLite 中執行，或由 Flask-SQLAlchemy 在應用啟動時自動執行

-- ============================================================================
-- User 表 — 使用者帳號與基本資訊
-- ============================================================================
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    initial_balance DECIMAL(12,2) NOT NULL,
    current_balance DECIMAL(12,2) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT 1
);

-- 建立帳號查詢索引
CREATE INDEX IF NOT EXISTS idx_user_username ON user(username);

-- ============================================================================
-- User Settings 表 — 使用者風控設定
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    daily_target DECIMAL(12,2) NOT NULL,
    target_type VARCHAR(20) NOT NULL,
    stop_loss_amount DECIMAL(12,2),
    stop_loss_percentage DECIMAL(5,2),
    cooldown_minutes INTEGER NOT NULL DEFAULT 30,
    auto_play_enabled BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);

-- ============================================================================
-- Room 表 — 遊戲房間
-- ============================================================================
CREATE TABLE IF NOT EXISTS room (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_code VARCHAR(20) NOT NULL UNIQUE,
    room_name VARCHAR(100) NOT NULL,
    current_odds DECIMAL(5,2) NOT NULL,
    total_records INTEGER NOT NULL DEFAULT 0,
    win_rate DECIMAL(5,2) NOT NULL DEFAULT 50.0,
    last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_room_code ON room(room_code);
CREATE INDEX IF NOT EXISTS idx_room_is_active ON room(is_active);

-- ============================================================================
-- Room Record 表 — 房間開獎紀錄
-- ============================================================================
CREATE TABLE IF NOT EXISTS room_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    result VARCHAR(20) NOT NULL,
    recorded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    burst_indicator INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (room_id) REFERENCES room(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_room_record_room_id ON room_record(room_id);
CREATE INDEX IF NOT EXISTS idx_room_record_user_id ON room_record(user_id);
CREATE INDEX IF NOT EXISTS idx_room_record_recorded_at ON room_record(recorded_at);

-- ============================================================================
-- User Strategy 表 — 使用者下注策略
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_strategy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    strategy_name VARCHAR(100) NOT NULL,
    strategy_type VARCHAR(50) NOT NULL,
    base_amount DECIMAL(10,2) NOT NULL,
    max_loss_streak INTEGER NOT NULL DEFAULT 5,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_strategy_user_id ON user_strategy(user_id);
CREATE INDEX IF NOT EXISTS idx_user_strategy_is_active ON user_strategy(is_active);

-- ============================================================================
-- Betting Record 表 — 下注紀錄
-- ============================================================================
CREATE TABLE IF NOT EXISTS betting_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    strategy_id INTEGER NOT NULL,
    room_id INTEGER NOT NULL,
    bet_amount DECIMAL(10,2) NOT NULL,
    bet_choice VARCHAR(20) NOT NULL,
    bet_result VARCHAR(20) NOT NULL DEFAULT 'pending',
    payout DECIMAL(10,2),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (strategy_id) REFERENCES user_strategy(id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES room(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_betting_record_user_id ON betting_record(user_id);
CREATE INDEX IF NOT EXISTS idx_betting_record_created_at ON betting_record(created_at);
CREATE INDEX IF NOT EXISTS idx_betting_record_bet_result ON betting_record(bet_result);

-- ============================================================================
-- Operation Log 表 — 操作日誌（Append-Only）
-- ============================================================================
CREATE TABLE IF NOT EXISTS operation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    amount DECIMAL(12,2),
    status VARCHAR(20) NOT NULL DEFAULT 'success',
    reason TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details TEXT,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_operation_log_user_id ON operation_log(user_id);
CREATE INDEX IF NOT EXISTS idx_operation_log_created_at ON operation_log(created_at);
CREATE INDEX IF NOT EXISTS idx_operation_log_operation_type ON operation_log(operation_type);

-- ============================================================================
-- Alert History 表 — 警告記錄
-- ============================================================================
CREATE TABLE IF NOT EXISTS alert_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    room_id INTEGER NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    alert_message TEXT NOT NULL,
    burst_score DECIMAL(5,2),
    is_read BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES room(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_alert_history_user_id ON alert_history(user_id);
CREATE INDEX IF NOT EXISTS idx_alert_history_is_read ON alert_history(is_read);
CREATE INDEX IF NOT EXISTS idx_alert_history_created_at ON alert_history(created_at);
CREATE INDEX IF NOT EXISTS idx_alert_history_alert_type ON alert_history(alert_type);

-- ============================================================================
-- 索引與視圖（可選）
-- ============================================================================

-- 複合索引：查詢未讀警告時常用
CREATE INDEX IF NOT EXISTS idx_alert_unread ON alert_history(user_id, is_read, created_at);

-- 複合索引：查詢使用者的下注歷史時常用
CREATE INDEX IF NOT EXISTS idx_betting_user_date ON betting_record(user_id, created_at);

-- 複合索引：查詢房間的最近開獎時常用
CREATE INDEX IF NOT EXISTS idx_room_record_date ON room_record(room_id, recorded_at);

-- ============================================================================
-- 備註
-- ============================================================================
-- 1. 所有 DATETIME 欄位皆使用 DEFAULT CURRENT_TIMESTAMP 自動記錄時間戳記
-- 2. 外鍵使用 ON DELETE CASCADE，確保刪除父記錄時自動清理子記錄
-- 3. operation_log 與 alert_history 遵循 Append-Only 原則（應用層禁止修改/刪除）
-- 4. 索引設計優先於頻繁查詢的條件，減少全表掃描
-- 5. 若使用 SQLAlchemy，可由 Flask 應用在啟動時自動執行 db.create_all()
