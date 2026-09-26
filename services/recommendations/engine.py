import sqlite3
from pathlib import Path
from datetime import datetime, timedelta


DB_PATH = Path(__file__).resolve().parents[2] / "database" / "lovematch.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _safe_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def get_preferences(user_id):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT min_age, max_age, preferred_gender,
               preferred_city, distance_km
        FROM user_preferences
        WHERE telegram_id = ?
        """,
        (user_id,),
    ).fetchone()

    conn.close()

    if not row:
        return {
            "min_age": 18,
            "max_age": 99,
            "preferred_gender": "any",
            "preferred_city": "",
            "distance_km": 100,
        }

    return dict(row)


def get_seen_users(user_id):
    conn = get_connection()

    seen = set()

    rows = conn.execute(
        """
        SELECT liked_id AS user_id
        FROM likes
        WHERE liker_id = ?

        UNION

        SELECT passed_id AS user_id
        FROM passes
        WHERE passer_id = ?

        UNION

        SELECT liked_id AS user_id
        FROM super_likes
        WHERE liker_id = ?
        """,
        (user_id, user_id, user_id),
    ).fetchall()

    for row in rows:
        seen.add(row["user_id"])

    seen.add(user_id)

    conn.close()
    return seen


def _profile_completeness(profile):
    fields = [
        profile["name"],
        profile["age"],
        profile["city"],
        profile["bio"],
        profile["photo_file_id"],
        profile["gender"],
        profile["interested_in"],
    ]

    completed = sum(
        1 for value in fields
        if value not in (None, "", 0)
    )

    return (completed / len(fields)) * 100


def _normalize_gender(value):
    value = str(value or "").strip().lower()

    aliases = {
        "male": {"male", "man", "men"},
        "female": {"female", "woman", "women"},
        "other": {"other", "non-binary", "nonbinary"},
    }

    for canonical, values in aliases.items():
        if value in values:
            return canonical

    return value


def _is_gender_match(user, candidate, preferred_gender=None):
    wanted = str(
        preferred_gender
        if preferred_gender is not None
        else user.get("interested_in") or ""
    ).strip().lower()

    candidate_gender = _normalize_gender(candidate.get("gender"))

    if not wanted or wanted in {"any", "all", "everyone"}:
        return True

    wanted_gender = _normalize_gender(wanted)

    if wanted_gender == "other":
        return candidate_gender == "other"

    return wanted_gender == candidate_gender


def _compatibility_score(user, candidate, preferences):
    score = 0

    user_age = _safe_int(user["age"], 0)
    candidate_age = _safe_int(candidate["age"], 0)

    # Age compatibility
    min_age = _safe_int(preferences["min_age"], 18)
    max_age = _safe_int(preferences["max_age"], 99)

    if min_age <= candidate_age <= max_age:
        score += 30

    age_difference = abs(user_age - candidate_age)

    if age_difference <= 2:
        score += 15
    elif age_difference <= 5:
        score += 10
    elif age_difference <= 10:
        score += 5

    # Gender / interest compatibility
    preferred_gender = preferences.get("preferred_gender", "any")

    if _is_gender_match(
        user,
        candidate,
        preferred_gender=preferred_gender,
    ):
        score += 25

    # Same city
    user_city = str(user["city"] or "").strip().lower()
    candidate_city = str(candidate["city"] or "").strip().lower()

    if user_city and candidate_city and user_city == candidate_city:
        score += 15

    # Profile quality
    completeness = _profile_completeness(candidate)
    score += round(completeness * 0.10)

    return min(score, 100)


def _boost_bonus(conn, candidate_id):
    row = conn.execute(
        """
        SELECT boost_type
        FROM boosts
        WHERE telegram_id = ?
          AND active = 1
          AND (
              expires_at IS NULL
              OR expires_at > CURRENT_TIMESTAMP
          )
        ORDER BY
            CASE boost_type
                WHEN 'super' THEN 3
                WHEN 'standard' THEN 2
                ELSE 1
            END DESC
        LIMIT 1
        """,
        (candidate_id,),
    ).fetchone()

    if not row:
        return 0

    if row["boost_type"] == "super":
        return 20

    return 10


def _activity_bonus(conn, candidate_id):
    row = conn.execute(
        """
        SELECT last_seen
        FROM user_activity
        WHERE telegram_id = ?
        """,
        (candidate_id,),
    ).fetchone()

    if not row or not row["last_seen"]:
        return 0

    try:
        last_seen = datetime.fromisoformat(
            str(row["last_seen"]).replace("Z", "")
        )
    except ValueError:
        return 0

    age = datetime.now() - last_seen

    if age <= timedelta(hours=1):
        return 10

    if age <= timedelta(hours=24):
        return 5

    return 0


def get_recommendations(user_id, limit=10):
    """
    Return ranked dating recommendations.

    Result:
    [
        {
            "profile": {...},
            "score": 87,
            "reason": "Strong match"
        }
    ]
    """

    conn = get_connection()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id = ?
        """,
        (user_id,),
    ).fetchone()

    if not user:
        conn.close()
        return []

    user = dict(user)

    preferences = get_preferences(user_id)
    seen_users = get_seen_users(user_id)

    candidates = conn.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id != ?
          AND COALESCE(is_incognito, 0) = 0
          AND age IS NOT NULL
          AND city IS NOT NULL
        """,
        (user_id,),
    ).fetchall()

    results = []

    for candidate_row in candidates:
        candidate = dict(candidate_row)
        candidate_id = candidate["telegram_id"]

        if candidate_id in seen_users:
            continue

        candidate_age = _safe_int(candidate["age"], 0)

        if not (
            _safe_int(preferences["min_age"], 18)
            <= candidate_age
            <= _safe_int(preferences["max_age"], 99)
        ):
            continue

        # Preferred gender filter
        preferred_gender = str(
            preferences.get("preferred_gender") or "any"
        ).strip().lower()

        if not _is_gender_match(
            user,
            candidate,
            preferred_gender=preferred_gender,
        ):
            continue

        # Preferred city filter
        preferred_city = str(
            preferences.get("preferred_city") or ""
        ).strip().lower()

        candidate_city = str(
            candidate.get("city") or ""
        ).strip().lower()

        if preferred_city:
            if not candidate_city:
                continue

            if candidate_city != preferred_city:
                continue

        # Distance filter is reserved for profiles with
        # geographic coordinates. The current users schema
        # does not contain latitude/longitude, so do not
        # incorrectly reject profiles based on distance_km.

        score = _compatibility_score(
            user,
            candidate,
            preferences,
        )

        score += _boost_bonus(conn, candidate_id)
        score += _activity_bonus(conn, candidate_id)

        score = min(score, 100)

        if score >= 75:
            reason = "Strong match ❤️"
        elif score >= 55:
            reason = "Good compatibility 💕"
        elif score >= 35:
            reason = "Potential match ✨"
        else:
            reason = "New discovery 🌹"

        results.append(
            {
                "profile": candidate,
                "score": score,
                "reason": reason,
            }
        )

    conn.close()

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return results[:limit]


def get_best_match(user_id):
    matches = get_recommendations(
        user_id=user_id,
        limit=1,
    )

    return matches[0] if matches else None
