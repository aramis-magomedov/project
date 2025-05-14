from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💸 Добавить расход"), KeyboardButton(text="🗑️ Удалить расход")],
        [KeyboardButton(text="🗓 Запланировать расход"),KeyboardButton(text='📋 Список расходов')],
        [KeyboardButton(text="⚙️ Параметры")]
    ],
    resize_keyboard=True,
)


kb_right = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🟢 Да,всё верно"), KeyboardButton(text="🔴 Нет,ввести данные заново")]
    ],
    resize_keyboard=True,
    )