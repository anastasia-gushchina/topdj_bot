from typing import Callable

from aiogram import types, F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import Bot, types
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.i18n import gettext as _
from src.bot.utils.helper import chunk_list_safe, escape_markdown

MAX_BUTTONS_COUNT = 12


class IncorrextInput(Exception): ...


class SelectableList(StatesGroup):
    """
    Базовый класс для создания FSM-состояния, в котором пользователь выбирает элемент из списка.

    Класс автоматически регистрирует обработчики:
    - Первого сообщения или callback'а (открытие списка)
    - Выбора элемента из списка (по тексту или кнопке)
    - Пагинации (если включена)

    Атрибуты класса:
    ----------------
    select : State
        Обязательное состояние выбора (должно быть переопределено в подклассе).

    buttons : bool
        Включить генерацию кнопок для выбора. По умолчанию True.

    pagination : bool
        Включить пагинацию по страницам. По умолчанию True.

    limit : int
        Количество элементов на странице. По умолчанию 1.

    first_message_route : Optional[Route]
        Роутер для первого сообщения. Если None — используется `route.message`.

    route : Router
        Обязательный роутер, к которому будет подключён выбор.

    filters : list
        Фильтры для регистрации начального хендлера (обычно `F.data == "..."` и т.п.).

    input_type : Callable
        Тип преобразования ввода (например, int). Если невалидный ввод — будет сообщение об ошибке.
        Обработчик ввода с клавиатуры, может быть функция, которая кидает exception.
        Сallble[str], вернуть уже в формате данных, котрый необходим для обработки
        ```python
        def type_input(s: str) -> int:
            if str == "error":
                raise Exception()
            return int(s)
        ```

    Методы, которые нужно переопределить:
    -------------------------------------
    - get_list(limit, offset) -> tuple[dict, int]
        Возвращает словарь элементов и общее число элементов.

    - get_one(pk)
        Получает элемент по ключу. Используется для валидации.

    - on_select_end(cls, selected_id, message, state) -> State | None
        Логика завершения выбора. Вызывается после успешного выбора.

    Методы, которые можно переопределить:
    -------------------------------------
    - list_format_to_telegram(data) -> str
        Форматирование для отправки сообзения в телеграм

    Пример использования:
    ---------------------
    ```python
    TEST_DATA = {1: "Элемент 1", 2: "Элемент 2"}

    class SetGroupRole(SelectableList):
        select = State()
        next_state = State()

        pagination = False
        route = test_route
        input_type = int
        filters = [F.data == "type"]

        @classmethod
        async def on_select_end(cls, selected_id, source: types.Message | types.CallbackQuery, state: FSMContext):
            # cls.respond т.к. может быть callback, либо message
            await cls.respond(source, text=f"Вы выбрали {escape_markdown(str(selected_id))}")
            return cls.next_state # либо None

        @staticmethod
        async def get_list(limit, offset):
            return TEST_DATA, len(TEST_DATA)

        @staticmethod
        async def get_one(pk):
            return TEST_DATA.get(pk)
    ```
    """

    select = State()

    # params
    buttons: bool = True
    pagination: bool = True
    limit: int = 10
    first_message_route: bool = False
    route: Router = None
    filters: list = []
    input_type: type | Callable = int
    list_parse_mode = ParseMode.MARKDOWN_V2

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if "select" not in cls.__dict__:
            raise TypeError(f"{cls.__name__} must override `select` State from SelectableList")

        if cls.route is None:
            raise ValueError(f"{cls.__name__} must define `route`")

        cls._register_handlers()

    @classmethod
    def _page_prefix(cls) -> str:
        return f"{cls.__name__}_page_"

    @classmethod
    def _parse_page(cls, data: str) -> int:
        return int(data[len(cls._page_prefix()) :])

    @classmethod
    def _is_page(cls, data: str) -> bool:
        return data.startswith(cls._page_prefix())

    @classmethod
    def _register_handlers(cls):
        route = cls.route
        filters = cls.filters
        first_route = cls.first_message_route or route.message

        @first_route(*filters)
        async def start_selection(message: types.Message, state: FSMContext, bot: Bot):
            await cls._send_page(message, state, bot, page=0)

        if cls.pagination:

            @route.callback_query(cls.select, F.data.startswith(cls._page_prefix()))
            async def paginate(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
                page = cls._parse_page(callback.data)
                await callback.message.delete()
                await cls._send_page(callback.message, state, bot, page=page)

        @route.message(cls.select, ~F.data.startswith(cls._page_prefix()))
        async def handle_selection_message(message: types.Message, state: FSMContext):
            await cls._handle_selection(message.text.strip(), message, state)

        if cls.buttons:

            @route.callback_query(cls.select, ~F.data.startswith(cls._page_prefix()))
            async def handle_selection_callback(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
                await cls._handle_selection(callback.data.strip(), callback, state, bot)

    @classmethod
    async def _handle_selection(
        cls, input_text: str, source: types.Message | types.CallbackQuery, state: FSMContext, bot: Bot = None
    ):
        try:
            selected_id = cls.input_type(input_text)
        except Exception:
            await cls.respond(source, bot, text=_("Некорректный ввод."))
            return

        item = await cls.get_one(selected_id)
        if not item:
            await cls.respond(source, bot, text=_("Элемент не найден."))
            return

        try:
            new_state = await cls.on_select_end(selected_id, source, state)
            await state.set_state(new_state)
        except IncorrextInput as e:
            await cls.respond(source, bot, text=str(e))

    @classmethod
    async def _send_page(cls, message: types.Message, state: FSMContext, bot: Bot, page: int):
        offset = page * cls.limit
        dict_, total = await cls.get_list(cls.limit, offset)

        text = await cls.list_format_to_telegram(dict_)

        keyboard = cls._build_keyboard(dict_.keys(), page, offset, total)
        await cls.respond(message, text=text, reply_markup=keyboard, parse_mode=cls.list_parse_mode)

        await state.set_state(cls.select)
        await state.update_data(page=page)

    @classmethod
    def _build_keyboard(cls, keys, page: int, offset: int, total: int) -> InlineKeyboardMarkup | None:
        keyboard = []

        nav_buttons = []
        if cls.pagination:
            if offset > 0:
                nav_buttons.append(InlineKeyboardButton(_("⬅️ Назад"), callback_data=f"{cls._page_prefix()}{page - 1}"))
            if offset + cls.limit < total:
                nav_buttons.append(InlineKeyboardButton(_("➡️ Далее"), callback_data=f"{cls._page_prefix()}{page + 1}"))

        if cls.buttons and cls.limit <= MAX_BUTTONS_COUNT - len(nav_buttons):
            key_buttons = [InlineKeyboardButton(text=str(k), callback_data=str(k)) for k in keys]
            keyboard.extend(chunk_list_safe(key_buttons, 2))

        if nav_buttons:
            keyboard.append(nav_buttons)

        return InlineKeyboardMarkup(inline_keyboard=keyboard) if keyboard else None

    @classmethod
    async def on_select_end(cls, pk, source: types.Message | types.CallbackQuery, state: FSMContext) -> State | None:
        raise NotImplementedError

    @classmethod
    async def respond(cls, r: types.Message | types.CallbackQuery, bot: Bot = None, **kwargs):
        if isinstance(r, types.CallbackQuery):
            await (bot or r.message.bot).send_message(r.message.chat.id, **kwargs)
        else:
            await r.answer(**kwargs)

    @staticmethod
    async def get_list(limit: int, offset: int) -> tuple[dict, int]:
        """
        Возвращает:
            dict: элементы {id: label}, label должен быть экранирован с помощью escape_markdown
            int: общее количество элементов
        """
        raise NotImplementedError

    @staticmethod
    async def get_one(pk):
        raise NotImplementedError

    @staticmethod
    async def list_format_to_telegram(data: dict):
        # подразумивается, что v уже escape_markdown
        items = [f"`{escape_markdown(str(k))}`\\) {v}" for k, v in data.items()]
        return "\n\n".join(items) + _("\n\nВведите ключ нужного элемента:")
