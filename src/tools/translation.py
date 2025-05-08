from db.database import BotDB
from gettext import translation, install
from tools.logger import logger
import os

# Initialize the database
db = BotDB()

# Load translations
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCALES_DIR = os.path.join(BASE_DIR, "..", "i18n")

try:
    TRANSLATIONS = {
        "en": translation("messages", localedir=LOCALES_DIR, languages=["en"], fallback=True),
        "fa": translation("messages", localedir=LOCALES_DIR, languages=["fa"], fallback=True),
    }
    logger.info("Translations loaded successfully.")
except Exception as e:
    logger.error(f"Error loading translations: {e}")
    TRANSLATIONS = {}

# Default to English
TRANSLATIONS.get("en", translation("messages", localedir=LOCALES_DIR, languages=["en"], fallback=True)).install()

def set_language(language_code: str):
    """Set the active translation language."""
    if language_code in TRANSLATIONS:
        TRANSLATIONS[language_code].install()
    else:
        TRANSLATIONS["en"].install()
        logging.warning(f"Language {language_code} not found. Defaulting to English.")

def translate(language_code: str, message: str) -> str:
    """Translate a message to the specified language."""
    return TRANSLATIONS.get(language_code, TRANSLATIONS["en"]).gettext(message)

async def get_user_language(user_id: int, default_language: str = "en") -> str:
    """Retrieve the user's language preference from the database."""
    try:
        user_config = await db.get_user_config(user_id)
        return user_config.get("language", default_language) if user_config else default_language
    except Exception as e:
        logger.error(f"Error retrieving user language for user_id {user_id}: {e}")
        return default_language
