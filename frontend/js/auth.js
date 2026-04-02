// Same origin when UI is served by FastAPI (`python run_server.py`). file:// falls back to local API.
const API_BASE_URL = "https://bingebuddy-5.onrender.com";
/**
 * Checks if the user is logged in.
 * If not, redirects them to the login page.
 */
function isTokenExpired() {
  const token = localStorage.getItem("access_token");
  if (!token) return true;

  const payload = JSON.parse(atob(token.split(".")[1]));
  return payload.exp * 1000 < Date.now();
}

function requireAuth() {
  const token = localStorage.getItem("access_token");
  if (!token || isTokenExpired()) {
    localStorage.removeItem("access_token");
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
  localStorage.removeItem("access_token");
  window.location.href = "login.html";
}
