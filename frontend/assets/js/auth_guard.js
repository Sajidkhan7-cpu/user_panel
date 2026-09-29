/**
 * auth_guard.js
 * Protects student portal pages.
 *
 * A missing token is redirected immediately.
 * A token is then verified against FastAPI.
 */

const AUTH_API_BASE =
  window.location.port === "8000"
    ? ""
    : "http://localhost:8000";

const storedToken =
  localStorage.getItem("access_token");

if (!storedToken) {
  window.location.replace("login.html");
}

async function requireLogin() {
  const token =
    localStorage.getItem("access_token");

  if (!token) return false;

  try {
    const response =
      await fetch(
        `${AUTH_API_BASE}/api/student/me`,
        {
          method: "GET",
          headers: {
            Authorization:
              `Bearer ${token}`,
          },
        }
      );

    if (!response.ok) {
      localStorage.removeItem(
        "access_token"
      );
      localStorage.removeItem(
        "user"
      );
      localStorage.removeItem(
        "chatbot_session_id"
      );

      window.location.replace(
        "login.html"
      );

      return false;
    }

    const user =
      await response.json();

    localStorage.setItem(
      "user",
      JSON.stringify(user)
    );

    document.dispatchEvent(
      new CustomEvent(
        "authenticatedUser",
        {
          detail: user,
        }
      )
    );

    return true;

  } catch (error) {
    console.error(
      "Authentication check failed:",
      error
    );

    window.location.replace(
      "login.html"
    );

    return false;
  }
}

function logoutUser() {
  localStorage.removeItem(
    "access_token"
  );
  localStorage.removeItem(
    "user"
  );
  localStorage.removeItem(
    "chatbot_session_id"
  );

  window.location.replace(
    "login.html"
  );
}

document.addEventListener(
  "DOMContentLoaded",
  requireLogin
);
