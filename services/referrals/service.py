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
    conn = get_connection()

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
        conn.close()
        return False

    if row["reward_claimed"]:
        conn.close()
        return False

    conn.execute(
        """
        UPDATE referrals
        SET reward_claimed = 1
        WHERE id = ?
        """,
        (row["id"],),
    )

    conn.commit()
    conn.close()

    notify_referral(
        referrer_id,
        f"Referral reward claimed for user {referred_id}.",
    )

    return True
