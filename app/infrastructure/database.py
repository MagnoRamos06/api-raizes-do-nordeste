from pathlib import Path
from typing import Generator

from sqlalchemy import event
from sqlmodel import Session, create_engine

from app.config import settings


DATABASE_URL = settings.database_url

if DATABASE_URL.startswith("sqlite:///"):
    database_file = DATABASE_URL.removeprefix("sqlite:///")
    Path(database_file).parent.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)

if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(connection, _record) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
