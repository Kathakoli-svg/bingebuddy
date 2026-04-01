import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from auth import get_current_user
from services import tmdb
import models

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/trending")
async def trending(
    page: int = Query(default=1, ge=1),
    current_user: models.User = Depends(get_current_user),
):
    try:
        return await tmdb.get_trending(page=page)
    except Exception as e:
        logger.exception("trending failed")
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/search")
async def search(
    q: str = Query(..., min_length=1),
    page: int = Query(default=1, ge=1),
    current_user: models.User = Depends(get_current_user),
):
    try:
        return await tmdb.search_movies(query=q, page=page)
    except Exception as e:
        logger.exception("search failed")
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/by-genre")
async def by_genre(
    genre_ids: str = Query(..., description="Comma-separated TMDB genre IDs e.g. 28,12"),
    page: int = Query(default=1, ge=1),
    current_user: models.User = Depends(get_current_user),
):
    try:
        ids = [int(g) for g in genre_ids.split(",")]
        return await tmdb.get_movies_by_genres(genre_ids=ids, page=page)
    except ValueError:
        raise HTTPException(status_code=400, detail="genre_ids must be comma-separated numbers")
    except Exception as e:
        logger.exception("by-genre failed")
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/genres")
async def genres(current_user: models.User = Depends(get_current_user)):
    try:
        return await tmdb.get_all_genres()
    except Exception as e:
        logger.exception("genres failed")
        raise HTTPException(status_code=502, detail=str(e))


# ── These must come BEFORE /{tmdb_id} ─────────────────────────────────────────

@router.get("/{tmdb_id}/videos")
async def movie_videos(
    tmdb_id: int,
    current_user: models.User = Depends(get_current_user),
):
    """Get YouTube trailers/teasers for a movie."""
    try:
        return await tmdb.get_movie_videos(tmdb_id=tmdb_id)
    except Exception as e:
        logger.exception("videos failed")
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{tmdb_id}/reviews")
async def movie_reviews(
    tmdb_id: int,
    current_user: models.User = Depends(get_current_user),
):
    """Get user reviews for a movie."""
    try:
        return await tmdb.get_movie_reviews(tmdb_id=tmdb_id)
    except Exception as e:
        logger.exception("reviews failed")
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{tmdb_id}")
async def movie_detail(
    tmdb_id: int,
    current_user: models.User = Depends(get_current_user),
):
    try:
        return await tmdb.get_movie_details(tmdb_id=tmdb_id)
    except Exception as e:
        logger.exception("movie detail failed")
        raise HTTPException(status_code=404, detail=str(e))


