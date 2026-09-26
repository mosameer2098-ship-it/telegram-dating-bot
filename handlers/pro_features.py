import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_ID
from services.pro_features import (
    notification_prefs, toggle_notification_pref, get_viewers, trending_profiles,
    recommendations, get_compatibility, user_achievements, ACHIEVEMENTS,
    set_flag, get_flag, is_banned, set_ban, remove_ban, evaluate_achievements,
)


def pro_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧠 Recommendations", callback_data="pro_recommendations"), InlineKeyboardButton("🔥 Trending", callback_data="pro_trending")],
        [InlineKeyboardButton("💯 Compatibility", callback_data="pro_compatibility"), InlineKeyboardButton("🏆 Achievements", callback_data="pro_achievements")],
        [InlineKeyboardButton("👀 Who Viewed Me", callback_data="pro_viewers")],
        [InlineKeyboardButton("🔔 Notification Settings", callback_data="pro_notifications")],
    ])

async def pro_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 <b>LoveMatch Pro</b>\n\nChoose a feature below.",
        reply_markup=pro_keyboard(),
        parse_mode="HTML",
    )

async def pro_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.edit_message_text("🚀 <b>LoveMatch Pro</b>\n\nExplore smart recommendations, compatibility, trending profiles, achievements and privacy notifications.", reply_markup=pro_keyboard(), parse_mode="HTML")

async def pro_recommendations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    rows=recommendations(update.effective_user.id, 5)
    if not rows: return await q.message.reply_text("No recommendations available yet.")
    text="🧠 <b>Smart Recommendations</b>\n\n"+"\n".join(f"• {html.escape(r['name'])}, {r['age']} — {html.escape(r['city'])}" for r in rows)
    await q.message.reply_text(text, parse_mode="HTML")

async def pro_trending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    rows=trending_profiles(update.effective_user.id,5)
    text="🔥 <b>Trending Profiles</b>\n\n"+"\n".join(f"• {html.escape(r['name'])}, {r['age']} — {html.escape(r['city'])}" for r in rows) if rows else "No trending profiles yet."
    await q.message.reply_text(text, parse_mode="HTML")

async def pro_compatibility(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    from handlers.matches import get_match_profile
    p=get_match_profile(update.effective_user.id)
    if not p: return await q.message.reply_text("💔 You need an active match first.")
    score=get_compatibility(update.effective_user.id,p['telegram_id'])
    await q.message.reply_text(f"💯 <b>Compatibility</b>\n\nYou and {html.escape(p['name'])}: <b>{score}%</b>",parse_mode="HTML")

async def pro_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer(); evaluate_achievements(update.effective_user.id)
    rows=user_achievements(update.effective_user.id); unlocked={r['achievement_key'] for r in rows}
    lines=[f"{'✅' if k in unlocked else '🔒'} {v[0]} {v[1]} — {v[2]}" for k,v in ACHIEVEMENTS.items()]
    await q.message.reply_text("🏆 <b>Achievements</b>\n\n"+"\n".join(lines),parse_mode="HTML")

async def pro_viewers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    rows=get_viewers(update.effective_user.id)
    text="👀 <b>Who Viewed You</b>\n\n"+"\n".join(f"• {html.escape(r['name'])}, {r['age']} — {html.escape(r['city'])}" for r in rows) if rows else "Nobody has viewed your profile yet."
    await q.message.reply_text(text,parse_mode="HTML")

async def pro_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer(); p=notification_prefs(update.effective_user.id)
    labels=[("likes","❤️ Likes"),("matches","💞 Matches"),("messages","💬 Messages"),("profile_views","👀 Profile views"),("promotions","📢 Promotions")]
    kb=[[InlineKeyboardButton(f"{label}: {'ON' if p[key] else 'OFF'}",callback_data=f"notif_toggle_{key}")] for key,label in labels]
    await q.message.reply_text("🔔 <b>Notification Preferences</b>",reply_markup=InlineKeyboardMarkup(kb),parse_mode="HTML")

async def notif_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; key=q.data.replace("notif_toggle_",""); value=toggle_notification_pref(update.effective_user.id,key); await q.answer("Enabled" if value else "Disabled")
    await pro_notifications(update,context)

async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    from database import get_connection
    c=get_connection(); users=c.execute("SELECT COUNT(*) FROM users").fetchone()[0]; matches=c.execute("SELECT COUNT(*) FROM matches").fetchone()[0]; premium=c.execute("SELECT COUNT(*) FROM users WHERE is_premium=1").fetchone()[0]; reports=c.execute("SELECT COUNT(*) FROM reports").fetchone()[0]; c.close()
    await update.message.reply_text(f"🛠 <b>Admin Dashboard</b>\n\n👥 Users: {users}\n💞 Matches: {matches}\n⭐ Premium: {premium}\n🚩 Reports: {reports}\n📢 AI Broadcast: {'ON' if get_flag('ai_broadcast_enabled') else 'OFF'}\n\n/admin_broadcast_on\n/admin_broadcast_off\n/admin_ban USER_ID [reason]\n/admin_unban USER_ID",parse_mode="HTML")

async def admin_broadcast_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    enabled=update.message.text.endswith("on"); set_flag("ai_broadcast_enabled",enabled); await update.message.reply_text(f"AI promotional broadcast: {'ON' if enabled else 'OFF'}")

async def admin_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or len(context.args)<1: return
    try: uid=int(context.args[0])
    except ValueError: return await update.message.reply_text("Invalid user ID.")
    set_ban(uid,ADMIN_ID," ".join(context.args[1:]) or "Admin action"); await update.message.reply_text(f"Banned {uid}.")

async def admin_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or len(context.args)<1: return
    try: uid=int(context.args[0])
    except ValueError: return await update.message.reply_text("Invalid user ID.")
    remove_ban(uid,ADMIN_ID); await update.message.reply_text(f"Unbanned {uid}.")


async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from services.pro_features import ai_translate
    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /translate <language> <message>\nExample: /translate Hindi Hello, nice to meet you!")
    language=context.args[0]
    source=" ".join(context.args[1:])
    try:
        result=await ai_translate(source, language)
    except Exception:
        return await update.message.reply_text("❌ Translation is unavailable right now.")
    await update.message.reply_text(f"🌐 <b>{html.escape(language)}</b>\n\n{html.escape(result)}",parse_mode="HTML")

async def admin_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    from database import get_connection
    c=get_connection(); rows=c.execute("SELECT reporter_id,reported_id,reason,created_at FROM reports ORDER BY id DESC LIMIT 15").fetchall(); c.close()
    if not rows: return await update.message.reply_text("No reports found.")
    text="🚩 <b>Recent Reports</b>\n\n"+"\n".join(f"{r['created_at']} — {r['reporter_id']} → {r['reported_id']}\n{html.escape(r['reason'] or 'No reason')}" for r in rows)
    await update.message.reply_text(text,parse_mode="HTML")

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    from database import get_connection
    c=get_connection(); rows=c.execute("SELECT telegram_id,name,age,city,is_premium,created_at FROM users ORDER BY id DESC LIMIT 25").fetchall(); c.close()
    if not rows: return await update.message.reply_text("No users found.")
    lines=[]
    for r in rows:
        lines.append(f"{r['telegram_id']} — {html.escape(r['name'])}, {r['age']} — {html.escape(r['city'])} — {'PREMIUM' if r['is_premium'] else 'FREE'}")
    await update.message.reply_text("👥 <b>Recent Users</b>\n\n"+"\n".join(lines),parse_mode="HTML")

async def admin_flag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or len(context.args) < 2: return
    key=context.args[0]; value=context.args[1].lower() in ("on","1","true","yes")
    set_flag(key,value)
    await update.message.reply_text(f"Feature flag <code>{html.escape(key)}</code>: {'ON' if value else 'OFF'}",parse_mode="HTML")
