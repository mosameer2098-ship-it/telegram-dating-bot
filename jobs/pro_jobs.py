import asyncio
from telegram.error import Forbidden, BadRequest, RetryAfter
from services.pro_features import (
    get_flag, generate_promo, all_users_for_broadcast, create_broadcast,
    record_delivery, finish_broadcast,
)
from database import get_connection


async def run_ai_broadcast_once(bot):
    if not get_flag("ai_broadcast_enabled"):
        return
    try:
        message = await generate_promo()
    except Exception:
        return

    bid = create_broadcast(message)
    sent = failed = 0
    for uid in all_users_for_broadcast():
        try:
            await bot.send_message(
                uid,
                "📢 <b>LoveMatch</b>\n\n" + message,
                parse_mode="HTML",
            )
            record_delivery(bid, uid, "sent")
            sent += 1
        except RetryAfter as exc:
            await asyncio.sleep(float(exc.retry_after) + 1)
            try:
                await bot.send_message(
                    uid,
                    "📢 <b>LoveMatch</b>\n\n" + message,
                    parse_mode="HTML",
                )
                record_delivery(bid, uid, "sent")
                sent += 1
            except Exception:
                record_delivery(bid, uid, "failed")
                failed += 1
        except (Forbidden, BadRequest):
            record_delivery(bid, uid, "skipped")
            failed += 1
        except Exception:
            record_delivery(bid, uid, "failed")
            failed += 1
        await asyncio.sleep(0.12)

    finish_broadcast(bid, sent, failed)


def cleanup_expired_data():
    conn = get_connection()
    conn.execute("DELETE FROM boosts WHERE expires_at IS NOT NULL AND datetime(expires_at) < CURRENT_TIMESTAMP")
    conn.execute("UPDATE boosts SET active=0 WHERE expires_at IS NOT NULL AND datetime(expires_at) < CURRENT_TIMESTAMP")
    conn.execute("DELETE FROM user_activity WHERE last_seen IS NOT NULL AND datetime(last_seen) < datetime('now','-30 days')")
    conn.execute("DELETE FROM notifications WHERE created_at < datetime('now','-90 days') AND is_read=1")
    conn.commit()
    conn.close()


async def hourly_ai_broadcast_loop(bot):
    while True:
        try:
            cleanup_expired_data()
            await asyncio.sleep(3600)
            await run_ai_broadcast_once(bot)
        except asyncio.CancelledError:
            raise
        except Exception:
            await asyncio.sleep(60)
