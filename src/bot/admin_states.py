
from aiogram import F, types, Router
from src.settings import settings
from logging import Logger

logger = Logger(__name__)

admin_router = Router(name="admin")


@admin_router.message(F.forward_origin.is_not(None))
async def only_forwarded_message_handler(message: types.Message):
    if message.from_user.id in settings.admins_ids:
        await message.answer("Here is document id:")
        mes = f"{message.document.file_name} - {message.document.file_id}"
        await message.answer(mes)
