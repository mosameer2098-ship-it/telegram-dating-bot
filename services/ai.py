import asyncio
from google import genai
from config import GEMINI_API_KEY

MODEL = "gemini-3.8-flash"

_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


async def generate_bio(name: str, age: int, city: str, gender: str, interested_in: str) -> str:
    if not _client:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    prompt = f"""
Create a short, attractive dating profile bio for a Telegram dating app.

Profile:
Name: {name}
Age: {age}
City: {city}
Gender: {gender}
Interested in: {interested_in}

Rules:
- 2 to 4 short sentences.
- Romantic, friendly and natural.
- Do not invent specific hobbies, job, education or personal facts.
- Do not mention that AI wrote the bio.
- No sexual or explicit content.
- Keep it suitable for a general dating app.
- Return only the bio text.
"""

    response = await asyncio.to_thread(
        _client.models.generate_content,
        model=MODEL,
        contents=prompt,
    )

    bio = (response.text or "").strip()

    if not bio:
        raise RuntimeError("Gemini returned an empty response.")

    return bio


async def generate_icebreaker(
    user_name: str,
    user_city: str,
    user_bio: str,
    match_name: str,
    match_city: str,
    match_bio: str,
) -> str:
    if not _client:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    prompt = f"""
Create one natural first-message icebreaker for a dating match.

Person:
Name: {user_name}
City: {user_city}
Bio: {user_bio or "No bio"}

Match:
Name: {match_name}
City: {match_city}
Bio: {match_bio or "No bio"}

Rules:
- One short message, maximum 2 sentences.
- Friendly, warm and natural.
- Use only information actually provided.
- Do not invent hobbies, interests, jobs or facts.
- Do not be sexual or explicit.
- Do not mention AI.
- Avoid generic "Hi, how are you?" if a profile detail can be used.
- Return only the icebreaker message.
"""

    response = await asyncio.to_thread(
        _client.models.generate_content,
        model=MODEL,
        contents=prompt,
    )

    icebreaker = (response.text or "").strip()

    if not icebreaker:
        raise RuntimeError("Gemini returned an empty response.")

    return icebreaker
