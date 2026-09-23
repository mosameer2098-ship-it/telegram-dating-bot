from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from database import save_profile


NAME, AGE, CITY, BIO = range(4)


async def profile_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    context.user_data.clear()

    await update.message.reply_text(
        "👤 Let's create your profile!\n\n"
        "What should we call you?"
    )

    return NAME


async def get_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    name = update.message.text.strip()

    if not name:
        await update.message.reply_text(
            "Please enter a valid name."
        )
        return NAME

    context.user_data["name"] = name

    await update.message.reply_text(
        "🎂 How old are you?\n\n"
        "LoveMatch is strictly for users aged 18+."
    )

    return AGE


async def get_age(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text(
            "Please enter your age as a number."
        )
        return AGE

    age = int(text)

    if age < 18:
        await update.message.reply_text(
            "❌ Sorry, LoveMatch is only available to adults (18+)."
        )
        context.user_data.clear()
        return ConversationHandler.END

    if age > 100:
        await update.message.reply_text(
            "Please enter a valid age."
        )
        return AGE

    context.user_data["age"] = age

    await update.message.reply_text(
        "📍 Which city do you live in?"
    )

    return CITY


async def get_city(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    city = update.message.text.strip()

    if not city:
        await update.message.reply_text(
            "Please enter a valid city."
        )
        return CITY

    context.user_data["city"] = city

    await update.message.reply_text(
        "📝 Tell us a little about yourself.\n\n"
        "Keep it friendly and respectful."
    )

    return BIO


async def get_bio(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    bio = update.message.text.strip()

    if not bio:
        await update.message.reply_text(
            "Please enter a short bio."
        )
        return BIO

    context.user_data["bio"] = bio

    user = update.effective_user

    save_profile(
        telegram_id=user.id,
        username=user.username,
        name=context.user_data["name"],
        age=context.user_data["age"],
        city=context.user_data["city"],
        bio=context.user_data["bio"],
    )

    name = context.user_data["name"]
    age = context.user_data["age"]
    city = context.user_data["city"]

    await update.message.reply_text(
        "✅ Profile saved!\n\n"
        f"👤 {name}, {age}\n"
        f"📍 {city}\n\n"
        "Your LoveMatch profile is ready. ❤️"
    )

    context.user_data.clear()

    return ConversationHandler.END


async def cancel_profile(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    context.user_data.clear()

    await update.message.reply_text(
        "❌ Profile creation cancelled."
    )

    return ConversationHandler.END
