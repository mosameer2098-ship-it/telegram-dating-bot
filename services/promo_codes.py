from datetime import datetime, timezone, timedelta
from database import get_connection


def _normalize_code(code):
    return str(code or "").strip().upper()


def create_promo_code(
    code,
    reward_type="premium_days",
    reward_value=7,
    max_uses=0,
    expires_at=None,
):
    code = _normalize_code(code)

    if not code:
        raise ValueError("Promo code cannot be empty")

    if reward_type != "premium_days":
        raise ValueError("Unsupported reward type")

    if int(reward_value) <= 0:
        raise ValueError("Reward value must be greater than 0")

    if int(max_uses) < 0:
        raise ValueError("max_uses cannot be negative")

    conn = get_connection()

    try:
        existing = conn.execute(
            "SELECT id FROM promo_codes WHERE UPPER(code) = ?",
            (code,),
        ).fetchone()

        if existing:
            raise ValueError("Promo code already exists")

        cursor = conn.execute(
            """
            INSERT INTO promo_codes
            (
                code,
                reward_type,
                reward_value,
                max_uses,
                used_count,
                active,
                expires_at
            )
            VALUES (?, ?, ?, ?, 0, 1, ?)
            """,
            (
                code,
                reward_type,
                int(reward_value),
                int(max_uses),
                expires_at,
            ),
        )

        conn.commit()

        return {
            "id": cursor.lastrowid,
            "code": code,
            "reward_type": reward_type,
            "reward_value": int(reward_value),
            "max_uses": int(max_uses),
            "used_count": 0,
            "active": True,
            "expires_at": expires_at,
        }

    finally:
        conn.close()


def get_promo_code(code):
    code = _normalize_code(code)

    if not code:
        return None

    conn = get_connection()

    try:
        row = conn.execute(
            """
            SELECT *
            FROM promo_codes
            WHERE UPPER(code) = ?
            LIMIT 1
            """,
            (code,),
        ).fetchone()

        return dict(row) if row else None

    finally:
        conn.close()


def is_promo_valid(code):
    promo = get_promo_code(code)

    if not promo:
        return False, "Promo code not found"

    if not bool(promo["active"]):
        return False, "Promo code is inactive"

    max_uses = int(promo["max_uses"] or 0)
    used_count = int(promo["used_count"] or 0)

    if max_uses > 0 and used_count >= max_uses:
        return False, "Promo code usage limit reached"

    expires_at = promo["expires_at"]

    if expires_at:
        try:
            expiry = datetime.fromisoformat(
                str(expires_at).replace("Z", "+00:00")
            )

            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)

            if datetime.now(timezone.utc) >= expiry:
                return False, "Promo code has expired"

        except ValueError:
            return False, "Promo code expiry is invalid"

    return True, "OK"


def redeem_promo_code(user_id, code):
    code = _normalize_code(code)

    if not code:
        return {
            "success": False,
            "reason": "invalid_code",
            "message": "Please enter a valid promo code.",
        }

    conn = get_connection()

    try:
        promo = conn.execute(
            """
            SELECT *
            FROM promo_codes
            WHERE UPPER(code) = ?
            LIMIT 1
            """,
            (code,),
        ).fetchone()

        if not promo:
            return {
                "success": False,
                "reason": "not_found",
                "message": "Promo code not found.",
            }

        if not bool(promo["active"]):
            return {
                "success": False,
                "reason": "inactive",
                "message": "This promo code is inactive.",
            }

        max_uses = int(promo["max_uses"] or 0)
        used_count = int(promo["used_count"] or 0)

        if max_uses > 0 and used_count >= max_uses:
            return {
                "success": False,
                "reason": "limit_reached",
                "message": "This promo code has reached its usage limit.",
            }

        expires_at = promo["expires_at"]

        if expires_at:
            try:
                expiry = datetime.fromisoformat(
                    str(expires_at).replace("Z", "+00:00")
                )

                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)

                if datetime.now(timezone.utc) >= expiry:
                    return {
                        "success": False,
                        "reason": "expired",
                        "message": "This promo code has expired.",
                    }

            except ValueError:
                return {
                    "success": False,
                    "reason": "invalid_expiry",
                    "message": "Promo code expiry is invalid.",
                }

        existing = conn.execute(
            """
            SELECT id
            FROM user_promo_redemptions
            WHERE telegram_id = ?
              AND promo_code_id = ?
            LIMIT 1
            """,
            (user_id, promo["id"]),
        ).fetchone()

        if existing:
            return {
                "success": False,
                "reason": "already_redeemed",
                "message": "You have already redeemed this promo code.",
            }

        reward_type = promo["reward_type"]
        reward_value = int(promo["reward_value"] or 0)

        if reward_type != "premium_days":
            return {
                "success": False,
                "reason": "unsupported_reward",
                "message": "This promo reward is currently unsupported.",
            }

        conn.execute(
            """
            INSERT INTO user_promo_redemptions
            (
                telegram_id,
                promo_code_id,
                reward_type,
                reward_value
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                promo["id"],
                reward_type,
                reward_value,
            ),
        )

        conn.execute(
            """
            UPDATE promo_codes
            SET used_count = used_count + 1
            WHERE id = ?
            """,
            (promo["id"],),
        )

        conn.commit()

        return {
            "success": True,
            "reason": "redeemed",
            "message": f"Promo code redeemed successfully. Reward: {reward_value} premium days.",
            "code": code,
            "reward_type": reward_type,
            "reward_value": reward_value,
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def deactivate_promo_code(code):
    code = _normalize_code(code)

    conn = get_connection()

    try:
        cursor = conn.execute(
            """
            UPDATE promo_codes
            SET active = 0
            WHERE UPPER(code) = ?
            """,
            (code,),
        )

        conn.commit()
        return cursor.rowcount > 0

    finally:
        conn.close()


def apply_promo_premium(user_id, reward_days):
    reward_days = int(reward_days)

    if reward_days <= 0:
        raise ValueError("Reward days must be greater than 0")

    conn = get_connection()

    try:
        row = conn.execute(
            """
            SELECT premium_until
            FROM users
            WHERE telegram_id = ?
            """,
            (user_id,),
        ).fetchone()

        if not row:
            return False

        now = datetime.now(timezone.utc)

        current_until = None
        if row["premium_until"]:
            try:
                current_until = datetime.fromisoformat(
                    str(row["premium_until"]).replace("Z", "+00:00")
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
                user_id,
            ),
        )

        conn.commit()

        return {
            "success": True,
            "premium_until": new_until.isoformat(),
            "reward_days": reward_days,
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
