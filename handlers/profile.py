
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

NAME, AGE, CITY, BIO = range(4)


async def profile_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "👤 Let's create your profile!\n\n"
        "First, what should we call you?"
    )
    return NAME


async def get_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    context.user_data["name"] = update.message.text.strip()

    await update.message.reply_text(
        "🎂 How old are you?\n\n"
        "You must be 18 or older to use LoveMatch."
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
            "Sorry, LoveMatch is only available to adults (18+)."
        )
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
    context.user_data["city"] = update.message.text.strip()

    await update.message.reply_text(
        "📝 Write a short bio about yourself."
    )
    return BIO


async def get_bio(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    context.user_data["bio"] = update.message.text.strip()

    name = context.user_data["name"]
    age = context.user_data["age"]
    city = context.user_data["city"]
    bio = context.user_data["bio"]

    await update.message.reply_text(
        "✅ Profile created!\n\n"
        f"👤 {name}, {age}\n"
        f"📍 {city}\n\n"
        f"📝 {bio}"
    )

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
