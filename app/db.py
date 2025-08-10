from sqlmodel import SQLModel, create_engine, Session
import os

STORAGE_DIR = os.environ.get("STORAGE_DIR", "/workspace/app_storage")
DB_PATH = os.path.join(STORAGE_DIR, "app.db")
os.makedirs(STORAGE_DIR, exist_ok=True)

environment = os.environ.get("ENV", "dev")
connect_args = {"check_same_thread": False} if DB_PATH.endswith(".db") else {}
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, connect_args=connect_args)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)