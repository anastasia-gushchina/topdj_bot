# pseudo translation
_t = lambda x: x  # noqa: E731

LANGS = {
    "en": {"name": "English [en]", "keys": ["[en]", "english"], "t": "English"},
    # "pt": {"name": "Português [pt]", "keys": ["[pt]", "português"], "t": "Portuguese"},
    "ru": {"name": "Русский [ru]", "keys": ["[ru]", "русский"], "t": "Russian"},
}

BOT_DESCRIPTION = _t("Привет, я бот TopDJ School и я помогу тебе купить наши паки с музыкой")

COMMANDS = {
    "/start": _t("Получить список паков"),
}
