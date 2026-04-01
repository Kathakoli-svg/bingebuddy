from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float,
    Boolean, DateTime, ForeignKey, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String(50), unique=True, index=True, nullable=False)
    email           = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)

    genres    = relationship("UserGenre",  back_populates="user", cascade="all, delete")
    liked     = relationship("LikedMovie", back_populates="user", cascade="all, delete")
    watchlist = relationship("Watchlist",  back_populates="user", cascade="all, delete")
    ratings   = relationship("Rating",     back_populates="user", cascade="all, delete")


class UserGenre(Base):
    """Genre preferences the user picks at signup."""
    __tablename__ = "user_genres"
    __table_args__ = (UniqueConstraint("user_id", "genre_id"),)

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    genre_id   = Column(Integer, nullable=False)
    genre_name = Column(String(50), nullable=False)

    user = relationship("User", back_populates="genres")


class LikedMovie(Base):
    """Movies the user has liked."""
    __tablename__ = "liked_movies"
    __table_args__ = (UniqueConstraint("user_id", "tmdb_movie_id"),)

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    tmdb_movie_id = Column(Integer, nullable=False, index=True)
    title         = Column(String(255), nullable=False)
    poster_path   = Column(String(255), nullable=True)
    genre_ids     = Column(String(255), nullable=True)  # comma-separated
    liked_at      = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="liked")


class Watchlist(Base):
    """Movies the user saved to watch later."""
    __tablename__ = "watchlist"
    __table_args__ = (UniqueConstraint("user_id", "tmdb_movie_id"),)

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    tmdb_movie_id = Column(Integer, nullable=False, index=True)
    title         = Column(String(255), nullable=False)
    poster_path   = Column(String(255), nullable=True)
    added_at      = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="watchlist")


class Rating(Base):
    """1–5 star rating given by the user to a movie."""
    __tablename__ = "ratings"
    __table_args__ = (UniqueConstraint("user_id", "tmdb_movie_id"),)

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    tmdb_movie_id = Column(Integer, nullable=False, index=True)
    title         = Column(String(255), nullable=False)
    rating        = Column(Float, nullable=False)
    rated_at      = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="ratings")