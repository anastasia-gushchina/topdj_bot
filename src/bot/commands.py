from aiogram import types, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

commands_router = Router(name="commands")


@commands_router.message(Command("start"))
async def cmd_id(message: types.Message) -> None:
    await message.answer(_("Hi"))


@commands_router.message(Command("id"))
async def cmd_id(message: types.Message) -> None:
    await message.answer(f"Your ID: {message.from_user.id}")


@commands_router.message(Command("debug"))
async def cmd_debug(message: types.Message, state: FSMContext) -> None:
    await message.answer(text=repr(message))
    await message.answer(text=repr(await state.get_data()))
    await message.answer(text=repr(await state.get_state()))
