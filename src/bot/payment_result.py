
import logging
from urllib.parse import urljoin
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
from src.utils.tg_messages import send_tg_message

logger = logging.Logger(__name__)

payment_result_router = Router(name="payment_result")


async def change_status(from_status, to_status, user_id: int, transaction_id: str | None = None):

    filter_ = {"user_id": user_id,
               "status": from_status.value}
    update_schema = UpdatePaymentsSchema(status=to_status.value)
    if transaction_id:
        update_schema.transaction_id = transaction_id
    try:
        await PaymentService().update(filter_, schema=update_schema)
    except Exception as e:
        await send_tg_message(f"Не получилось перевести статус платежа: {filter_}: {str(e.__traceback__)}")


@payment_result_router.pre_checkout_query()
async def pre_checkout_query(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    await change_status(PaymentStatus.payment_started, PaymentStatus.transaction_created,
                        user_id=pre_checkout_query.from_user.id,
                        transaction_id=pre_checkout_query.id)


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
        found_pack = (await PaymentService().get_list(filter_={"user_id": message.from_user.id}))
        if found_pack:
            pack_name = found_pack[-1].pack_name
        else:
            await incorrect_db_condition(message)
            return
    pack: MusicPack = get_pack_by_name_or_category(pack_name)
    await message.answer(f"Спасибо за оплату пака {pack.human_name}, сейчас пришлю архив")

    doc = pack.document_id
    if doc is None:
        path_to_doc = urljoin(settings.files_path, pack.file_name)
        doc = FSInputFile(path=path_to_doc)

    await message.answer_document(doc, protect_content=True)
    await send_tg_message(f"Пользователь @{message.from_user.username} успешно купил пак {pack.human_name}")
    await change_status(PaymentStatus.transaction_created, PaymentStatus.transaction_completed,
                        user_id=message.from_user.id)
