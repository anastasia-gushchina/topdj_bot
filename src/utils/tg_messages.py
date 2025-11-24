
import requests
from src.settings import settings
import logging

logger = logging.Logger(__name__)


async def send_tg_message(message: str, chat_id: int | None = None):

    bot_token = settings.bot_token
    if chat_id is None:
        chat_id = settings.notification_admin_chat_id
    error = False

    try:
        url = f"https://api.telegram.org/bot{str(bot_token)}/sendMessage"
        params = {
            "chat_id": str(chat_id),
            "parse_mode": "Markdown",
            "text": message
            }
        requests.get(url, params=params)
    except Exception as e:
        error = True
        logger.error(f"Can not send notification message: {e}")
    return "ERROR" if error else "OK"
