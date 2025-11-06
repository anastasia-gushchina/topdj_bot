import logging
import traceback
from typing import Annotated  # , Callable
from urllib.parse import urljoin
import aiogram
from aiogram import types
from aiogram.types import BotCommand
from fastapi import Request, APIRouter, Header
from aiogram.fsm.storage.redis import RedisStorage
from redis import StrictRedis

from src.config import LANGS, BOT_DESCRIPTION, COMMANDS
from src.settings import settings

logger = logging.getLogger(__name__)

bot = aiogram.Bot(token=settings.bot_token)
dp = aiogram.Dispatcher(
    bot=bot,
    storage=RedisStorage.from_url(settings.redis_url),
)
redis = None
try:
    redis = StrictRedis(host=settings.redis_host, port=settings.redis_port, db=settings.redis_db,
                        password=settings.redis_password, socket_connect_timeout=600)
    if redis.ping():
        logger.info('Redis is accepted to connections')
    else:
        logger.error('Can not connect to redis')
except Exception as e:
    logger.error(f"Can not connect to redis: {e}")


webhook_router = APIRouter()


def get_menu(lang: str, debug: bool = False) -> list[BotCommand]:
    commands = [BotCommand(command=key, description=text) for key, text in COMMANDS.items()]
    return commands


async def bot_startup():

    full_url = urljoin(settings.bot_webhook_url, settings.bot_webhook_path)
    try:
        webhook_info = await bot.get_webhook_info()
        logger.error(webhook_info)
        if webhook_info.url != full_url:
            logger.info(f"Change webhook URL to {full_url}")
            res = await bot.set_webhook(
                url=full_url,
                secret_token=settings.bot_webhook_secret,
                drop_pending_updates=webhook_info.pending_update_count > 0,
                max_connections=40 if settings.debug else 100,
            )
            logger.error(res)
        else:
            logger.info(f"Webhook URL already set to {full_url}")

        for lang in LANGS.keys():
            commands = get_menu(lang)
            try:
                logger.debug("Order startup = %s", str(commands))
                await bot.set_my_commands(
                    commands=commands, language_code=lang, scope=aiogram.types.BotCommandScopeAllPrivateChats()
                )
            except Exception as e:
                logger.error(f"Can't set commands {lang} - {e}")

            try:
                logger.debug(f"Order desc = {BOT_DESCRIPTION}, lang={lang}")
                await bot.set_my_description(description=BOT_DESCRIPTION, language_code=lang)
            except Exception as e:
                logger.error(f"Can't set not description {lang} - {e}")

    except Exception:
        logger.exception("Can't register webhook")


async def bot_shutdown():
    try:
        if bot.session:
            await bot.session.close()
    except Exception:
        logger.exception("Error while close bot session")


@webhook_router.post(settings.bot_webhook_path)
async def bot_webhook(
    r: Request, update: dict, x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None
) -> None:
    if x_telegram_bot_api_secret_token != settings.bot_webhook_secret:
        logger.error("Wrong secret token in webhook!")
        return {"status": "error", "message": "Wrong secret token!"}
    telegram_update = types.Update(**update)
    try:
        await dp.feed_webhook_update(bot=bot, update=telegram_update)
    except Exception:
        logger.error(traceback.format_exc())
    return {"status": "done"}
