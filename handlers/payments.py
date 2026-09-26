import json
from datetime import datetime, timedelta, timezone

from telegram import LabeledPrice, Update
from telegram.ext import ContextTypes

from services.payments import (
    create_payment_order,
    get_payment_order,
    mark_payment_paid,
)
from services.premium import get_premium_plan
from database import get_connection


async def buy_premium_plan(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    plan_id = query.data.replace("buy_premium_", "", 1)
    plan = get_premium_plan(plan_id)

    if not plan:
        await query.answer(
            "❌ Invalid Premium plan.",
            show_alert=True,
        )
        return

    user_id = update.effective_user.id

    try:
        order = create_payment_order(user_id, plan_id)
    except Exception:
        await query.message.reply_text(
            "❌ Could not create the payment order. Please try again."
        )
        return

    price = LabeledPrice(
        label=plan["name"],
        amount=plan["stars"],
    )

    await context.bot.send_invoice(
        chat_id=query.message.chat_id,
        title=plan["name"],
        description=(
            f"LoveMatch Premium access for {plan['days']} days."
        ),
        payload=order["payload"],
        provider_token="",
        currency="XTR",
        prices=[price],
    )


async def precheckout_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.pre_checkout_query

    try:
        payload = json.loads(query.invoice_payload)
        order_id = payload["order_id"]
        user_id = int(payload["telegram_id"])
        plan_id = payload["plan_id"]

        order = get_payment_order(order_id)
        plan = get_premium_plan(plan_id)

        valid = (
            order is not None
            and plan is not None
            and order["status"] == "pending"
            and int(order["telegram_id"]) == int(query.from_user.id)
            and int(order["telegram_id"]) == user_id
            and order["currency"] == "XTR"
            and int(order["amount"]) == int(query.total_amount)
        )

        if not valid:
            await query.answer(
                ok=False,
                error_message="This payment order is invalid or expired.",
            )
            return

        await query.answer(ok=True)

    except Exception:
        await query.answer(
            ok=False,
            error_message="Unable to verify this payment order.",
        )


async def successful_payment_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.message
    payment = message.successful_payment

    if not payment:
        return

    try:
        payload = json.loads(payment.invoice_payload)

        order_id = payload["order_id"]
        user_id = int(payload["telegram_id"])
        plan_id = payload["plan_id"]

        if user_id != update.effective_user.id:
            return

        order = get_payment_order(order_id)
        plan = get_premium_plan(plan_id)

        if not order or not plan:
            await message.reply_text(
                "⚠️ Payment received, but the order could not be verified. "
                "Please contact support."
            )
            return

        if order["status"] == "paid":
            await message.reply_text(
                "✅ This payment has already been processed."
            )
            return

        if (
            order["currency"] != "XTR"
            or int(order["amount"]) != int(payment.total_amount)
        ):
            await message.reply_text(
                "⚠️ Payment amount verification failed. Please contact support."
            )
            return

        saved = mark_payment_paid(
            order_id,
            payment.telegram_payment_charge_id,
        )

        if not saved:
            await message.reply_text(
                "⚠️ Payment could not be recorded. Please contact support."
            )
            return

        conn = get_connection()

        row = conn.execute(
            """
            SELECT premium_until
            FROM users
            WHERE telegram_id = ?
            """,
            (user_id,),
        ).fetchone()

        now = datetime.now(timezone.utc)

        current_until = None

        if row and row["premium_until"]:
            try:
                current_until = datetime.fromisoformat(
                    row["premium_until"]
                )

                if current_until.tzinfo is None:
                    current_until = current_until.replace(
                        tzinfo=timezone.utc
                    )

            except ValueError:
                current_until = None

        start_from = (
            current_until
            if current_until and current_until > now
            else now
        )

        premium_until = start_from + timedelta(
            days=plan["days"]
        )

        conn.execute(
            """
            UPDATE users
            SET is_premium = 1,
                premium_until = ?
            WHERE telegram_id = ?
            """,
            (
                premium_until.isoformat(),
                user_id,
            ),
        )

        conn.commit()
        conn.close()

        await message.reply_text(
            "💎 <b>Premium Activated!</b>\n\n"
            f"✨ Plan: <b>{plan['name']}</b>\n"
            f"⭐ Paid: <b>{payment.total_amount} Stars</b>\n"
            f"📅 Valid until: <b>{premium_until.isoformat()}</b>\n\n"
            "❤️ Enjoy your LoveMatch Premium experience!",
            parse_mode="HTML",
        )

    except Exception:
        await message.reply_text(
            "⚠️ Payment received but activation failed. "
            "Please contact support."
        )
