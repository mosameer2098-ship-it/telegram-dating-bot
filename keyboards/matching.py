from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def discover_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "❤️ Like",
                    callback_data="like",
                ),
                InlineKeyboardButton(
                    "💖 Super Like",
                    callback_data="super_like",
                ),
            ],
            [
                InlineKeyboardButton(
                    "❌ Pass",
                    callback_data="pass",
                ),
                InlineKeyboardButton(
                    "↩️ Rewind",
                    callback_data="rewind",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⭐ Favorite",
                    callback_data="favorite_current",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🚩 Report",
                    callback_data="report",
                ),
                InlineKeyboardButton(
                    "🚫 Block",
                    callback_data="block",
                ),
            ],
        ]
    )


def match_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💬 Start Chat",
                    callback_data="start_chat",
                )
            ],
            [
                InlineKeyboardButton(
                    "❤️ View Match",
                    callback_data="view_match",
                ),
            ],
        ]
    )


def match_actions_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💬 Chat",
                    callback_data="start_chat",
                ),
                InlineKeyboardButton(
                    "⚙️ Chat Menu",
                    callback_data="chat_menu",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🤖 AI Icebreaker",
                    callback_data="ai_icebreaker",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🤖 AI Icebreaker",
                    callback_data="ai_icebreaker",
                ),
            ],
            [
                InlineKeyboardButton(
                    "❌ Unmatch",
                    callback_data="unmatch",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🚫 Block",
                    callback_data="block",
                ),
                InlineKeyboardButton(
                    "🚩 Report",
                    callback_data="report",
                ),
            ],
        ]
    )


def advanced_chat_keyboard(unread_count=0):
    unread_text = (
        f"🔔 Unread Messages ({unread_count})"
        if unread_count
        else "🔔 Unread Messages"
    )

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💬 Continue Chat",
                    callback_data="chat_continue",
                )
            ],
            [
                InlineKeyboardButton(
                    "📖 Chat History",
                    callback_data="chat_history",
                )
            ],
            [
                InlineKeyboardButton(
                    unread_text,
                    callback_data="chat_unread",
                )
            ],
            [
                InlineKeyboardButton(
                    "🛑 End Chat",
                    callback_data="chat_end",
                )
            ],
        ]
    )
