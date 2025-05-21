import gettext

def get_translator(lang_code: str):
    try:
        translator = gettext.translation(
            domain="messages",
            localedir="i18n/locales",
            languages=[lang_code],
            fallback=True
        )
        return translator.gettext
    except Exception:
        return lambda x: x  # fallback
