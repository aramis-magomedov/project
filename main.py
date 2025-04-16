# 

import asyncio
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token="7793831868:AAGMDKY-PnVtVDm4cIZQx5ckMdg3OJ7_9bU")
dp = Dispatcher()

# Настройка базы данных
DATABASE_URL = "sqlite+aiosqlite:///db.db"
Base = declarative_base()

# Модель пользователя
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    name = Column(String)
    surname = Column(String)
    created_at = Column(DateTime, default=datetime.now)

# Модель расхода
class Expense(Base):
    __tablename__ = 'expenses'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    category = Column(String)
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.now)

# Создаем асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Создаем таблицы при старте
async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Состояния для FSM
class Reg(StatesGroup):
    name = State()
    surname = State()
    password = State()

class Waste(StatesGroup):
    category = State()
    sum_waste = State()

# Клавиатуры
kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Добавить расход"), KeyboardButton(text="Удалить расход")],
        [KeyboardButton(text="Запланировать расход")],
        [KeyboardButton(text="Параметры")]
    ],
    resize_keyboard=True,
)

kb_right = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Да,всё верно"), KeyboardButton(text="Нет,ввести данные заново")]
    ],
    resize_keyboard=True,
)

kb_options = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Добавить нового пользователя", url="https://example.com")],
    [InlineKeyboardButton(text="Добавить категорию расхода", url="https://example.com")]
])

markup = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Еда"), KeyboardButton(text="Транспорт"), KeyboardButton(text="Развлечения")]
    ],
    resize_keyboard=True,
)

# Хэндлеры
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Привет! Давай тратить деньги вместе!")
    await state.set_state(Reg.name)
    await message.answer('Введи своё имя')

@dp.message(Reg.name)
async def cmd_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Reg.surname)
    await message.answer("Теперь введи фамилию")

@dp.message(Reg.surname)
async def cmd_surname(message: types.Message, state: FSMContext):
    await state.update_data(surname=message.text)
    data = await state.get_data()
    
    # Сохраняем пользователя в БД
    async with async_session() as session:
        user = User(
            telegram_id=message.from_user.id,
            name=data["name"],
            surname=data["surname"]
        )
        session.add(user)
        await session.commit()
    
    await message.answer(f'Имя: {data["name"]} Фамилия: {data["surname"]}')
    await message.answer("Верно?", reply_markup=kb_right)
    await state.clear()

@dp.message(F.text == "Да,всё верно")
async def show_main_reply(message: types.Message):
    await message.answer(
        "Отлично, если вам понадобится добавить пользователя, вы можете сделать это в пункте \"Параметры\"",
        reply_markup=kb
    )

@dp.message(F.text == "Параметры")
async def options(message: types.Message):
    await message.answer("Параметры", reply_markup=kb_options)

@dp.message(F.text == "Добавить расход")
async def show_menu_expenses(message: types.Message, state: FSMContext):
    await message.answer("Введите сумму расхода")
    await state.set_state(Waste.sum_waste)

@dp.message(Waste.sum_waste)
async def process_sum(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        await state.update_data(sum_waste=amount)
        await state.set_state(Waste.category)
        await message.answer("Выберите категорию расхода", reply_markup=markup)
    except ValueError:
        await message.answer("Пожалуйста, введите число!")

@dp.message(Waste.category)
async def process_category(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    # Сохраняем расход в БД
    async with async_session() as session:
        expense = Expense(
            user_id=message.from_user.id,
            category=message.text,
            amount=data["sum_waste"]
        )
        session.add(expense)
        await session.commit()
    
    await message.answer(
        f'''{datetime.now().strftime("%d/%m/%Y %H:%M")}
Категория: {message.text}
Сумма: {data["sum_waste"]}''',
        reply_markup=kb
    )
    await state.clear()

async def main():
    await init_models()  # Инициализация БД
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())