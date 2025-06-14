from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime,select, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime




# Настройка базы данных
DATABASE_URL = "sqlite+aiosqlite:///db.db"
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    # не забыть убрать флажок
    telegram_id = Column(Integer, unique=False) 
    name = Column(String)
    surname = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    password = Column(String)
    IQ_user = Column(Integer, default=50)


# Модель расхода
class Expense(Base):
    __tablename__ = 'expenses'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    category = Column(String)
    amount = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    user_id = Column(Integer, ForeignKey('users.id'))


# Модель категорий расхода
class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name_categories = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))

# Создаем асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Создаем таблицы при старте 
async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
