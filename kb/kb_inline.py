from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

kb_options = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📊 Показать диаграмму расходов", callback_data="show_diagram")],
    [InlineKeyboardButton(text="📂 Добавить категорию расхода", callback_data="new_category")],
    [InlineKeyboardButton(text="📑 Текущие категории расходов", url="https://example.com")],
    [InlineKeyboardButton(text="❌ Удалить категорию", callback_data='asv')]
])

list_categories_inline = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Eда", callback_data="fqwefwe")],
    [InlineKeyboardButton(text="Транспорт", url="https://example.com")],
    [InlineKeyboardButton(text="Развлечения", callback_data='asv')]
])

kb_register_user = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🚪 Войти в аккаунт", callback_data="auth_callback")],
    [InlineKeyboardButton(text="🌱 Регистрация", callback_data="register_callback")]
])

