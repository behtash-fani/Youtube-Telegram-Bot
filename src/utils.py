from database import Database
from gettext import translation
import logging
import os

# Initialize the database
db = Database("bot_database.db")

# Load translations
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCALES_DIR = f"{BASE_DIR}/locales"
try:
    TRANSLATIONS = {
        "en": translation("messages", localedir=LOCALES_DIR, languages=["en"]),
        "fa": translation("messages", localedir=LOCALES_DIR, languages=["fa"]),
    }
    logging.info("Translations loaded successfully.")
except Exception as e:
    logging.error(f"Error loading translations: {e}")
    TRANSLATIONS = {}


def set_language(language_code: str):
    """Set the active translation language."""
    if language_code in TRANSLATIONS:
        TRANSLATIONS[language_code].install()
    else:
        TRANSLATIONS["en"].install()

def translate(language_code: str, message: str) -> str:
    """Translate a message to the specified language."""
    if language_code in TRANSLATIONS:
        return TRANSLATIONS[language_code].gettext(message)
    return message

async def get_user_language(user_id: int, default_language: str = "en") -> str:
    """Retrieve the user's language preference from the database."""
    try:
        user_config = await db.get_user_config(user_id)
        return user_config.get("language", default_language) if user_config else default_language
    except Exception as e:
        logging.error(f"Error retrieving user language for user_id {user_id}: {e}")
        return default_language