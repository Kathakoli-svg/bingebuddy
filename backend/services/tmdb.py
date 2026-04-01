import time
import asyncio
import threading
import httpx
from config import settings

# verify=False fixes intermittent SSL failures on Windows
CLIENT_KWARGS = {
    "timeout": 20.0,
    "verify": False,
    "http2": False,
}

PARAMS_BASE = {
    "api_key": settings.TMDB_API_KEY,
    "language": "en-US",
}

_cache: dict = {}
_cache_lock = threading.Lock()  # guards all _cache reads/writes
CACHE_TTL = 1800   # 30 min fresh
STALE_TTL = 86400  # 24 hr stale fallback


def _cache_get(key):
    with _cache_lock:
        e = _cache.get(key)
    if e and (time.time() - e["ts"]) < CACHE_TTL:
        return e["data"]
    return None


def _cache_get_stale(key):
    with _cache_lock:
        e = _cache.get(f"stale:{key}")
    if e and (time.time() - e["ts"]) < STALE_TTL:
        return e["data"]
    return None


def _cache_set(key, data):
    now = time.time()
    with _cache_lock:
        _cache[key] = {"data": data, "ts": now}
        _cache[f"stale:{key}"] = {"data": data, "ts": now}


def _cache_evict_expired():
    """Remove entries older than STALE_TTL to prevent unbounded memory growth."""
    now = time.time()
    with _cache_lock:
        expired = [k for k, v in _cache.items() if (now - v["ts"]) > STALE_TTL]
        for k in expired:
            del _cache[k]


def _build_movie(m):
    return {
        "tmdb_id":       m.get("id"),
        "title":         m.get("title", ""),
        "overview":      m.get("overview", ""),
        "poster_path":   m.get("poster_path"),
        "backdrop_path": m.get("backdrop_path"),
        "release_date":  m.get("release_date", ""),
        "vote_average":  round(m.get("vote_average", 0), 1),
        "genre_ids":     m.get("genre_ids", []),
    }


async def _fetch(endpoint, extra_params=None):
    params = {**PARAMS_BASE, **(extra_params or {})}
    last_err = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(**CLIENT_KWARGS) as client:
                r = await client.get(f"{settings.TMDB_BASE_URL}{endpoint}", params=params)
                r.raise_for_status()
                return r.json()
        except Exception as e:
            last_err = e
            await asyncio.sleep(2 ** attempt)
    raise last_err


async def _get(endpoint, extra_params=None, key=None):
    cache_key = key or endpoint
    hit = _cache_get(cache_key)
    if hit is not None:
        return hit
    try:
        data = await _fetch(endpoint, extra_params)
        _cache_set(cache_key, data)
        return data
    except Exception as e:
        stale = _cache_get_stale(cache_key)
        if stale is not None:
            return stale
        raise e


async def get_trending(page=1):
    data = await _get("/trending/movie/week", {"page": page}, f"trending:{page}")
    return [_build_movie(m) for m in data.get("results", [])]


async def search_movies(query, page=1):
    data = await _get("/search/movie", {"query": query, "page": page}, f"search:{query.lower().strip()}:{page}")
    return [_build_movie(m) for m in data.get("results", [])]


async def get_movies_by_genres(genre_ids, page=1):
    key = f"genres:{','.join(str(g) for g in sorted(genre_ids))}:{page}"
    data = await _get("/discover/movie", {"with_genres": ",".join(str(g) for g in genre_ids), "sort_by": "popularity.desc", "page": page}, key)
    return [_build_movie(m) for m in data.get("results", [])]


async def get_movie_details(tmdb_id):
    movie = await _get(f"/movie/{tmdb_id}", None, f"detail:{tmdb_id}")
    return {**_build_movie(movie), "genres": movie.get("genres", []), "runtime": movie.get("runtime"), "tagline": movie.get("tagline", ""), "vote_count": movie.get("vote_count", 0), "status": movie.get("status", "")}


async def get_movie_videos(tmdb_id):
    data = await _get(f"/movie/{tmdb_id}/videos", None, f"videos:{tmdb_id}")
    videos = [{"key": v["key"], "name": v["name"], "type": v["type"], "official": v.get("official", False)} for v in data.get("results", []) if v.get("site") == "YouTube" and v.get("type") in ("Trailer", "Teaser")]
    videos.sort(key=lambda v: (not v["official"], v["type"] != "Trailer"))
    return videos


async def get_movie_reviews(tmdb_id):
    data = await _get(f"/movie/{tmdb_id}/reviews", None, f"reviews:{tmdb_id}")
    return [{"author": r.get("author", "Anonymous"), "rating": r.get("author_details", {}).get("rating"), "content": r.get("content", ""), "created_at": r.get("created_at", "")[:10]} for r in data.get("results", [])]


async def get_all_genres():
    data = await _get("/genre/movie/list", None, "all_genres")
    return data.get("genres", [])


def _sync_fetch(endpoint, extra_params=None):
    """Sync fetch for background thread warm-up."""
    params = {**PARAMS_BASE, **(extra_params or {})}
    with httpx.Client(**CLIENT_KWARGS) as client:
        r = client.get(f"{settings.TMDB_BASE_URL}{endpoint}", params=params)
        r.raise_for_status()
        return r.json()


def warm_cache():
    def _warm():
        time.sleep(2)
        try:
            for page in range(1, 3):
                data = _sync_fetch("/trending/movie/week", {"page": page})
                _cache_set(f"trending:{page}", data)
            _cache_set("all_genres", _sync_fetch("/genre/movie/list"))
        except Exception:
            pass
    threading.Thread(target=_warm, daemon=True).start()


def _bg_refresh():
    while True:
        time.sleep(CACHE_TTL)
        try:
            for page in range(1, 3):
                _cache_set(f"trending:{page}", _sync_fetch("/trending/movie/week", {"page": page}))
            _cache_set("all_genres", _sync_fetch("/genre/movie/list"))
        except Exception:
            pass
        _cache_evict_expired()  # prune stale entries every refresh cycle

threading.Thread(target=_bg_refresh, daemon=True).start()