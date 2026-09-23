
from telegram import Update
from telegram.ext import ContextTypes


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "❤️ Welcome to LoveMatch!\n\n"
        "Find new people, create your profile, "
        "and discover compatible matches.\n\n"
        "Use /profile to create your profile."
    )
