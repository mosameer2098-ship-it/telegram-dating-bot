from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def discover_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("❤️ Like", callback_data="like"),
                InlineKeyboardButton("❌ Pass", callback_data="pass"),
            ],
            [
                InlineKeyboardButton(
                    "🚫 Report",
                    callback_data="report",
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
            ]
        ]
    )
