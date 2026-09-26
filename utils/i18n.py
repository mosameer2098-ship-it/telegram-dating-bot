from utils.locales.en import TEXTS as EN
from utils.locales.hi import TEXTS as HI
from utils.locales.hinglish import TEXTS as HINGLISH
from utils.locales.bn import TEXTS as BN

LANGUAGES = {
    "en": EN,
    "hi": HI,
    "hinglish": HINGLISH,
    "bn": BN,
}

DEFAULT_LANGUAGE = "en"


def get_text(key, language="en"):
    texts = LANGUAGES.get(language, EN)
    return texts.get(key, EN.get(key, key))


def get_language_name(code):
    names = {
        "en": "🇬🇧 English",
        "hi": "🇮🇳 हिन्दी",
        "hinglish": "🇮🇳 Hinglish",
        "bn": "🇧🇩 বাংলা",
    }
    return names.get(code, "🇬🇧 English")


def supported_languages():
    return list(LANGUAGES.keys())
