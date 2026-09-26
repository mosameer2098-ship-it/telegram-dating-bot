from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from database import get_connection, save_profile
from services.ai import generate_bio

EDIT_NAME, EDIT_AGE, EDIT_CITY, EDIT_BIO = range(4)


def edit_profile_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Name", callback_data="edit_name")],
        [InlineKeyboardButton("🎂 Age", callback_data="edit_age")],
        [InlineKeyboardButton("📍 City", callback_data="edit_city")],
        [InlineKeyboardButton("📝 Bio", callback_data="edit_bio")],
        [InlineKeyboardButton("🤖 AI Generate Bio", callback_data="ai_generate_bio")],
        [InlineKeyboardButton("⬅️ Back", callback_data="settings")],
    ])


async def edit_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    connection = get_connection()
    profile = connection.execute(
        "SELECT name, age, city, bio FROM users WHERE telegram_id = ?",
        (user_id,),
    ).fetchone()
    connection.close()

    if not profile:
        await query.edit_message_text(
            "👤 You don't have a profile yet.\n\n"
            "Use /profile to create one."
        )
        return ConversationHandler.END

    await query.edit_message_text(
        "✏️ <b>Edit Profile</b>\n\n"
        "Choose what you want to change:",
        reply_markup=edit_profile_keyboard(),
        parse_mode="HTML",
    )


async def edit_name_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "✏️ Send your new name:"
    )
    return EDIT_NAME


async def edit_age_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🎂 Send your new age (18–100):"
    )
    return EDIT_AGE


async def edit_city_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📍 Send your new city:"
    )
    return EDIT_CITY


async def edit_bio_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📝 Send your new bio:"
    )
    return EDIT_BIO


async def save_edit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    field: str,
    value,
):
    user_id = update.effective_user.id

    connection = get_connection()
    profile = connection.execute(
        "SELECT * FROM users WHERE telegram_id = ?",
        (user_id,),
    ).fetchone()
    connection.close()

    if not profile:
        await update.message.reply_text(
            "❌ Profile not found. Please use /profile."
        )
        return ConversationHandler.END

    data = dict(profile)

    data[field] = value

    save_profile(
        telegram_id=user_id,
        username=update.effective_user.username,
        name=data.get("name"),
        age=data.get("age"),
        city=data.get("city"),
        bio=data.get("bio"),
        photo_file_id=data.get("photo_file_id"),
        gender=data.get("gender"),
        interested_in=data.get("interested_in"),
        language=data.get("language") or "en",
    )

    await update.message.reply_text(
        "✅ Profile updated successfully!",
        reply_markup=edit_profile_keyboard(),
    )

    return ConversationHandler.END


async def save_edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()

    if not value or len(value) > 50:
        await update.message.reply_text(
            "❌ Please enter a valid name (1–50 characters)."
        )
        return EDIT_NAME

    return await save_edit(update, context, "name", value)


async def save_edit_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()

    if not value.isdigit():
        await update.message.reply_text(
            "❌ Age must be a number between 18 and 100."
        )
        return EDIT_AGE

    age = int(value)

    if age < 18 or age > 100:
        await update.message.reply_text(
            "❌ Age must be between 18 and 100."
        )
        return EDIT_AGE

    return await save_edit(update, context, "age", age)


async def save_edit_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()

    if not value or len(value) > 100:
        await update.message.reply_text(
            "❌ Please enter a valid city (1–100 characters)."
        )
        return EDIT_CITY

    return await save_edit(update, context, "city", value)


async def save_edit_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()

    if len(value) > 500:
        await update.message.reply_text(
            "❌ Bio must be 500 characters or less."
        )
        return EDIT_BIO

    return await save_edit(update, context, "bio", value)


async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Profile editing cancelled."
    )
    return ConversationHandler.END


async def ai_generate_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🤖 Generating your bio...")

    user_id = update.effective_user.id

    connection = get_connection()
    profile = connection.execute(
        "SELECT name, age, city, gender, interested_in FROM users WHERE telegram_id = ?",
        (user_id,),
    ).fetchone()
    connection.close()

    if not profile:
        await query.edit_message_text(
            "❌ Profile not found. Please create your profile first."
        )
        return

    try:
        bio = await generate_bio(
            name=profile["name"] or "",
            age=int(profile["age"] or 18),
            city=profile["city"] or "",
            gender=profile["gender"] or "",
            interested_in=profile["interested_in"] or "",
        )
    except Exception:
        await query.edit_message_text(
            "❌ AI bio generation failed.\n\n"
            "Please try again in a moment."
        )
        return

    context.user_data["ai_generated_bio"] = bio

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Save Bio", callback_data="ai_save_bio"),
            InlineKeyboardButton("🔄 Regenerate", callback_data="ai_generate_bio"),
        ],
        [
            InlineKeyboardButton("❌ Cancel", callback_data="ai_cancel_bio"),
        ],
    ])

    await query.edit_message_text(
        "🤖 <b>AI Generated Bio</b>\n\n"
        f"{bio}\n\n"
        "Save this bio to your profile?",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


async def ai_save_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    bio = context.user_data.get("ai_generated_bio")

    if not bio:
        await query.edit_message_text(
            "❌ No generated bio found. Please generate one again."
        )
        return

    user_id = update.effective_user.id

    connection = get_connection()
    profile = connection.execute(
        "SELECT * FROM users WHERE telegram_id = ?",
        (user_id,),
    ).fetchone()
    connection.close()

    if not profile:
        await query.edit_message_text(
            "❌ Profile not found."
        )
        return

    data = dict(profile)
    data["bio"] = bio

    save_profile(
        telegram_id=user_id,
        username=update.effective_user.username,
        name=data.get("name"),
        age=data.get("age"),
        city=data.get("city"),
        bio=data.get("bio"),
        photo_file_id=data.get("photo_file_id"),
        gender=data.get("gender"),
        interested_in=data.get("interested_in"),
        language=data.get("language") or "en",
    )

    context.user_data.pop("ai_generated_bio", None)

    await query.edit_message_text(
        "✅ <b>AI Bio Saved!</b>\n\n"
        f"{bio}",
        reply_markup=edit_profile_keyboard(),
        parse_mode="HTML",
    )


async def ai_cancel_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data.pop("ai_generated_bio", None)

    await query.edit_message_text(
        "❌ AI bio generation cancelled.",
        reply_markup=edit_profile_keyboard(),
    )
