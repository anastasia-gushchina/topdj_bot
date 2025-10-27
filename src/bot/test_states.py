from aiogram import types, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

test_router = Router(name="test")


# Определяем состояния (цепочку)
class Form(StatesGroup):
    name = State()
    age = State()
    city = State()


# Старт команды — начало цепочки
@test_router.message(Command("test"))
async def start(message: types.Message, state: FSMContext):
    await message.answer("Привет! Давай познакомимся. Как тебя зовут?")
    await state.set_state(Form.name)


# Получаем имя и запрашиваем возраст
@test_router.message(Form.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(Form.age)


# Получаем возраст и запрашиваем город
@test_router.message(Form.age)
async def process_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи число.")
        return
    await state.update_data(age=int(message.text))
    await message.answer("Из какого ты города?")
    await state.set_state(Form.city)


# Получаем город и завершаем цепочку
@test_router.message(Form.city)
async def process_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    data = await state.get_data()
    await message.answer(f"Отлично! Ты — {data['name']}, тебе {data['age']} лет, и ты из {data['city']}.")

    await state.clear()  # Завершаем состояние
