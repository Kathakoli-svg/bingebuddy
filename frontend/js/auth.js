// Same origin when UI is served by FastAPI (`python run_server.py`). file:// falls back to local API.
const API_BASE_URL = "https://bingebuddy-5.onrender.com";
const SESSION_TTL_MS = 7 * 24 * 60 * 60 * 1000; // 7 days

function getSessionExpiry() {
  const expiry = localStorage.getItem("access_token_expires_at");
  return expiry ? Number(expiry) : null;
}

function isSessionExpired() {
  const expiresAt = getSessionExpiry();
  return expiresAt !== null && Date.now() > expiresAt;
}

function clearSession() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("access_token_expires_at");
}

/**
 * Checks if the user is logged in.
 * If not, redirects them to the login page.
 */
function requireAuth() {
  const token = localStorage.getItem("access_token");
  if (!token || isSessionExpired()) {
    clearSession();
    window.location.href = "login.html";
  }
}

function parseErrorDetail(data) {
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map((d) => d.msg || JSON.stringify(d)).join(", ");
  }
  if (data.detail && typeof data.detail === "object") {
    return data.detail.msg || "Request failed";
  }
  return "Request failed";
}

/**
 * Login — returns { success, error? } for forms that handle UI.
 */
async function loginUser(email, password) {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await response.json();
    if (response.ok) {
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem(
        "access_token_expires_at",
        String(Date.now() + SESSION_TTL_MS),
      );
      return { success: true };
    }
    return { success: false, error: parseErrorDetail(data) };
  } catch (error) {
    console.error("Login error:", error);
    return {
      success: false,
      error:
        "Could not connect to the server. Is your FastAPI backend running?",
    };
  }
}

/**
 * Register — returns { success, error? }.
 */
async function registerUser(username, email, password) {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password }),
    });
    const data = await response.json();
    if (response.ok) {
      return { success: true };
    }
    return { success: false, error: parseErrorDetail(data) };
  } catch (error) {
    console.error("Register error:", error);
    return {
      success: false,
      error:
        "Could not connect to the server. Is your FastAPI backend running?",
    };
  }
}

/**
 * Helper to generate headers for authorized requests.
 */
function authHeaders() {
  const token = localStorage.getItem("access_token");
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

/**
 * Clears the session and redirects to login.
 */
function logout() {
  clearSession();
  window.location.href = "login.html";
}
