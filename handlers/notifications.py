from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services.notifications.service import (
    get_unread_notifications,
    mark_all_read,
)


def notifications_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Mark All Read",
                callback_data="notifications_read_all",
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back to LoveMatch",
                callback_data="welcome_back",
            )
        ],
    ])


def format_notification(item):
    title = item.get("title") or "🔔 Notification"
    body = item.get("body") or ""
    return f"{title}\n{body}"


async def notifications_dashboard(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    items = get_unread_notifications(user_id)

    if not items:
        text = (
            "🔔 <b>LoveMatch Notifications</b>\n"
            "━━━━━━━━━━━━━━\n\n"
            "✨ You're all caught up!\n\n"
            "No new notifications right now. ❤️"
        )
    else:
        lines = [
            "🔔 <b>LoveMatch Notifications</b>",
            "━━━━━━━━━━━━━━",
            "",
        ]

        for item in items[:10]:
            lines.append(format_notification(item))
            lines.append("")

        text = "\n".join(lines)

    await query.edit_message_text(
        text,
        reply_markup=notifications_keyboard(),
        parse_mode="HTML",
    )


async def notifications_mark_all_read(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer("Notifications marked as read ✅")

    user_id = update.effective_user.id
    mark_all_read(user_id)

    await query.edit_message_text(
        "🔔 <b>LoveMatch Notifications</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        "✅ All notifications marked as read.\n\n"
        "❤️ You're all caught up!",
        reply_markup=notifications_keyboard(),
        parse_mode="HTML",
    )
