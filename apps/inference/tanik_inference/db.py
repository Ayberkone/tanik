from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Iterator, Optional

from sqlalchemy import String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool

from .config import settings


def _engine_kwargs(url: str) -> Dict[str, Any]:
    # In-memory SQLite needs a single shared connection or each session sees an
    # empty database. StaticPool gives that without affecting file-backed URLs.
    if url.endswith(":memory:"):
        return {
            "poolclass": StaticPool,
            "connect_args": {"check_same_thread": False},
        }
    return {}


engine = create_engine(settings.db_url, echo=False, future=True, **_engine_kwargs(settings.db_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


class Subject(Base):
    __tablename__ = "subjects"
    subject_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    eye_side: Mapped[str] = mapped_column(String(8))
    enrolled_at: Mapped[datetime]
    template_version: Mapped[str] = mapped_column(String(64))
    template_json: Mapped[str] = mapped_column()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
