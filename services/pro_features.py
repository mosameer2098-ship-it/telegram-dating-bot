import asyncio
import html
import random
from datetime import datetime, timedelta, timezone
from typing import Optional

from database import get_connection

try:
    from services.ai import _client, MODEL
except Exception:
    _client = None
    MODEL = "gemini-3.8-flash"


FEATURE_DEFAULTS = {
    "ai_broadcast_enabled": "1",
    "ai_translation_enabled": "1",
    "compatibility_enabled": "1",
    "recommendations_enabled": "1",
    "achievements_enabled": "1",
    "trending_enabled": "1",
    "profile_views_enabled": "1",
    "notification_preferences_enabled": "1",
}

ACHIEVEMENTS = {
    "first_like": ("💗", "First Like", "Send your first like"),
    "first_match": ("💞", "First Match", "Get your first match"),
    "first_message": ("💬", "First Message", "Send your first chat message"),
    "profile_complete": ("✨", "Profile Complete", "Complete your profile"),
    "five_matches": ("🔥", "Popular Heart", "Get 5 matches"),
    "ten_likes": ("❤️", "Heart Collector", "Send 10 likes"),
    "referral_first": ("🎁", "Connector", "Refer your first user"),
}


def ensure_pro_tables():
    conn = get_connection()
    for sql in (
        """CREATE TABLE IF NOT EXISTS user_notification_preferences (
            telegram_id INTEGER PRIMARY KEY,
            likes INTEGER DEFAULT 1,
            matches INTEGER DEFAULT 1,
            messages INTEGER DEFAULT 1,
            profile_views INTEGER DEFAULT 1,
            promotions INTEGER DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS feature_flags (
            key TEXT PRIMARY KEY,
            enabled INTEGER DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS ai_broadcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_count INTEGER DEFAULT 0,
            failed_count INTEGER DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS ai_broadcast_deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            broadcast_id INTEGER NOT NULL,
            telegram_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(broadcast_id, telegram_id)
        )""",
        """CREATE TABLE IF NOT EXISTS bans (
            telegram_id INTEGER PRIMARY KEY,
            reason TEXT,
            banned_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS admin_audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            target_id INTEGER,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
    ):
        conn.execute(sql)
    for key, value in FEATURE_DEFAULTS.items():
        conn.execute("INSERT OR IGNORE INTO feature_flags(key, enabled) VALUES(?, ?)", (key, int(value)))
    conn.commit()
    conn.close()


def get_flag(key: str, default=True) -> bool:
    conn = get_connection()
    row = conn.execute("SELECT enabled FROM feature_flags WHERE key=?", (key,)).fetchone()
    conn.close()
    return bool(row[0]) if row else default


def set_flag(key: str, enabled: bool):
    conn = get_connection()
    conn.execute("INSERT INTO feature_flags(key, enabled, updated_at) VALUES(?,?,CURRENT_TIMESTAMP) ON CONFLICT(key) DO UPDATE SET enabled=excluded.enabled, updated_at=CURRENT_TIMESTAMP", (key, int(enabled)))
    conn.commit()
    conn.close()


def is_banned(user_id: int) -> bool:
    conn = get_connection()
    row = conn.execute("SELECT 1 FROM bans WHERE telegram_id=?", (user_id,)).fetchone()
    conn.close()
    return bool(row)


def set_ban(user_id: int, admin_id: int, reason: str = ""):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO bans(telegram_id, reason, banned_by) VALUES(?,?,?)", (user_id, reason, admin_id))
    conn.execute("INSERT INTO admin_audit_logs(admin_id, action, target_id, details) VALUES(?,?,?,?)", (admin_id, "ban", user_id, reason))
    conn.commit(); conn.close()


def remove_ban(user_id: int, admin_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM bans WHERE telegram_id=?", (user_id,))
    conn.execute("INSERT INTO admin_audit_logs(admin_id, action, target_id) VALUES(?,?,?)", (admin_id, "unban", user_id))
    conn.commit(); conn.close()


def notification_prefs(user_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM user_notification_preferences WHERE telegram_id=?", (user_id,)).fetchone()
    if not row:
        conn.execute("INSERT OR IGNORE INTO user_notification_preferences(telegram_id) VALUES(?)", (user_id,))
        conn.commit()
        row = conn.execute("SELECT * FROM user_notification_preferences WHERE telegram_id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row)


def toggle_notification_pref(user_id: int, field: str) -> bool:
    allowed = {"likes", "matches", "messages", "profile_views", "promotions"}
    if field not in allowed:
        return False
    current = notification_prefs(user_id)[field]
    value = 0 if current else 1
    conn = get_connection()
    conn.execute(f"UPDATE user_notification_preferences SET {field}=?, updated_at=CURRENT_TIMESTAMP WHERE telegram_id=?", (value, user_id))
    conn.commit(); conn.close()
    return bool(value)


def record_profile_view(viewer_id: int, viewed_id: int):
    if viewer_id == viewed_id or not get_flag("profile_views_enabled"):
        return
    conn = get_connection()
    conn.execute("INSERT INTO profile_views(viewer_id, viewed_id) VALUES(?,?)", (viewer_id, viewed_id))
    conn.commit(); conn.close()


def get_viewers(user_id: int, limit=20):
    conn = get_connection()
    rows = conn.execute("""SELECT u.telegram_id,u.name,u.age,u.city,u.bio,pv.created_at
        FROM profile_views pv JOIN users u ON u.telegram_id=pv.viewer_id
        WHERE pv.viewed_id=? ORDER BY pv.created_at DESC LIMIT ?""", (user_id, limit)).fetchall()
    conn.close(); return rows


def compatibility_score(a, b) -> int:
    score = 35
    if (a["city"] or "").strip().lower() == (b["city"] or "").strip().lower(): score += 20
    if a["interested_in"] and b["gender"] and a["interested_in"].lower() in (b["gender"].lower(), "any"): score += 15
    if b["interested_in"] and a["gender"] and b["interested_in"].lower() in (a["gender"].lower(), "any"): score += 15
    age_gap = abs(int(a["age"] or 0) - int(b["age"] or 0))
    score += max(0, 15 - min(age_gap, 15))
    return max(0, min(100, score))


def get_compatibility(user_id: int, target_id: int):
    conn = get_connection()
    a = conn.execute("SELECT * FROM users WHERE telegram_id=?", (user_id,)).fetchone()
    b = conn.execute("SELECT * FROM users WHERE telegram_id=?", (target_id,)).fetchone()
    conn.close()
    if not a or not b: return None
    return compatibility_score(a, b)


def trending_profiles(user_id: int, limit=10):
    conn = get_connection()
    rows = conn.execute("""SELECT u.*, (COALESCE(l.cnt,0)*3 + COALESCE(v.cnt,0) + COALESCE(m.cnt,0)*5) AS trend
        FROM users u
        LEFT JOIN (SELECT liked_id id, COUNT(*) cnt FROM likes GROUP BY liked_id) l ON l.id=u.telegram_id
        LEFT JOIN (SELECT viewed_id id, COUNT(*) cnt FROM profile_views GROUP BY viewed_id) v ON v.id=u.telegram_id
        LEFT JOIN (SELECT CASE WHEN user1_id=? THEN user2_id ELSE user1_id END id, COUNT(*) cnt FROM matches WHERE user1_id=? OR user2_id=? GROUP BY id) m ON m.id=u.telegram_id
        WHERE u.telegram_id!=? AND COALESCE(u.is_incognito,0)=0
        ORDER BY trend DESC, u.created_at DESC LIMIT ?""", (user_id,user_id,user_id,user_id,limit)).fetchall()
    conn.close(); return rows


def recommendations(user_id: int, limit=10):
    conn = get_connection()
    me = conn.execute("SELECT * FROM users WHERE telegram_id=?", (user_id,)).fetchone()
    if not me: conn.close(); return []
    rows = conn.execute("SELECT * FROM users WHERE telegram_id!=? AND COALESCE(is_incognito,0)=0 ORDER BY created_at DESC LIMIT 100", (user_id,)).fetchall()
    conn.close()
    scored = [(compatibility_score(me, row), row) for row in rows]
    scored.sort(key=lambda x:x[0], reverse=True)
    return [r for _, r in scored[:limit]]


def achievement_unlock(user_id: int, key: str):
    if key not in ACHIEVEMENTS: return False
    conn = get_connection()
    cur = conn.execute("INSERT OR IGNORE INTO achievements(telegram_id, achievement_key) VALUES(?,?)", (user_id,key))
    conn.commit(); conn.close()
    return cur.rowcount > 0


def user_achievements(user_id: int):
    conn = get_connection()
    rows = conn.execute("SELECT achievement_key, unlocked_at FROM achievements WHERE telegram_id=? ORDER BY unlocked_at DESC", (user_id,)).fetchall()
    conn.close(); return rows


def evaluate_achievements(user_id: int):
    conn = get_connection()
    likes = conn.execute("SELECT COUNT(*) FROM likes WHERE liker_id=?", (user_id,)).fetchone()[0]
    matches = conn.execute("SELECT COUNT(*) FROM matches WHERE user1_id=? OR user2_id=?", (user_id,user_id)).fetchone()[0]
    messages = conn.execute("SELECT COUNT(*) FROM chat_messages WHERE sender_id=?", (user_id,)).fetchone()[0]
    profile = conn.execute("SELECT name,age,city,bio,photo_file_id FROM users WHERE telegram_id=?", (user_id,)).fetchone()
    conn.close()
    keys=[]
    if likes>=1: keys.append("first_like")
    if matches>=1: keys.append("first_match")
    if messages>=1: keys.append("first_message")
    if profile and all(profile[k] for k in ("name","age","city","photo_file_id")) and profile["bio"]: keys.append("profile_complete")
    if matches>=5: keys.append("five_matches")
    if likes>=10: keys.append("ten_likes")
    for key in keys: achievement_unlock(user_id,key)


async def ai_translate(text: str, target_language: str) -> str:
    if not _client: raise RuntimeError("GEMINI_API_KEY is not configured.")
    prompt=f"Translate this dating-app message into {target_language}. Preserve tone and meaning. Return only the translation. Message: {text}"
    response = await asyncio.to_thread(_client.models.generate_content, model=MODEL, contents=prompt)
    return (response.text or "").strip()


async def generate_promo() -> str:
    if not _client: raise RuntimeError("GEMINI_API_KEY is not configured.")
    prompt=("Write a short, exciting promotional message for the LoveMatch Telegram dating bot. "
            "Mention discovering matches, chatting, premium features and a friendly call to action. "
            "No fake discounts, no guaranteed results, no spammy wording. 3-5 lines. Return only the message.")
    response=await asyncio.to_thread(_client.models.generate_content, model=MODEL, contents=prompt)
    return (response.text or "").strip()


def all_users_for_broadcast():
    conn=get_connection()
    rows=conn.execute("SELECT telegram_id FROM users WHERE telegram_id IS NOT NULL").fetchall()
    conn.close(); return [int(r[0]) for r in rows]


def create_broadcast(message: str) -> int:
    conn=get_connection(); cur=conn.execute("INSERT INTO ai_broadcasts(message) VALUES(?)",(message,)); conn.commit(); bid=cur.lastrowid; conn.close(); return bid


def finish_broadcast(bid, sent, failed):
    conn=get_connection(); conn.execute("UPDATE ai_broadcasts SET sent_count=?, failed_count=? WHERE id=?",(sent,failed,bid)); conn.commit(); conn.close()


def record_delivery(bid, uid, status):
    conn=get_connection(); conn.execute("INSERT OR IGNORE INTO ai_broadcast_deliveries(broadcast_id,telegram_id,status) VALUES(?,?,?)",(bid,uid,status)); conn.commit(); conn.close()
