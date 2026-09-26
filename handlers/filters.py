from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import get_connection


def filters_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎂 Age Range",
                    callback_data="filter_age",
                )
            ],
            [
                InlineKeyboardButton(
                    "👤 Preferred Gender",
                    callback_data="filter_gender",
                )
            ],
            [
                InlineKeyboardButton(
                    "📍 Preferred City",
                    callback_data="filter_city",
                )
            ],
            [
                InlineKeyboardButton(
                    "📏 Distance",
                    callback_data="filter_distance",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔄 Reset Filters",
                    callback_data="filter_reset",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back to Discover",
                    callback_data="dashboard_discover",
                )
            ],
        ]
    )


def age_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("18–25", callback_data="filter_age_18_25"),
                InlineKeyboardButton("18–30", callback_data="filter_age_18_30"),
            ],
            [
                InlineKeyboardButton("21–35", callback_data="filter_age_21_35"),
                InlineKeyboardButton("25–45", callback_data="filter_age_25_45"),
            ],
            [
                InlineKeyboardButton("18–99", callback_data="filter_age_18_99"),
            ],
            [
                InlineKeyboardButton("⬅️ Back", callback_data="advanced_filters"),
            ],
        ]
    )


def gender_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("👨 Male", callback_data="filter_gender_male"),
                InlineKeyboardButton("👩 Female", callback_data="filter_gender_female"),
            ],
            [
                InlineKeyboardButton("🌈 Other", callback_data="filter_gender_other"),
                InlineKeyboardButton("🌍 Any", callback_data="filter_gender_any"),
            ],
            [
                InlineKeyboardButton("⬅️ Back", callback_data="advanced_filters"),
            ],
        ]
    )


def distance_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📍 5 km", callback_data="filter_distance_5"),
                InlineKeyboardButton("📍 10 km", callback_data="filter_distance_10"),
            ],
            [
                InlineKeyboardButton("📍 25 km", callback_data="filter_distance_25"),
                InlineKeyboardButton("📍 50 km", callback_data="filter_distance_50"),
            ],
            [
                InlineKeyboardButton("🌍 100 km", callback_data="filter_distance_100"),
                InlineKeyboardButton("♾️ Any", callback_data="filter_distance_9999"),
            ],
            [
                InlineKeyboardButton("⬅️ Back", callback_data="advanced_filters"),
            ],
        ]
    )


def _ensure_preferences(user_id):
    connection = get_connection()

    connection.execute(
        """
        INSERT OR IGNORE INTO user_preferences
        (
            telegram_id,
            language,
            min_age,
            max_age,
            preferred_gender,
            preferred_city,
            distance_km
        )
        VALUES (?, 'en', 18, 99, 'any', '', 100)
        """,
        (user_id,),
    )

    connection.commit()
    connection.close()


def get_filter_preferences(user_id):
    _ensure_preferences(user_id)

    connection = get_connection()

    row = connection.execute(
        """
        SELECT min_age, max_age, preferred_gender,
               preferred_city, distance_km
        FROM user_preferences
        WHERE telegram_id = ?
        """,
        (user_id,),
    ).fetchone()

    connection.close()

    return dict(row) if row else {
        "min_age": 18,
        "max_age": 99,
        "preferred_gender": "any",
        "preferred_city": "",
        "distance_km": 100,
    }


async def advanced_filters(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    preferences = get_filter_preferences(update.effective_user.id)

    city = preferences.get("preferred_city") or "Any city"
    gender = preferences.get("preferred_gender") or "any"
    distance = preferences.get("distance_km") or 100

    text = (
        "🔎 <b>Advanced Filters</b>\n\n"
        f"🎂 Age: {preferences['min_age']}–{preferences['max_age']}\n"
        f"👤 Gender: {gender}\n"
        f"📍 City: {city}\n"
        f"📏 Distance: {distance} km\n\n"
        "Choose what you want to change:"
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=filters_keyboard(),
    )


async def filter_age(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🎂 <b>Select Age Range</b>",
        parse_mode="HTML",
        reply_markup=age_keyboard(),
    )


async def filter_gender(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "👤 <b>Select Preferred Gender</b>",
        parse_mode="HTML",
        reply_markup=gender_keyboard(),
    )


async def filter_distance(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📏 <b>Select Maximum Distance</b>",
        parse_mode="HTML",
        reply_markup=distance_keyboard(),
    )


async def filter_city(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    context.user_data["waiting_for_filter_city"] = True

    await query.edit_message_text(
        "📍 <b>Preferred City</b>\n\n"
        "Send the city name in your next message.\n\n"
        "Example: Mumbai",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ Cancel",
                        callback_data="advanced_filters",
                    )
                ]
            ]
        ),
    )


async def filter_age_select(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    data = query.data.replace("filter_age_", "")
    min_age, max_age = data.split("_")

    user_id = update.effective_user.id
    _ensure_preferences(user_id)

    connection = get_connection()
    connection.execute(
        """
        UPDATE user_preferences
        SET min_age = ?
            , max_age = ?
            , updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = ?
        """,
        (int(min_age), int(max_age), user_id),
    )
    connection.commit()
    connection.close()

    await advanced_filters(update, context)


async def filter_gender_select(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    gender = query.data.replace("filter_gender_", "")

    user_id = update.effective_user.id
    _ensure_preferences(user_id)

    connection = get_connection()
    connection.execute(
        """
        UPDATE user_preferences
        SET preferred_gender = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = ?
        """,
        (gender, user_id),
    )
    connection.commit()
    connection.close()

    await advanced_filters(update, context)


async def filter_distance_select(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    distance = query.data.replace("filter_distance_", "")

    user_id = update.effective_user.id
    _ensure_preferences(user_id)

    connection = get_connection()
    connection.execute(
        """
        UPDATE user_preferences
        SET distance_km = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = ?
        """,
        (int(distance), user_id),
    )
    connection.commit()
    connection.close()

    await advanced_filters(update, context)


async def filter_reset(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    _ensure_preferences(user_id)

    connection = get_connection()
    connection.execute(
        """
        UPDATE user_preferences
        SET min_age = 18,
            max_age = 99,
            preferred_gender = 'any',
            preferred_city = '',
            distance_km = 100,
            updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = ?
        """,
        (user_id,),
    )
    connection.commit()
    connection.close()

    await advanced_filters(update, context)


async def filter_city_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not context.user_data.get("waiting_for_filter_city"):
        return

    if not update.message or not update.message.text:
        return

    city = update.message.text.strip()

    if not city:
        await update.message.reply_text(
            "📍 Please enter a valid city name."
        )
        return

    if len(city) > 100:
        await update.message.reply_text(
            "📍 City name is too long. Please try again."
        )
        return

    user_id = update.effective_user.id
    _ensure_preferences(user_id)

    connection = get_connection()
    connection.execute(
        """
        UPDATE user_preferences
        SET preferred_city = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = ?
        """,
        (city, user_id),
    )
    connection.commit()
    connection.close()

    context.user_data.pop("waiting_for_filter_city", None)

    preferences = get_filter_preferences(user_id)

    await update.message.reply_text(
        "📍 <b>City filter saved!</b>\n\n"
        f"Preferred city: <b>{preferences['preferred_city']}</b>",
        parse_mode="HTML",
        reply_markup=filters_keyboard(),
    )
