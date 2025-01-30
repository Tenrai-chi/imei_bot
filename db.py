from sqlalchemy import Column, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker


Base = declarative_base()
engine = create_engine('sqlite:///whitelist.db')
Base.metadata.create_all(engine)


class User(Base):
    """ Модель базы данных user """

    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False)


def is_user_in_whitelist(telegram_id: int) -> bool:
    """ Проверка наличия пользователя в белом списке """

    with session_local() as db_sess:
        return db_sess.query(User).filter(User.telegram_id == telegram_id).first() is not None


def add_user(db: Session, telegram_id: int) -> User:
    """ Добавляет нового пользователя в базу данных """

    new_user = User(telegram_id=telegram_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def session_local() -> Session:
    """ Создание сессии в SQLAlchemy """

    session = sessionmaker(bind=engine)
    return session()
