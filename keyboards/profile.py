
from telegram import ReplyKeyboardMarkup


def profile_cancel_keyboard():
    return ReplyKeyboardMarkup(
        [["❌ Cancel"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
