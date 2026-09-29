/**
 * profile.js
 * Loads the logged-in student's profile from FastAPI.
 */

const PROFILE_API_BASE =
  window.location.port === "8000"
    ? ""
    : "http://localhost:8000";

function profileToken() {
  return localStorage.getItem(
    "access_token"
  );
}

function profileLogout() {
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

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString(
    "en-IN",
    {
      day: "2-digit",
      month: "long",
      year: "numeric",
    }
  );
}

async function loadProfile() {
  const token = profileToken();

  if (!token) {
    profileLogout();
    return;
  }

  try {
    const response =
      await fetch(
        `${PROFILE_API_BASE}/api/student/me`,
        {
          headers: {
            Authorization:
              `Bearer ${token}`,
          },
        }
      );

    if (response.status === 401) {
      profileLogout();
      return;
    }

    if (!response.ok) {
      throw new Error(
        "Could not load profile"
      );
    }

    const user =
      await response.json();

    document.getElementById(
      "avatar"
    ).textContent =
      (user.name || "S")
        .charAt(0)
        .toUpperCase();

    document.getElementById(
      "profileName"
    ).textContent =
      user.name;

    document.getElementById(
      "profileRole"
    ).textContent =
      user.role === "student"
        ? "Student Account"
        : user.role;

    document.getElementById(
      "name"
    ).textContent =
      user.name || "—";

    document.getElementById(
      "email"
    ).textContent =
      user.email || "—";

    document.getElementById(
      "phone"
    ).textContent =
      user.phone || "Not provided";

    document.getElementById(
      "role"
    ).textContent =
      user.role || "—";

    document.getElementById(
      "createdAt"
    ).textContent =
      formatDate(
        user.created_at
      );

    document.getElementById(
      "userId"
    ).textContent =
      `#${user.id}`;

  } catch (error) {
    console.error(
      "Profile error:",
      error
    );
  }
}

document
  .getElementById("logoutBtn")
  .addEventListener(
    "click",
    profileLogout
  );

document.addEventListener(
  "DOMContentLoaded",
  loadProfile
);
