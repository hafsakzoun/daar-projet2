
from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Index
from datetime import datetime
from sqlalchemy import DateTime

class Base(DeclarativeBase):
    pass


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    author: Mapped[str] = mapped_column(String(500))
    language: Mapped[str] = mapped_column(String(20))
    word_count: Mapped[int]
    source_url: Mapped[str] = mapped_column(Text)
    text_path: Mapped[str] = mapped_column(Text)

    __table_args__ = (
        CheckConstraint("word_count >= 10000"),
    )


class Term(Base):
    __tablename__ = "terms"

    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )


class Posting(Base):
    __tablename__ = "postings"

    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        primary_key=True,
    )
    term_id: Mapped[int] = mapped_column(
        ForeignKey("terms.id", ondelete="CASCADE"),
        primary_key=True,
    )
    frequency: Mapped[int]

    __table_args__ = (
        CheckConstraint("frequency > 0"),
    )
Index("ix_postings_term_id", Posting.term_id)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))