from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import ContextTypes, ConversationHandler

from database import save_profile
from utils.i18n import get_text


NAME, AGE, CITY, BIO, PHOTO, GENDER, INTERESTED_IN = range(7)


def lang(context):
    return context.user_data.get("language", "en")


def text(context, key):
    return get_text(key, lang(context))


def photo_keyboard(context):
    language = lang(context)

    if language == "hi":
        return ReplyKeyboardMarkup(
            [
                ["📷 Take Live Photo"],
                ["🖼️ Choose from Gallery"],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )

    if language == "bn":
        return ReplyKeyboardMarkup(
            [
                ["📷 Live Photo নিন"],
                ["🖼️ Gallery থেকে নিন"],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )

    return ReplyKeyboardMarkup(
        [
            ["📷 Take Live Photo"],
            ["🖼️ Choose from Gallery"],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


async def profile_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    language = context.user_data.get("language", "en")
    context.user_data.clear()
    context.user_data["language"] = language

    await update.message.reply_text(
        text(context, "profile_create")
    )

    return NAME


async def get_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    name = update.message.text.strip()

    if not name:
        await update.message.reply_text(
            text(context, "profile_valid_name")
        )
        return NAME

    context.user_data["name"] = name

    await update.message.reply_text(
        text(context, "profile_age")
    )

    return AGE


async def get_age(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    value = update.message.text.strip()

    if not value.isdigit():
        await update.message.reply_text(
            text(context, "profile_valid_age")
        )
        return AGE

    age = int(value)

    if age < 18:
        await update.message.reply_text(
            text(context, "profile_underage")
        )
        context.user_data.clear()
        return ConversationHandler.END

    if age > 100:
        await update.message.reply_text(
            text(context, "profile_invalid_age")
        )
        return AGE

    context.user_data["age"] = age

    await update.message.reply_text(
        text(context, "profile_city")
    )

    return CITY


async def get_city(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    city = update.message.text.strip()

    if not city:
        await update.message.reply_text(
            text(context, "profile_valid_city")
        )
        return CITY

    context.user_data["city"] = city

    await update.message.reply_text(
        text(context, "profile_bio")
    )

    return BIO


async def get_bio(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    bio = update.message.text.strip()

    if not bio:
        await update.message.reply_text(
            text(context, "profile_valid_bio")
        )
        return BIO

    context.user_data["bio"] = bio

    await update.message.reply_text(
        text(context, "profile_photo"),
        reply_markup=photo_keyboard(context),
        parse_mode="HTML",
    )

    return PHOTO


async def get_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message.photo:
        await update.message.reply_text(
            text(context, "profile_send_photo")
        )
        return PHOTO

    photo = update.message.photo[-1]
    context.user_data["photo_file_id"] = photo.file_id

    keyboard = ReplyKeyboardMarkup(
        [
            [text(context, "gender_male"), text(context, "gender_female")],
            [text(context, "gender_other")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        text(context, "profile_gender"),
        reply_markup=keyboard,
    )

    return GENDER


async def get_gender(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    gender_map = {
        text(context, "gender_male"): "male",
        text(context, "gender_female"): "female",
        text(context, "gender_other"): "other",
    }

    gender = gender_map.get(update.message.text)

    if not gender:
        await update.message.reply_text(
            text(context, "profile_choose_button")
        )
        return GENDER

    context.user_data["gender"] = gender

    keyboard = ReplyKeyboardMarkup(
        [
            [text(context, "interested_men"), text(context, "interested_women")],
            [text(context, "interested_everyone")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        text(context, "profile_interested"),
        reply_markup=keyboard,
    )

    return INTERESTED_IN


async def get_interested_in(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    interested_map = {
        text(context, "interested_men"): "men",
        text(context, "interested_women"): "women",
        text(context, "interested_everyone"): "everyone",
    }

    interested_in = interested_map.get(update.message.text)

    if not interested_in:
        await update.message.reply_text(
            text(context, "profile_choose_button")
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
        language=context.user_data.get("language", "en"),
    )

    await update.message.reply_text(
        text(context, "profile_saved"),
        reply_markup=ReplyKeyboardRemove(),
    )

    await update.message.reply_text(
        f"👤 {context.user_data['name']}, "
        f"{context.user_data['age']}\n"
        f"📍 {context.user_data['city']}\n"
        f"⚧ {context.user_data['gender']}\n\n"
        f"📝 {context.user_data['bio']}\n\n"
        + text(context, "profile_ready")
    )

    context.user_data.clear()

    return ConversationHandler.END


async def cancel_profile(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    context.user_data.clear()

    await update.message.reply_text(
        text(context, "profile_cancelled"),
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END
