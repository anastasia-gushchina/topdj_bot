
from aiogram import F, types, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup
from src.schemas.payments import CreatePaymentsSchema, PaymentStatus
from src.services.payments import PaymentService
from src.settings import settings
from src.models.music_pack import MusicPack, get_pack_price, Categories, get_pack_by_name_or_category
from src.services.users import UsersService
from src.schemas.users import CreateUserSchema
from logging import Logger
from src.bot_main import redis
from src.utils.tg_messages import send_tg_message


logger = Logger(__name__)

purchase_router = Router(name="purchase_pack")


class Form(StatesGroup):
    pack_category = State()
    pack_name = State()
    pack_info = State()
    new_invoice = State()
    create_new_pack = State()


async def start(message: types.Message, state: FSMContext):
    inline_kb_list = [
        [InlineKeyboardButton(text=category.value, callback_data=f"pack_category_{category.value}")]
        for category in Categories
    ]
    inline_kb_list.append([InlineKeyboardButton(text="Хочу заказать пак в другом жанре!",
                                                callback_data="create_new_pack")])
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_kb_list)
    create_user = CreateUserSchema(username=message.from_user.username,
                                   name=message.from_user.first_name,
                                   surname=message.from_user.last_name,
                                   tg_id=message.from_user.id,
                                   chat_id=message.chat.id,
                                   )
    await UsersService().check_and_create(create_user, redis)

    await message.answer(text="Мы рады, что тебя заинтересовал наш TOPDJ MUSIC PACK!\n\nВыбери интересующий тебя жанр🤩",
                         reply_markup=inline_keyboard)
    await state.set_state(Form.pack_category)


@purchase_router.callback_query(F.data.startswith("pack_category_"))
async def pack_name(callback: types.CallbackQuery, state: FSMContext):
    category_name = callback.data.replace("pack_category_", "")
    packs_dict = get_pack_by_name_or_category(category_name)
    inline_kb_list = [
        [InlineKeyboardButton(text=pack.human_name, callback_data=f"pack_name_{pack.name}")]
        for _, pack in packs_dict.items()
    ]
    inline_kb_list.append([InlineKeyboardButton(text="Хочу заказать другой пак!",
                                                callback_data="create_new_pack")])
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_kb_list)

    desc = f"Вот доступные паки в категории {category_name}. Во всех наших паках уникальные наборы треков.\
    \n\nА если тут нет нужного тебе пака, то ты всегда можешь заказать создание нового"
    await callback.message.answer(text=desc, reply_markup=inline_keyboard)
    await state.set_state(Form.pack_name)


@purchase_router.message(Command("start"))
async def start_bot(message: types.Message, state: FSMContext):
    await start(message, state)


@purchase_router.callback_query(F.data.startswith("create_new_pack"))
async def create_new_pack(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Form.create_new_pack)
    message = "Опиши пак, который хочешь купить:\n\
    1. В каком он должен быть жанре или поджанре\n\
    2. Сколько треков в нём должно быть\n\
    3. Любые комментарии на счёт пака, которые ты считаешь важными."
    await callback.message.answer(text=message)


@purchase_router.message(Form.create_new_pack)
async def get_new_pack_info(message: types.Message, state: FSMContext):
    user_request = message.text
    username = message.from_user.username
    message_text = f"Пользователь @{username} описал особый пак, который хотел бы купить:\n\n {user_request}"
    await send_tg_message(message_text)
    await message.answer(text="✅ Получили твои пожелания, когда пак будет готов наш администратор сообщит об этом")
    await state.clear()


@purchase_router.callback_query(F.data.startswith("pack_name_"))
async def process_name(callback: types.CallbackQuery, state: FSMContext):
    pack_name = callback.data.replace("pack_name_", "")
    logger.error(f"Pack name: {pack_name}")
    cur_pack = get_pack_by_name_or_category(pack_name)
    if cur_pack is None:
        await callback.message.answer("Пожалуйста, выбери пак из списка")
        return

    description = f"{cur_pack.human_name} - отличный выбор!\
        \nЗдесь собраны самые свежие треки в отличном качестве🎧\
        \n\nКоличество треков в паке: {cur_pack.track_count}\
        \nCтоимость: {cur_pack.cost/100} RUB"

    inline_kb_list = [
        [InlineKeyboardButton(text="Беру этот pack", callback_data=f"buy_pack_{pack_name}")]
        ]
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_kb_list)
    await callback.message.answer(text=description, reply_markup=inline_keyboard)
    await state.set_state(Form.pack_info)


@purchase_router.callback_query(F.data.startswith("buy_pack_"))
async def start_buy(callback: types.CallbackQuery, state: FSMContext):
    pack_name = callback.data.replace("buy_pack_", "")
    await state.update_data(pack_name=pack_name)
    cur_pack: MusicPack = get_pack_by_name_or_category(pack_name)
    pack_price = get_pack_price(pack_name)

    pack_price = types.LabeledPrice(label=f"Оплата за музыкальный пак {cur_pack.human_name}", amount=pack_price)
    invoice = await callback.message.answer_invoice(
        title="Оплата музыкального пака",
        description=f"Внеси оплату за пак {cur_pack.human_name} и я пришлю тебе его",
        provider_token=settings.bot_payments_token,
        currency="rub",
        # photo_url="https://www.aroged.com/wp-content/uploads/2022/06/Telegram-has-a-premium-subscription.jpg",
        # photo_width=416,
        # photo_height=234,
        # photo_size=416,
        is_flexible=False,
        prices=[pack_price],
        start_parameter="music_pack_payment",
        payload="pack-invoice-payload")
    logger.debug(invoice.dict())
    new_payment = CreatePaymentsSchema(user_id=str(callback.from_user.id),
                                       status=PaymentStatus.payment_started,
                                       transaction_id=None,
                                       pack_name=pack_name
                                       )
    await PaymentService().create(new_payment)
    await state.set_state(Form.new_invoice)
