from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


# ── Auth ─────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def username_check(cls, v):
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_check(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Genres ────────────────────────────────────────────────────────────────────

class GenreIn(BaseModel):
    genre_id: int
    genre_name: str


# ── Liked Movies ──────────────────────────────────────────────────────────────

class LikedMovieIn(BaseModel):
    tmdb_movie_id: int
    title: str
    poster_path: Optional[str] = None
    genre_ids: Optional[str] = None


class LikedMovieOut(LikedMovieIn):
    id: int
    liked_at: datetime
    model_config = {"from_attributes": True}


# ── Watchlist ─────────────────────────────────────────────────────────────────

class WatchlistIn(BaseModel):
    tmdb_movie_id: int
    title: str
    poster_path: Optional[str] = None


class WatchlistOut(WatchlistIn):
    id: int
    added_at: datetime
    model_config = {"from_attributes": True}


# ── Ratings ───────────────────────────────────────────────────────────────────

class RatingIn(BaseModel):
    tmdb_movie_id: int
    title: str
    rating: float

    @field_validator("rating")
    @classmethod
    def rating_range(cls, v):
        if not (1.0 <= v <= 5.0):
            raise ValueError("Rating must be between 1 and 5")
        return round(v, 1)


class RatingOut(RatingIn):
    id: int
    rated_at: datetime
    model_config = {"from_attributes": True}


# ── Recommendations ───────────────────────────────────────────────────────────

class RecommendedMovie(BaseModel):
    tmdb_id: int
    title: str
    poster_path: Optional[str] = None
    overview: Optional[str] = None
    vote_average: Optional[float] = None
    release_date: Optional[str] = None
    reason: str  # Claude's explanation


class RecommendationsOut(BaseModel):
    recommendations: list[RecommendedMovie]