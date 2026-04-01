from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from schemas import (
    GenreIn,
    LikedMovieIn, LikedMovieOut,
    WatchlistIn, WatchlistOut,
    RatingIn, RatingOut,
)
import models

router = APIRouter()


# ── Genres ────────────────────────────────────────────────────────────────────

@router.post("/genres", status_code=status.HTTP_201_CREATED)
def save_genres(
    genres: list[GenreIn],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Save the user's preferred genres. Clears old ones first."""
    db.query(models.UserGenre).filter(models.UserGenre.user_id == current_user.id).delete()

    for genre in genres:
        db.add(models.UserGenre(
            user_id=current_user.id,
            genre_id=genre.genre_id,
            genre_name=genre.genre_name,
        ))
    db.commit()
    return {"message": "Genres saved successfully"}


@router.get("/genres")
def get_genres(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get the user's saved genre preferences."""
    return db.query(models.UserGenre).filter(models.UserGenre.user_id == current_user.id).all()


# ── Liked Movies ──────────────────────────────────────────────────────────────

@router.post("/liked", response_model=LikedMovieOut, status_code=status.HTTP_201_CREATED)
def like_movie(
    payload: LikedMovieIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Like a movie."""
    already_liked = db.query(models.LikedMovie).filter(
        models.LikedMovie.user_id == current_user.id,
        models.LikedMovie.tmdb_movie_id == payload.tmdb_movie_id,
    ).first()

    if already_liked:
        raise HTTPException(status_code=400, detail="Movie already liked")

    liked = models.LikedMovie(
        user_id=current_user.id,
        tmdb_movie_id=payload.tmdb_movie_id,
        title=payload.title,
        poster_path=payload.poster_path,
        genre_ids=payload.genre_ids,
    )
    db.add(liked)
    db.commit()
    db.refresh(liked)
    return liked


@router.delete("/liked/{tmdb_movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlike_movie(
    tmdb_movie_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Unlike a movie."""
    liked = db.query(models.LikedMovie).filter(
        models.LikedMovie.user_id == current_user.id,
        models.LikedMovie.tmdb_movie_id == tmdb_movie_id,
    ).first()

    if not liked:
        raise HTTPException(status_code=404, detail="Movie not in liked list")

    db.delete(liked)
    db.commit()


@router.get("/liked", response_model=list[LikedMovieOut])
def get_liked(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get all movies the user has liked."""
    return db.query(models.LikedMovie).filter(
        models.LikedMovie.user_id == current_user.id
    ).order_by(models.LikedMovie.liked_at.desc()).all()


# ── Watchlist ─────────────────────────────────────────────────────────────────

@router.post("/watchlist", response_model=WatchlistOut, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    payload: WatchlistIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Add a movie to the watchlist."""
    already_saved = db.query(models.Watchlist).filter(
        models.Watchlist.user_id == current_user.id,
        models.Watchlist.tmdb_movie_id == payload.tmdb_movie_id,
    ).first()

    if already_saved:
        raise HTTPException(status_code=400, detail="Movie already in watchlist")

    item = models.Watchlist(
        user_id=current_user.id,
        tmdb_movie_id=payload.tmdb_movie_id,
        title=payload.title,
        poster_path=payload.poster_path,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/watchlist/{tmdb_movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_watchlist(
    tmdb_movie_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Remove a movie from the watchlist."""
    item = db.query(models.Watchlist).filter(
        models.Watchlist.user_id == current_user.id,
        models.Watchlist.tmdb_movie_id == tmdb_movie_id,
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Movie not in watchlist")

    db.delete(item)
    db.commit()


@router.get("/watchlist", response_model=list[WatchlistOut])
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get all movies in the user's watchlist."""
    return db.query(models.Watchlist).filter(
        models.Watchlist.user_id == current_user.id
    ).order_by(models.Watchlist.added_at.desc()).all()


# ── Ratings ───────────────────────────────────────────────────────────────────

@router.post("/ratings", response_model=RatingOut, status_code=status.HTTP_201_CREATED)
def rate_movie(
    payload: RatingIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Rate a movie. If already rated, updates the existing rating."""
    existing = db.query(models.Rating).filter(
        models.Rating.user_id == current_user.id,
        models.Rating.tmdb_movie_id == payload.tmdb_movie_id,
    ).first()

    if existing:
        existing.rating = payload.rating
        db.commit()
        db.refresh(existing)
        return existing

    rating = models.Rating(
        user_id=current_user.id,
        tmdb_movie_id=payload.tmdb_movie_id,
        title=payload.title,
        rating=payload.rating,
    )
    db.add(rating)
    db.commit()
    db.refresh(rating)
    return rating


@router.get("/ratings", response_model=list[RatingOut])
def get_ratings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get all movies the user has rated."""
    return db.query(models.Rating).filter(
        models.Rating.user_id == current_user.id
    ).order_by(models.Rating.rated_at.desc()).all()