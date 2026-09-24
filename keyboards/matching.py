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
