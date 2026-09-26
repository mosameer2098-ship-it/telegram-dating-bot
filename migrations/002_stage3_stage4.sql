-- Stage 3 + Stage 4 additive schema
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT, sender_id INTEGER NOT NULL, receiver_id INTEGER NOT NULL,
    message_id INTEGER, message_type TEXT DEFAULT 'text', message_preview TEXT, reply_to_message_id INTEGER,
    is_read INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS payment_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER NOT NULL, order_type TEXT NOT NULL, plan_id TEXT,
    amount INTEGER NOT NULL, currency TEXT NOT NULL, status TEXT DEFAULT 'pending', gateway TEXT, gateway_order_id TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS payment_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL, telegram_id INTEGER NOT NULL, gateway TEXT,
    gateway_payment_id TEXT, amount INTEGER, currency TEXT, status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS payment_webhooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT, gateway TEXT, event_type TEXT, payload TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS user_notification_preferences (telegram_id INTEGER PRIMARY KEY, likes INTEGER DEFAULT 1, matches INTEGER DEFAULT 1, messages INTEGER DEFAULT 1, profile_views INTEGER DEFAULT 1, promotions INTEGER DEFAULT 1, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS feature_flags (key TEXT PRIMARY KEY, enabled INTEGER DEFAULT 1, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS ai_broadcasts (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, sent_count INTEGER DEFAULT 0, failed_count INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS ai_broadcast_deliveries (id INTEGER PRIMARY KEY AUTOINCREMENT, broadcast_id INTEGER NOT NULL, telegram_id INTEGER NOT NULL, status TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(broadcast_id, telegram_id));
CREATE TABLE IF NOT EXISTS bans (telegram_id INTEGER PRIMARY KEY, reason TEXT, banned_by INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS admin_audit_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER NOT NULL, action TEXT NOT NULL, target_id INTEGER, details TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS idx_chat_messages_receiver ON chat_messages(receiver_id, is_read);
CREATE INDEX IF NOT EXISTS idx_payment_orders_user ON payment_orders(telegram_id);
CREATE INDEX IF NOT EXISTS idx_broadcast_delivery_user ON ai_broadcast_deliveries(telegram_id);
INSERT OR IGNORE INTO feature_flags(key,enabled) VALUES('ai_broadcast_enabled',1);
INSERT OR IGNORE INTO feature_flags(key,enabled) VALUES('ai_translation_enabled',1);
INSERT OR IGNORE INTO feature_flags(key,enabled) VALUES('compatibility_enabled',1);
INSERT OR IGNORE INTO feature_flags(key,enabled) VALUES('recommendations_enabled',1);
INSERT OR IGNORE INTO feature_flags(key,enabled) VALUES('achievements_enabled',1);
INSERT OR IGNORE INTO feature_flags(key,enabled) VALUES('trending_enabled',1);
INSERT OR IGNORE INTO feature_flags(key,enabled) VALUES('profile_views_enabled',1);
INSERT OR IGNORE INTO feature_flags(key,enabled) VALUES('notification_preferences_enabled',1);
