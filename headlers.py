from db import User, Expense, Category, async_session
from FSM import Reg, Waste, Category_fsm
from kb.kb_inline import kb_options, kb_register_user
from kb.kb_reply import kb, kb_right, kb_cancel_FSM

import asyncio
from aiogram import types, Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.command import Command
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime


router = Router()


# @router.callback_query(F.data == "new_user")
# async def handle_btn1(callback: types.CallbackQuery, state: FSMContext):
#     await callback.answer("")
#     await state.set_state(Reg.name)
#     await callback.message.edit_text("Введи имя нового пользователя")




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
    keyboard.append([KeyboardButton(text="Отмена")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# Хэндлеры


# Вызов гланого меню через меню бургер
@router.message(Command("main_menu"))
async def cmd_start(message: types.Message):
    await message.answer("Вызов главного меню", reply_markup=kb)



@router.message(F.text == '📋 Список расходов')
async def send_users_table(message: types.Message):
    async with async_session() as session:
        result = await session.execute(select(Expense))
        show_amounts = result.scalars().all()
        
        if not show_amounts:
            await message.answer("Расходов нет в базе")
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


# Регистарциия пользователя
@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Привет! Давай тратить деньги вместе!", reply_markup=kb_register_user)
    await state.set_state(Reg.registry_or_auth)

# Если пользователь регистрируется
@router.callback_query(F.data == "register_callback")
async def cmd_start(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(registry_or_auth='registration')
    await callback.message.answer('Введи своё имя')
    await state.set_state(Reg.name)

# Если пользователь аутентифицируется
@router.callback_query(F.data == "auth_callback")
async def cmd_start(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(registry_or_auth='authentication')
    await state.set_state(Reg.name)
    await callback.message.answer('Введи своё имя')
    
# Пользователь вводит имя
@router.message(Reg.name)
async def cmd_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Reg.surname)
    await message.answer("Теперь введи фамилию")


# Потльзователь вводит фамилию
@router.message(Reg.surname)
async def cmd_surname(message: types.Message, state: FSMContext):
    await state.update_data(surname=message.text)
    await state.set_state(Reg.password)
    await message.answer("Введите пароль")

# Пользователь вводит пароль и проверяет корректость введенных данных
@router.message(Reg.password)
async def cmd_surname(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)
    data = await state.get_data()
    
    await message.answer(f'Имя: {data["name"]} Фамилия: {data["surname"]} //n Пароль:{data["password"]}')
    await state.set_state(Reg.cheked)
    await message.answer("Верно?", reply_markup=kb_right)

# Фиксирует корректность данных
@router.message(Reg.cheked)
async def show_main_reply(message: types.Message, state: FSMContext):
    data = await state.get_data()
    # Сохраняем пользователя в БД, если пользователь регистрируется
    if data["registry_or_auth"] =='registration':
        if message.text == "🟢 Да,всё верно":
            async with async_session() as session:
                user = User(
                    id=message.from_user.id,
                    name=data["name"],
                    surname=data["surname"],
                    password=data["password"]
                )
                session.add(user)
                await session.commit()
                await message.answer(
                "\u2003Отлично👍, если вам понадобится добавить пользователя, вы можете сделать это в пункте\n\"⚙️ Параметры\"",
                reply_markup=kb)
                await state.clear()

        elif message.text == "🔴 Нет,ввести данные заново":
            await message.answer("А с первого раза нельзя было правильно ввести, чурок?",reply_markup=kb)
            await message.answer("Ничего страшного, попробуем еще раз?")
            await state.clear()
            await state.set_state(Reg.registry_or_auth)
            await message.answer('Введи своё имя', reply_markup=kb_register_user)

        else:
            await message.answer('Там внизу вместо обычной клавиатуры две фигнюшки вышли, куда нибудь туда тыкни')
        
        # Проверяем есть ли такой поользователь в базе данных, если пользователь аутентифицируется
    if data['registry_or_auth'] == 'authentication':
            if (User.telegram_id == message.from_user.id and User.surname == data["surname"] 
                and User.name == data["name"] and User.password == data["password"]):
                await message.answer('Олично, вы вошли в аккаунт')
            else:
                await state.clear()
                await message.answer('Упс, что то пошло не так ')
                await message.answer('Попробуем еще раз',reply_markup=kb_register_user)
                await state.set_state(Reg.registry_or_auth)

                    
              
                        
                        





@router.message(F.text == "⚙️ Параметры")
async def options(message: types.Message):
    await message.answer("Параметры", reply_markup=kb_options)




@router.message(F.text == "🗓 Запланировать расход")
async def show_menu_expenses(message: types.Message, bot: Bot):
    print("Хендлер 🗓 Запланировать расход отработал")

    async with async_session() as session:
        # Получаем пользователя из БД по его Telegram ID
        user = await session.execute(select(User).where(User.id == message.from_user.id))
        user = user.scalar_one_or_none()  # Возвращает None, если пользователя нет
        
        if user and user.IQ_user == 50:  # Проверяем, что пользователь найден и его IQ = 50
            print("Первая проверка IQ отработала")
            await message.answer(
                "Я честно по приколу эту суету добавил. Ты вообще сюда зачем нажал(а)? "
                "Как ты себе представляешь должен работать такой функционал? "
                "Ерундой не занимайся, больше не нажимай сюда."
            )
            user.IQ_user = 49
            await session.commit()
            return



        if user and user.IQ_user == 49:  # Проверяем, что пользователь найден и его IQ = 49
            print("Вторая проверка IQ отработала")
            await message.answer("Успокойся говорю. Хоть что-то в голове держи")
            user.IQ_user = 48
            await session.commit()
            return
    
        if user and user.IQ_user == 48:  # Проверяем, что пользователь найден и его IQ = 48
            await message.answer("Как черт не веди себя, хватит нажимать сюда")
            user.IQ_user = 47
            await session.commit()
            return
        
        if user and user.IQ_user == 47:  # Проверяем, что пользователь найден и его IQ = 47
            await message.answer("Ты че хочешь? Иди делом займись, родителей своих порадуй или прогуляйся, чем целый день за компом сидеть ерундой страдать")
            user.IQ_user = 46
            await session.commit()
            return
        
        if user and user.IQ_user == 46:  # Проверяем, что пользователь найден и его IQ = 46
            await message.answer("Душу твою мотал, не нажимай сюда")
            user.IQ_user = 45
            await session.commit()
            return
        
        if user and user.IQ_user == 45:  # Проверяем, что пользователь найден и его IQ = 45
            await message.answer("Твой нос топтал! Не нажимай сюда!")
            user.IQ_user = 44
            await session.commit()
            return
        
        if user and user.IQ_user == 44:  # Проверяем, что пользователь найден и его IQ = 44
            await message.answer("Если заняться нечем - скажи, там мне огород надо вскопать")
            user.IQ_user = 43
            await session.commit()
            return

        if user and user.IQ_user == 43:
            await message.answer("Давай тогда сам реализуешь эту фукцию, если ты ашалеть какой умный")
            user.IQ_user = 42
            await session.commit()
            return
        
        if user and user.IQ_user == 42:
            await message.answer("Ни хаха уже, по идее")
            user.IQ_user = 41
            await session.commit()
            return
        
        if user and user.IQ_user == 41:
            await message.answer("Упс! Что-то пошло не так. Проверьте интернет соединение")
            user.IQ_user = 40
            await session.commit()
            return
        
        if user and user.IQ_user == 40:
            await message.answer("Упс! Что-то пошло не так. Проверьте интернет соединение")
            user.IQ_user = 39
            await session.commit()
            return
        
        if user and user.IQ_user == 39:
            await message.answer("Упс! Что-то пошло не так. Проверьте интернет соединение")
            user.IQ_user = 38
            await session.commit()
            return
        
        if user and user.IQ_user == 38:
            await message.answer("Упс! Что-то пошло не так. Проверьте интернет соединение")
            user.IQ_user = 37
            await session.commit()
            return
        
        if user and user.IQ_user == 37:
            await message.answer("Упс! Что-то пошло не так. Проверьте интернет соединение")
            user.IQ_user = 36
            await session.commit()
            return
        
        if user and user.IQ_user == 36:
            await message.answer("Упс! Что-то пошло не так. Проверьте интернет соединение")
            user.IQ_user = 35
            await session.commit()
            return

        if user and user.IQ_user == 35:
            await message.answer("Упс! Что-то пошло не так. Проверьте интернет соединение")
            user.IQ_user = 34
            await session.commit()
            return
        
        if user and user.IQ_user == 34:
            await message.answer("Упс! Что-то пошло не так. Проверьте интернет соединение")
            user.IQ_user = 33
            await session.commit()
            return
        
        if user and user.IQ_user == 33:
            await message.answer("Упс! Что-то пошло не так. Кажется вы потеряли свое мужское")
            user.IQ_user = 32
            await session.commit()
            return
        
        if user and user.IQ_user == 32:
            await message.answer("Неугомоный ты внатуре")
            user.IQ_user = 31
            await session.commit()
            return
        
        if user and user.IQ_user == 31:
            await message.answer("Тебя роняли разок в детсве об кафель, да?")
            user.IQ_user = 30
            await session.commit()
            return
        
        if user and user.IQ_user == 30:
            await message.answer("Тебя роняли два раза в детсве об кафель, да?")
            user.IQ_user = 29
            await session.commit()
            return
        
        if user and user.IQ_user == 29:
            await message.answer("Вай блин, три раза в неделю роняли что-ли?")
            user.IQ_user = 28
            await session.commit()
            return
        
        if user and user.IQ_user == 28:
            await message.answer("Э, оставь да уже эту кнопкку!")
            user.IQ_user = 27
            await session.commit()
            return
        
        if user and user.IQ_user == 27:
            await message.answer("Я сейчас удалю тебя из интернета, пять секунд я тебе интернет удалю")
            user.IQ_user = 26
            await session.commit()
            return
        
        if user and user.IQ_user == 26:
            await message.answer("Номер ка дай свой сюда, черт")
            user.IQ_user = 25
            await session.commit()
            return

        if user and user.IQ_user == 25:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await message.answer("Номер говорю дай свой")
            user.IQ_user = 24
            await session.commit()
            return



# Добавление расхода
@router.message(F.text == "💸 Добавить расход")
async def show_menu_expenses(message: types.Message, state: FSMContext):
    await message.answer("Введите сумму расхода", reply_markup=kb_cancel_FSM)
    await state.set_state(Waste.sum_waste)


@router.message(Waste.sum_waste)
async def process_sum(message: types.Message, state: FSMContext):
    if message.text == "Отмена":
       await state.clear()
       await message.answer("Действие отменено", reply_markup=kb)
    else:
        amount = float(message.text)
        await state.update_data(sum_waste=amount)
        await state.set_state(Waste.category)

        dynamic_markup = await get_dynamic_markup(message.from_user.id, async_session)
        await message.answer("Выберите категорию расхода", reply_markup=dynamic_markup)



@router.message(Waste.category)
async def process_category(message: types.Message, state: FSMContext):
    if message.text == "Отмена":
       await state.clear()
       await message.answer("Действие отменено", reply_markup=kb)

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






@router.callback_query(F.data.startswith("callback_"))
async def handle_callback(callback: types.CallbackQuery):
    # Извлекаем динамическую часть (some_id)
    name_cat = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    
    async with async_session() as session:
        # 1. Находим запись
        result = await session.execute(
            select(Category).where(Category.name_categories == name_cat, Category.user_id == user_id)
        )
        item = result.scalar_one_or_none()

        # 2. Если запись не найдена или не принадлежит пользователю
    if not item:
        await callback.answer("❌ Запись не найдена!", show_alert=True)
        return

        # 3. Удаляем запись
    await session.delete(item)
    await session.commit()
    
    await callback.answer(f"Категория  \"{name_cat}\"  удалена", show_alert=True)







@router.callback_query(F.data == "new_category")
async def show_categories(callback, state: FSMContext):
    await callback.answer("")
    await state.set_state(Category_fsm.cats)
    await callback.message.answer("Введи новую категорию", reply_markup = kb_cancel_FSM)



@router.message(Category_fsm.cats)
async def add_category(message: types.Message, state: FSMContext):
    if message.text == "Отмена":
       await state.clear()
       await message.answer("Действие отменено", reply_markup=kb)
    else:
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
        
        await message.answer(f"Категория '{message.text}' добавлена!", reply_markup=kb)
        await state.clear()








import matplotlib.pyplot as plt 
from io import BytesIO
from aiogram.types import BufferedInputFile
from sqlalchemy import func


@router.callback_query(F.data == "show_diagram")
async def send_pie_chart(callback: types.CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(Expense.category, func.sum(Expense.amount))
            .where(Expense.user_id == callback.from_user.id)
            .group_by(Expense.category)
        )
        data = result.all()

        if not data:
            await callback.message.answer("Нет данных для построения диаграммы")
            return

        # 2. Подготавливаем данные
        labels = [item[0] for item in data]
        sizes = [float(item[1]) for item in data]
        
        # 3. Создаем диаграмму
        buf = BytesIO()
        plt.figure(figsize=(10, 8))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', shadow=True)
        plt.title('Ваши расходы по категориям')
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        plt.close()

        # 4. Отправляем изображение (ПРАВИЛЬНЫЙ способ для aiogram 3.x)
        await callback.message.answer_photo(
            types.BufferedInputFile(buf.read(), filename='expenses.png')
        )
        buf.close()







# 🗑️ Удалить расход
@router.message(F.text == '🗑️ Удалить расход')
async def send_users_table(message: types.Message):
    async with async_session() as session:
        result = await session.execute(select(Expense).where(Expense.user_id == message.from_user.id))
        db_object = result.scalars().all()
        for expense in db_object:
                print(f"✅ ✅ ✅ ✅  {expense.__dict__}✅ ✅ ✅ ✅ ")