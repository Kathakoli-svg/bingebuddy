// API_BASE_URL and authHeaders() are defined in auth.js (loaded before this file)

/** Poster: backend may return a full proxy URL or a TMDB path. */
function posterUrl(movie) {
  const p = movie.poster_path;
  if (!p) return "https://via.placeholder.com/500x750?text=No+Poster";
  if (p.startsWith("http://") || p.startsWith("https://")) return p;
  return `https://image.tmdb.org/t/p/w500${p}`;
}

function genreIdsString(movie) {
  const g = movie.genre_ids;
  if (!g) return "";
  if (Array.isArray(g)) return g.join(",");
  return String(g);
}

async function fetchTrending() {
  const res = await fetch(`${API_BASE_URL}/movies/trending`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch trending");
  return res.json();
}

async function fetchLiked() {
  const res = await fetch(`${API_BASE_URL}/user/liked`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch liked movies");
  return res.json();
}

async function fetchWatchlist() {
  const res = await fetch(`${API_BASE_URL}/user/watchlist`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch watchlist");
  return res.json();
}

async function fetchRecommendations() {
  const res = await fetch(`${API_BASE_URL}/recommend`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch recommendations");
  return res.json();
}

async function fetchGenres() {
  const res = await fetch(`${API_BASE_URL}/movies/genres`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch genres");
  return res.json();
}

async function searchMovies(query) {
  const res = await fetch(
    `${API_BASE_URL}/movies/search?q=${encodeURIComponent(query)}`,
    { headers: authHeaders() },
  );
  if (!res.ok) throw new Error("Search failed");
  return res.json();
}

function createMovieCard(movie, isLiked) {
  const div = document.createElement("div");
  div.className = "movie-card";

  const movieId = movie.tmdb_id || movie.tmdb_movie_id || movie.id;
  const poster = posterUrl(movie);
  const genreStr = genreIdsString(movie);

  div.innerHTML = `
    <div class="movie-poster-container" style="cursor:pointer;">
      <img src="${poster}" class="movie-poster" alt="">
      <div class="movie-overlay">
        <button type="button" class="btn-like ${isLiked ? "active" : ""}" data-movie-id="${movieId}">
          <i class="fa${isLiked ? "s" : "r"} fa-heart"></i>
        </button>
      </div>
    </div>
    <div class="movie-info">
      <h3 class="movie-title"></h3>
    </div>
  `;

  div.querySelector(".movie-title").textContent = movie.title || "";

  const reasonEl = movie.reason
    ? `<p class="movie-reason">🤖 ${movie.reason}</p>`
    : "";
  if (reasonEl) {
    div.querySelector(".movie-info").insertAdjacentHTML("beforeend", reasonEl);
  }

  // Click poster → go to detail page
  div.querySelector(".movie-poster-container").addEventListener("click", (e) => {
    if (e.target.closest(".btn-like")) return;
    window.location.href = `movie.html?id=${movieId}`;
  });

  const btn = div.querySelector(".btn-like");
  btn.addEventListener("click", (e) => {
    e.stopPropagation();
    handleLikeToggle(btn, movieId, movie.title, poster, genreStr);
  });

  return div;
}

async function handleLikeToggle(button, id, title, poster, genreStr) {
  const isActive = button.classList.contains("active");
  const method = isActive ? "DELETE" : "POST";
  const url = `${API_BASE_URL}/user/liked${isActive ? `/${id}` : ""}`;

  const body = isActive
    ? null
    : JSON.stringify({
        tmdb_movie_id: id,
        title: title,
        poster_path: poster,
        genre_ids: genreStr || null,
      });

  try {
    const res = await fetch(url, {
      method: method,
      headers: authHeaders(),
      body: body,
    });

    if (res.ok) {
      button.classList.toggle("active");
      const icon = button.querySelector("i");
      icon.classList.toggle("fas");
      icon.classList.toggle("far");

      if (typeof likedIds !== "undefined") {
        if (isActive) likedIds.delete(id);
        else likedIds.add(id);
      }
    }
  } catch (err) {
    console.error("Like toggle failed:", err);
  }
}
