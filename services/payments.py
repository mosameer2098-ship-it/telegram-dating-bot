import json
import uuid

from database import get_connection
from services.premium import get_premium_plan


def create_payment_order(telegram_id, plan_id):
    plan = get_premium_plan(plan_id)

    if not plan:
        raise ValueError("Invalid Premium plan")

    order_id = f"LM-{uuid.uuid4().hex[:16].upper()}"

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO payment_orders (
            telegram_id,
            order_type,
            plan_id,
            amount,
            currency,
            status,
            gateway,
            gateway_order_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            telegram_id,
            "premium",
            plan_id,
            plan["stars"],
            "XTR",
            "pending",
            "telegram_stars",
            order_id,
        ),
    )

    conn.commit()
    database_id = conn.execute(
        "SELECT last_insert_rowid()"
    ).fetchone()[0]

    conn.close()

    payload = json.dumps(
        {
            "order_id": order_id,
            "database_id": database_id,
            "telegram_id": telegram_id,
            "plan_id": plan_id,
            "type": "premium",
        },
        separators=(",", ":"),
    )

    return {
        "database_id": database_id,
        "order_id": order_id,
        "telegram_id": telegram_id,
        "plan_id": plan_id,
        "title": plan["name"],
        "description": f"LoveMatch Premium for {plan['days']} days",
        "stars": plan["stars"],
        "currency": "XTR",
        "payload": payload,
    }


def get_payment_order(order_id):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM payment_orders
        WHERE gateway_order_id = ?
        LIMIT 1
        """,
        (order_id,),
    ).fetchone()

    conn.close()

    return dict(row) if row else None


def mark_payment_paid(order_id, telegram_payment_charge_id):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM payment_orders
        WHERE gateway_order_id = ?
        LIMIT 1
        """,
        (order_id,),
    ).fetchone()

    if not row:
        conn.close()
        return False

    conn.execute(
        """
        UPDATE payment_orders
        SET status = 'paid',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (row["id"],),
    )

    conn.execute(
        """
        INSERT INTO payment_transactions (
            order_id,
            telegram_id,
            gateway,
            gateway_payment_id,
            amount,
            currency,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["id"],
            row["telegram_id"],
            "telegram_stars",
            telegram_payment_charge_id,
            row["amount"],
            "XTR",
            "paid",
        ),
    )

    conn.commit()
    conn.close()

    return True
