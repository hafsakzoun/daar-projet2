
from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
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

class Favorite(Base):
    """Livre mis en favori par un utilisateur (stocke en base,
    donc retrouve sur n'importe quelle machine)."""

    __tablename__ = "user_favorites"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SearchHistory(Base):
    """Recherche lancee par un utilisateur connecte."""

    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    query: Mapped[str] = mapped_column(String(200))
    mode: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("mode IN ('keyword', 'regex')"),
    )


class BookSimilarity(Base):
    """Arete du graphe de Jaccard (stockee dans les deux sens)."""

    __tablename__ = "book_similarities"

    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        primary_key=True,
    )
    neighbor_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        primary_key=True,
    )
    similarity: Mapped[float]


class BookScore(Base):
    """Centralite PageRank d'un livre dans le graphe de Jaccard."""

    __tablename__ = "book_scores"

    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        primary_key=True,
    )
    pagerank: Mapped[float]
