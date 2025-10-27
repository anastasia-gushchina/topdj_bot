from aiogram import Bot, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, ChatMemberUpdatedFilter, BaseFilter
from aiogram.enums import ChatType

from src.settings import settings


class ChatTypeFilter(BaseFilter):
    def __init__(self, chat_type: str | list):
        self.chat_type = [chat_type] if isinstance(chat_type, str) else chat_type

    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type in self.chat_type


class GroupFilter(ChatTypeFilter):
    def __init__(self):
        super().__init__([ChatType.GROUP, ChatType.SUPERGROUP])
