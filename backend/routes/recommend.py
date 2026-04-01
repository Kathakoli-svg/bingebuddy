from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from services.tmdb import get_movies_by_genres, get_trending
from services.ai_recommender import get_recommendations
from schemas import RecommendationsOut
import models

router = APIRouter()


@router.get("", response_model=RecommendationsOut)
async def recommend(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Generate personalized movie recommendations using
    content-based filtering with TF-IDF and Cosine Similarity.
    """

    # Step 1 — Get user's genre preferences from DB
    user_genres = db.query(models.UserGenre).filter(
        models.UserGenre.user_id == current_user.id
    ).all()

    genre_ids = [g.genre_id for g in user_genres]

    # Step 2 — Get user's liked movies from DB
    liked = db.query(models.LikedMovie).filter(
        models.LikedMovie.user_id == current_user.id
    ).all()

    # Build liked movies as dicts for the recommender
    liked_movies = [
        {
            "tmdb_id": m.tmdb_movie_id,
            "title": m.title,
            "overview": "",
            "genre_ids": [int(g) for g in m.genre_ids.split(",") if g.strip()]
            if m.genre_ids
            else [],
            "vote_average": 0,
            "poster_path": m.poster_path,
            "release_date": "",
        }
        for m in liked
    ]

    # Step 3 — Fetch candidate movies from TMDB
    try:
        if genre_ids:
            candidates = await get_movies_by_genres(genre_ids=genre_ids, page=1)
        else:
            candidates = await get_trending(page=1)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to fetch movies from TMDB")

    if not candidates:
        raise HTTPException(status_code=404, detail="No candidate movies found")

    # Step 4 — Run cosine similarity to rank candidates
    recommendations = get_recommendations(
        liked_movies=liked_movies,
        candidate_movies=candidates,
        top_n=10,
    )

    return {"recommendations": recommendations}