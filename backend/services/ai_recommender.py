import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _build_movie_profile(movie: dict) -> str:
    """
    Combine a movie's genres, overview and title into a single
    text string so TF-IDF can vectorize it.
    """
    genre_ids = movie.get("genre_ids", [])
    genre_text = " ".join([f"genre{g}" for g in genre_ids])
    overview   = movie.get("overview", "")
    title      = movie.get("title", "")
    return f"{title} {genre_text} {overview}"


def get_recommendations(
    liked_movies: list[dict],
    candidate_movies: list[dict],
    top_n: int = 10,
) -> list[dict]:
    """
    Content-based filtering using TF-IDF + Cosine Similarity.

    1. Build a text profile for every candidate movie
    2. Build a user profile by averaging the TF-IDF vectors of liked movies
    3. Compute cosine similarity between user profile and every candidate
    4. Return the top N candidates ranked by similarity score
    """

    if not candidate_movies:
        return []

    # If the user has no liked movies yet, return candidates sorted by rating
    if not liked_movies:
        sorted_movies = sorted(
            candidate_movies,
            key=lambda m: m.get("vote_average", 0),
            reverse=True,
        )
        for movie in sorted_movies[:top_n]:
            movie["reason"] = "Highly rated in your preferred genres"
        return sorted_movies[:top_n]

    # Build text profiles for all movies (liked + candidates combined)
    all_movies   = liked_movies + candidate_movies
    all_profiles = [_build_movie_profile(m) for m in all_movies]

    # Vectorize using TF-IDF
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(all_profiles)

    # Split back into liked vectors and candidate vectors
    liked_vectors     = tfidf_matrix[: len(liked_movies)]
    candidate_vectors = tfidf_matrix[len(liked_movies) :]

    # Build user profile = average of all liked movie vectors
    user_profile = np.asarray(liked_vectors.mean(axis=0))

    # Compute cosine similarity between user profile and each candidate
    similarities = cosine_similarity(user_profile, candidate_vectors)[0]

    # Attach similarity scores to candidates
    scored = []
    for idx, movie in enumerate(candidate_movies):
        scored.append({**movie, "_score": float(similarities[idx])})

    # Sort by similarity score descending
    scored.sort(key=lambda m: m["_score"], reverse=True)

    # Build final result with a reason and remove internal score field
    results = []
    for movie in scored[:top_n]:
        movie["reason"] = f"Matches your taste with a similarity score of {movie['_score']:.2f}"
        movie.pop("_score")
        results.append(movie)

    return results
