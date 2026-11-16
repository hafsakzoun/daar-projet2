"""Tables independantes pour experimenter l'index V2."""

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class V2Base(DeclarativeBase):
    pass


class BookV2(V2Base):
    __tablename__ = "books_v2"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    author: Mapped[str] = mapped_column(String(500))
    language: Mapped[str] = mapped_column(String(20))


class TermV2(V2Base):
    __tablename__ = "terms_v2"

    id: Mapped[int] = mapped_column(primary_key=True)
    language: Mapped[str] = mapped_column(String(20))
    value: Mapped[str] = mapped_column(String(255))

    __table_args__ = (
        UniqueConstraint(
            "language", "value",
            name="uq_terms_v2_language_value",
        ),
    )


class PostingV2(V2Base):
    __tablename__ = "postings_v2"

    book_id: Mapped[int] = mapped_column(
        ForeignKey("books_v2.id", ondelete="CASCADE"),
        primary_key=True,
    )
    term_id: Mapped[int] = mapped_column(
        ForeignKey("terms_v2.id", ondelete="CASCADE"),
        primary_key=True,
    )
    frequency: Mapped[int]

    __table_args__ = (
        CheckConstraint("frequency > 0"),
    )


Index("ix_postings_v2_term_id", PostingV2.term_id)
