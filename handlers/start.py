import random
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils.i18n import get_text, get_language_name
from database import get_user_language, set_user_language


def language_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
                InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="lang_hi"),
            ],
            [
                InlineKeyboardButton("🇮🇳 Hinglish", callback_data="lang_hinglish"),
                InlineKeyboardButton("🇧🇩 বাংলা", callback_data="lang_bn"),
            ],
        ]
    )


def main_dashboard(language="en"):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"🔎 {get_text('discover', language)}",
                callback_data="dashboard_discover"
            ),
        ],
        [
            InlineKeyboardButton(
                f"👤 {get_text('profile', language)}",
                callback_data="my_profile"
            ),
            InlineKeyboardButton(
                f"💎 {get_text('premium', language)}",
                callback_data="premium_dashboard"
            ),
        ],
        [
            InlineKeyboardButton(
                f"⚙️ {get_text('settings', language)}",
                callback_data="settings"
            ),
            InlineKeyboardButton(
                "🌍 Language",
                callback_data="change_language"
            ),
        ],
        [
            InlineKeyboardButton(
                "🛡️ Safety & Report",
                callback_data="safety_info"
            ),
        ],
    ])


def get_random_welcome_photo():
    folder = Path(__file__).resolve().parent.parent / "assets" / "welcome"
    photos = sorted(folder.glob("*.jpg"))

    if not photos:
        return None

    return random.choice(photos)


def welcome_text(language="en"):
    if language == "hi":
        return (
            "❤️ <b>LoveMatch में आपका स्वागत है!</b>\n\n"
            "✨ नए लोगों से मिलें\n"
            "💞 अपने पसंदीदा लोगों से connect करें\n"
            "🔎 अपने लिए बेहतर matches खोजें\n"
            "💎 Premium features explore करें\n\n"
            "🌹 <i>Your connection starts here.</i>"
        )

    if language == "bn":
        return (
            "❤️ <b>LoveMatch-এ আপনাকে স্বাগতম!</b>\n\n"
            "✨ নতুন মানুষের সাথে পরিচিত হন\n"
            "💞 পছন্দের মানুষের সাথে connect করুন\n"
            "🔎 আপনার জন্য match খুঁজুন\n"
            "💎 Premium features ব্যবহার করুন\n\n"
            "🌹 <i>Your connection starts here.</i>"
        )

    return (
        "❤️ <b>Welcome to LoveMatch!</b>\n\n"
        "✨ Meet new people\n"
        "💞 Connect with people you like\n"
        "🔎 Discover compatible matches\n"
        "💎 Explore Premium features\n\n"
        "🌹 <i>Your connection starts here.</i>"
    )


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user_id = update.effective_user.id

    try:
        language = get_user_language(user_id)
    except Exception:
        language = context.user_data.get("language", "en")

    context.user_data["language"] = language

    photo = get_random_welcome_photo()

    if photo:
        with photo.open("rb") as image:
            await update.message.reply_photo(
                photo=image,
                caption=welcome_text(language),
                reply_markup=main_dashboard(language),
                parse_mode="HTML",
            )
    else:
        await update.message.reply_text(
            welcome_text(language),
            reply_markup=main_dashboard(language),
            parse_mode="HTML",
        )


async def language_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        get_text("choose_language"),
        reply_markup=language_keyboard(),
    )


async def language_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    language = query.data.replace("lang_", "")
    context.user_data["language"] = language

    user_id = update.effective_user.id
    set_user_language(user_id, language)

    await query.edit_message_text(
        welcome_text(language),
        reply_markup=main_dashboard(language),
        parse_mode="HTML",
    )


async def change_language(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🌍 <b>Choose your language</b>",
        reply_markup=language_keyboard(),
        parse_mode="HTML",
    )


async def safety_info(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    language = context.user_data.get("language", "en")

    if language == "hi":
        text = (
            "🛡️ <b>LoveMatch Safety</b>\n\n"
            "• अपना personal information जल्दी share न करें।\n"
            "• suspicious users को report या block करें।\n"
            "• किसी भी unsafe situation में chat बंद करें।\n"
            "• किसी से पैसे या sensitive information मांगने/देने से बचें।"
        )
    elif language == "bn":
        text = (
            "🛡️ <b>LoveMatch Safety</b>\n\n"
            "• দ্রুত ব্যক্তিগত তথ্য শেয়ার করবেন না।\n"
            "• সন্দেহজনক user-কে report বা block করুন।\n"
            "• unsafe মনে হলে chat বন্ধ করুন।"
        )
    else:
        text = (
            "🛡️ <b>LoveMatch Safety</b>\n\n"
            "• Don't share personal information too quickly.\n"
            "• Report or block suspicious users.\n"
            "• Leave a chat if you feel unsafe.\n"
            "• Never share sensitive information or send money to strangers."
        )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="welcome_back"
                )
            ]
        ]),
        parse_mode="HTML",
    )


async def welcome_back(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    language = context.user_data.get("language", "en")

    await query.edit_message_text(
        welcome_text(language),
        reply_markup=main_dashboard(language),
        parse_mode="HTML",
    )
