from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import String, create_engine

from sqlalchemy.ext.asyncio import AsyncSession


class Base(DeclarativeBase):
    pass
@property

class User(Base):
    __tablename__ = "tg_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(20))
    email: Mapped[str] = mapped_column(String(50))

engine = create_engine("sqlite:///db.db", echo=True)


def create_db_and_tables() -> None:
	Base.metadata.create_all(engine)
     
Session = AsyncSession(engine)


