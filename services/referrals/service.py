from database import get_connection
from services.notifications.service import notify_referral


def create_referral(referrer_id, referred_id):
    if referrer_id == referred_id:
        return False

    conn = get_connection()

    existing = conn.execute(
        """
        SELECT id
        FROM referrals
        WHERE referred_id = ?
        LIMIT 1
        """,
        (referred_id,),
    ).fetchone()

    if existing:
        conn.close()
        return False

    conn.execute(
        """
        INSERT INTO referrals (
            referrer_id,
            referred_id,
            reward_claimed
        )
        VALUES (?, ?, 0)
        """,
        (referrer_id, referred_id),
    )

    conn.commit()
    conn.close()

    return True


def get_referral_count(referrer_id):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM referrals
        WHERE referrer_id = ?
        """,
        (referrer_id,),
    ).fetchone()

    conn.close()

    return row["total"] if row else 0


def get_referral_info(referrer_id):
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT referred_id, reward_claimed, created_at
        FROM referrals
        WHERE referrer_id = ?
        ORDER BY created_at DESC
        """,
        (referrer_id,),
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def claim_referral_reward(referrer_id, referred_id):
    from datetime import datetime, timedelta, timezone

    conn = get_connection()

    try:
        row = conn.execute(
            """
            SELECT id, reward_claimed
            FROM referrals
            WHERE referrer_id = ?
              AND referred_id = ?
            LIMIT 1
            """,
            (referrer_id, referred_id),
        ).fetchone()

        if not row:
            return False

        if row["reward_claimed"]:
            return False

        user = conn.execute(
            """
            SELECT is_premium, premium_until
            FROM users
            WHERE telegram_id = ?
            """,
            (referrer_id,),
        ).fetchone()

        if not user:
            return False

        reward_days = REFERRAL_REWARD_DAYS
        now = datetime.now(timezone.utc)

        current_until = None

        if user["premium_until"]:
            try:
                current_until = datetime.fromisoformat(
                    str(user["premium_until"]).replace("Z", "+00:00")
                )

                if current_until.tzinfo is None:
                    current_until = current_until.replace(
                        tzinfo=timezone.utc
                    )
            except ValueError:
                current_until = None

        if current_until and current_until > now:
            start_from = current_until
        else:
            start_from = now

        new_until = start_from + timedelta(days=reward_days)

        conn.execute(
            """
            UPDATE users
            SET is_premium = 1,
                premium_until = ?
            WHERE telegram_id = ?
            """,
            (
                new_until.isoformat(),
                referrer_id,
            ),
        )

        conn.execute(
            """
            UPDATE referrals
            SET reward_claimed = 1
            WHERE id = ?
            """,
            (row["id"],),
        )

        conn.commit()

        notify_referral(
            referrer_id,
            f"Referral reward claimed: {reward_days} days Premium.",
        )

        return True

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def get_referral_link(bot_username, user_id):
    bot_username = str(bot_username or "").lstrip("@").strip()
    return f"https://t.me/{bot_username}?start=ref_{int(user_id)}"


def get_referral_stats(referrer_id):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT
            COUNT(*) AS total_referrals,
            COALESCE(SUM(reward_claimed), 0) AS rewards_claimed
        FROM referrals
        WHERE referrer_id = ?
        """,
        (referrer_id,),
    ).fetchone()

    conn.close()

    if not row:
        return {
            "total_referrals": 0,
            "rewards_claimed": 0,
            "pending_rewards": 0,
        }

    total = int(row["total_referrals"] or 0)
    claimed = int(row["rewards_claimed"] or 0)

    return {
        "total_referrals": total,
        "rewards_claimed": claimed,
        "pending_rewards": max(0, total - claimed),
    }


def get_referral_by_referred(referred_id):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT
            id,
            referrer_id,
            referred_id,
            reward_claimed,
            created_at
        FROM referrals
        WHERE referred_id = ?
        LIMIT 1
        """,
        (referred_id,),
    ).fetchone()

    conn.close()

    return dict(row) if row else None


REFERRAL_REWARD_DAYS = 7


def get_referral_reward_days():
    return REFERRAL_REWARD_DAYS
