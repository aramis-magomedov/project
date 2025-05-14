from db import User, Expense, Category, async_session
from FSM import Reg, Waste, Category_fsm
from kb.kb_inline import kb_options
from kb.kb_reply import kb, kb_right

import asyncio
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.command import Command
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime


router = Router()


@router.callback_query(F.data == "new_user")
async def handle_btn1(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("")
    await state.set_state(Reg.name)
    await callback.message.edit_text("Введи имя нового пользователя")




async def get_dynamic_markup(user_id: int, session_maker) -> ReplyKeyboardMarkup:
    async with session_maker() as session:
        result = await session.execute(
            select(Category.name_categories).where(Category.user_id == user_id)
        )
        categories = result.scalars().all()

    if not categories:
        categories = ["Нет категорий"]

    # Формируем список строк кнопок по 2-3 в ряд (например)
    keyboard = [[KeyboardButton(text=cat)] for cat in categories]

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# Хэндлеры
@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Привет! Давай тратить деньги вместе!")
    await state.set_state(Reg.name)
    await message.answer('Введи своё имя')


@router.message(F.text == '📋 Список расходов')
async def send_users_table(message: types.Message):
    async with async_session() as session:
        result = await session.execute(select(Expense))
        show_amounts = result.scalars().all()
        
        if not show_amounts:
            await message.answer("Пользователей нет в базе")
            return
            
        response = "📋 Список расходов:\n\n"
        sum_amount = 0 
        data_str = ''
        for show_amount in show_amounts:
            time_str = show_amount.created_at.strftime("%H:%M")

            if data_str != show_amount.created_at.strftime("%d.%m.%Y"):
                 data_str = show_amount.created_at.strftime("%d.%m.%Y")
                 response += f"Дата: {data_str}\n\n" 

            response += f"Время: {time_str}\n Категория: {show_amount.category}\n Сумма: {show_amount.amount}\n\n"
            sum_amount += show_amount.amount
        response += f"💵 Общая сумма за день: {sum_amount} руб."
        await message.answer(response)
    

@router.message(Reg.name)
async def cmd_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Reg.surname)
    await message.answer("Теперь введи фамилию")

@router.message(Reg.surname)
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

@router.message(F.text == "🟢 Да,всё верно")
async def show_main_reply(message: types.Message):
    await message.answer(
        "\u2003Отлично👍, если вам понадобится добавить пользователя, вы можете сделать это в пункте\n\"⚙️ Параметры\"",
        reply_markup=kb
    )

@router.message(F.text == "⚙️ Параметры")
async def options(message: types.Message):
    await message.answer("Параметры", reply_markup=kb_options)

@router.message(F.text == "💸 Добавить расход")
async def show_menu_expenses(message: types.Message, state: FSMContext):
    await message.answer("Введите сумму расхода")
    await state.set_state(Waste.sum_waste)

@router.message(Waste.sum_waste)
async def process_sum(message: types.Message, state: FSMContext):
    # try:
    amount = float(message.text)
    await state.update_data(sum_waste=amount)
    await state.set_state(Waste.category)

    dynamic_markup = await get_dynamic_markup(message.from_user.id, async_session)
    await message.answer("Выберите категорию расхода", reply_markup=dynamic_markup)
        # await message.answer("Выберите категорию расхода", reply_markup=markup)
    # except ValueError:
    #     await message.answer("Пожалуйста, введите число!")

@router.message(Waste.category)
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



async def get_categories(user_id: int, session_maker) -> ReplyKeyboardMarkup:
    async with session_maker() as session:
        result = await session.execute(
            select(Category.name_categories).where(Category.user_id == user_id)
        )
        categories = result.scalars().all()

    if not categories:
        categories = ["Нет категорий"]

    # Формируем список строк
    Inline_list_categories = [[InlineKeyboardButton(text=cat, callback_data=cat)] for cat in categories]

    return InlineKeyboardMarkup(inline_keyboard=Inline_list_categories)



@router.message(F.text == "🗑️ Удалить расход")
async def show_main_reply(message: types.Message):
    
    dynamic_list_categories = await get_categories(message.from_user.id, async_session)
    await message.answer("Выберите категорию для удаления", reply_markup=dynamic_list_categories)


@router.callback_query(F.data == "new_category")
async def show_categories(callback, state: FSMContext):
    await callback.answer("")
    await state.set_state(Category_fsm.cats)
    await callback.message.edit_text("Введи новую категорию")



@router.message(Category_fsm.cats)
async def add_category(message: types.Message, state: FSMContext):
    async with async_session() as session:
        # Проверяем, есть ли уже такая категория
        existing = await session.execute(
            select(Category).where(
                Category.name_categories == message.text,
                Category.user_id == message.from_user.id
            )
        )
        

        if existing.scalar():
            await message.answer("Эта категория уже существует!")
            return 
            
        # Добавляем новую категорию
        new_category = Category(
            name_categories=message.text,
            user_id=message.from_user.id
        )
        session.add(new_category)
        await session.commit()
        
    await message.answer(f"Категория '{message.text}' добавлена!")
    await state.clear()