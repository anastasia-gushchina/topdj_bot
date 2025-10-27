
import logging
from urllib.parse import urljoin
import requests
from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    PreCheckoutQuery,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile
)

from src.schemas.payments import UpdatePaymentsSchema, PaymentStatus
from src.services.payments import PaymentService
from src.models.music_pack import MusicPack, get_pack_by_name_or_category
from src.settings import settings

logger = logging.Logger(__name__)

payment_result_router = Router(name="payment_result")


async def send_tg_message(message: str):

    bot_token = settings.bot_token

    # send only to tg_bot, not for users
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


@payment_result_router.pre_checkout_query()
async def pre_checkout_query(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    update_schema = UpdatePaymentsSchema(status=PaymentStatus.transaction_created, transaction_id=pre_checkout_query.id)
    await PaymentService().update(pre_checkout_query.from_user.id, schema=update_schema)


async def incorrect_db_condition(message: Message):
    chat_id = settings.notification_admin_chat_id
    button_url = f'tg://openmessage?user_id={chat_id}'
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="Написать админу", url=button_url))
    await message.answer(text="Спасибо за оплату, напишите администратору \
                         и прикрепите сообщения с оплатой и выбранным паком, чтобы получить его", reply_markup=markup)


@payment_result_router.message(F.successful_payment)
async def successful_payment(message: Message, state: FSMContext):

    pack_name = (await state.get_data()).get("pack_name")
    if not pack_name:
        found_pack = (await PaymentService().get_by_user_id(message.from_user.id))
        if found_pack:
            pack_name = found_pack.pack_name
        else:
            await incorrect_db_condition(message)
            return
    pack: MusicPack = get_pack_by_name_or_category(pack_name)
    await message.answer(f"Спасибо за оплату пака {pack.human_name}, сейчас пришлю архив")

    # TODO: send message to admin
    # update to db

    # protect content to document
    path_to_doc = urljoin(settings.files_path, pack.file_name)
    doc = FSInputFile(path=path_to_doc)
    await message.answer_document(doc)
