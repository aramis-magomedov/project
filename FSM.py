from aiogram.fsm.state import StatesGroup, State


# Состояния для FSM
class Reg(StatesGroup):
    name = State()
    surname = State()
    password = State()
    registry_or_auth = State()
    cheked = State()

class Waste(StatesGroup):
    category = State()
    sum_waste = State()

class Category_fsm(StatesGroup):
    cats = State()