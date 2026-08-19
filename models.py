import enum
from sqlalchemy import Integer, Float, String, Date, Enum, Table, Column, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import date

class Base(DeclarativeBase):
    pass

movie_genres = Table(
    "movie_genres",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id"), primary_key=True),
)

class MovieStatus(str, enum.Enum):
    WANT_TO_WATCH = "want to watch"
    WATCHING = "watching"
    WATCHED = "watched"

class Genre(Base):
    __tablename__="genres"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    
    movies: Mapped[list["Movie"]] = relationship(secondary=movie_genres, back_populates="genres")

class Movie(Base):
    __tablename__="movies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), unique=True)
    year: Mapped[int] = mapped_column(Integer)
    genres: Mapped[list["Genre"]] = relationship(secondary=movie_genres, back_populates="movies")
    rating: Mapped[float | None] = mapped_column(Float)
    status: Mapped[MovieStatus] = mapped_column(Enum(MovieStatus), default=MovieStatus.WANT_TO_WATCH)
    watched_at: Mapped[date | None] = mapped_column(Date)

