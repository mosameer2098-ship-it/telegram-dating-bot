from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from database import save_profile


NAME, AGE, CITY, BIO, PHOTO, GENDER, INTERESTED_IN = range(7)


async def profile_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    context.user_data.clear()

    await update.message.reply_text(
        "👤 Let's create your dating profile!\n\n"
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
            "❌ LoveMatch is only available to users aged 18+."
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

    await update.message.reply_text(
        "📸 Now send a profile photo.\n\n"
        "Please use a photo you're comfortable sharing "
        "with other LoveMatch users."
    )

    return PHOTO


async def get_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message.photo:
        await update.message.reply_text(
            "📸 Please send an image as a photo."
        )
        return PHOTO

    photo = update.message.photo[-1]

    context.user_data["photo_file_id"] = photo.file_id

    keyboard = ReplyKeyboardMarkup(
        [
            ["👨 Male", "👩 Female"],
            ["⚪ Other"],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        "👤 What is your gender?",
        reply_markup=keyboard,
    )

    return GENDER


async def get_gender(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    gender_map = {
        "👨 Male": "male",
        "👩 Female": "female",
        "⚪ Other": "other",
    }

    gender = gender_map.get(update.message.text)

    if not gender:
        await update.message.reply_text(
            "Please choose one of the buttons."
        )
        return GENDER

    context.user_data["gender"] = gender

    keyboard = ReplyKeyboardMarkup(
        [
            ["👨 Men", "👩 Women"],
            ["👥 Everyone"],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        "❤️ Who are you interested in?",
        reply_markup=keyboard,
    )

    return INTERESTED_IN


async def get_interested_in(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    interested_map = {
        "👨 Men": "men",
        "👩 Women": "women",
        "👥 Everyone": "everyone",
    }

    interested_in = interested_map.get(update.message.text)

    if not interested_in:
        await update.message.reply_text(
            "Please choose one of the buttons."
        )
        return INTERESTED_IN

    context.user_data["interested_in"] = interested_in

    user = update.effective_user

    save_profile(
        telegram_id=user.id,
        username=user.username,
        name=context.user_data["name"],
        age=context.user_data["age"],
        city=context.user_data["city"],
        bio=context.user_data["bio"],
        photo_file_id=context.user_data["photo_file_id"],
        gender=context.user_data["gender"],
        interested_in=context.user_data["interested_in"],
    )

    await update.message.reply_text(
        "✅ Profile saved successfully!",
        reply_markup=ReplyKeyboardRemove(),
    )

    await update.message.reply_text(
        f"👤 {context.user_data['name']}, "
        f"{context.user_data['age']}\n"
        f"📍 {context.user_data['city']}\n"
        f"⚧ Gender: {context.user_data['gender']}\n\n"
        f"📝 {context.user_data['bio']}\n\n"
        "❤️ Your LoveMatch profile is ready!"
    )

    context.user_data.clear()

    return ConversationHandler.END


async def cancel_profile(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    context.user_data.clear()

    await update.message.reply_text(
        "❌ Profile creation cancelled.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END
