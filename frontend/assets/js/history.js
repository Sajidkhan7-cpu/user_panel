/**
 * history.js
 * Shows only the currently logged-in student's chat history.
 */

const API_BASE =
  window.location.port === "8000"
    ? ""
    : "http://localhost:8000";

const historyList =
  document.getElementById("historyList");

const loading =
  document.getElementById("loading");

const empty =
  document.getElementById("empty");

const refreshBtn =
  document.getElementById("refreshBtn");

const clearBtn =
  document.getElementById("clearBtn");

const sessionLabel =
  document.getElementById("sessionLabel");

function getToken() {
  return localStorage.getItem("access_token");
}

function escapeHtml(value) {
  return String(value ?? "").replace(
    /[&<>"']/g,
    (char) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      })[char]
  );
}

function formatDate(value) {
  if (!value) return "Date unavailable";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString(
    "en-IN",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }
  );
}

function getCurrentUser() {
  try {
    return JSON.parse(
      localStorage.getItem("user") || "{}"
    );
  } catch {
    return {};
  }
}

function showLoading() {
  loading.classList.remove("hidden");
  empty.classList.add("hidden");
  historyList.innerHTML = "";
}

function showEmpty() {
  loading.classList.add("hidden");
  empty.classList.remove("hidden");
  historyList.innerHTML = "";
}

function showError(message) {
  loading.classList.add("hidden");
  empty.classList.add("hidden");

  historyList.innerHTML = `
    <div class="state">
      <h3>Unable to load history</h3>
      <p>${escapeHtml(message)}</p>
      <button class="btn secondary" onclick="loadHistory()">
        Try Again
      </button>
    </div>
  `;
}

function renderHistory(history) {
  if (
    !Array.isArray(history) ||
    history.length === 0
  ) {
    showEmpty();
    return;
  }

  loading.classList.add("hidden");
  empty.classList.add("hidden");

  historyList.innerHTML =
    history
      .map(
        (item, index) => `
          <article class="history-item">

            <div class="history-meta">
              <span>
                Conversation #${index + 1}
              </span>

              <span>
                ${escapeHtml(
                  formatDate(
                    item.created_at
                  )
                )}
              </span>
            </div>

            <div class="message-row question">
              <span class="message-label">
                You asked
              </span>

              <div class="message-text">
                ${escapeHtml(
                  item.question
                )}
              </div>
            </div>

            <div class="message-row answer">
              <span class="message-label">
                AI Assistant
              </span>

              <div class="message-text">
                ${escapeHtml(
                  item.answer
                )}
              </div>

              ${
                item.intent
                  ? `
                    <span class="intent">
                      ${escapeHtml(
                        item.intent
                      )}
                    </span>
                  `
                  : ""
              }
            </div>

          </article>
        `
      )
      .join("");
}

async function loadHistory() {
  const token = getToken();

  if (!token) {
    window.location.replace(
      "login.html"
    );
    return;
  }

  const user = getCurrentUser();

  sessionLabel.textContent =
    `Logged in as ${user.name || "Student"}`;

  showLoading();

  try {
    const response =
      await fetch(
        `${API_BASE}/api/student/me/chat-history`,
        {
          method: "GET",
          headers: {
            Authorization:
              `Bearer ${token}`,
            Accept:
              "application/json",
          },
        }
      );

    if (response.status === 401) {
      logoutUser();
      return;
    }

    if (!response.ok) {
      throw new Error(
        `Server responded with ${response.status}`
      );
    }

    const history =
      await response.json();

    renderHistory(history);

  } catch (error) {
    console.error(
      "History error:",
      error
    );

    showError(
      "Please make sure the FastAPI backend is running."
    );
  }
}

async function clearHistory() {
  const token = getToken();

  if (!token) {
    logoutUser();
    return;
  }

  const confirmed =
    confirm(
      "Delete all of your chatbot history?"
    );

  if (!confirmed) return;

  clearBtn.disabled = true;
  clearBtn.textContent =
    "Deleting...";

  try {
    const response =
      await fetch(
        `${API_BASE}/api/student/me/chat-history`,
        {
          method: "DELETE",
          headers: {
            Authorization:
              `Bearer ${token}`,
          },
        }
      );

    if (response.status === 401) {
      logoutUser();
      return;
    }

    if (!response.ok) {
      throw new Error(
        "Could not delete history"
      );
    }

    await loadHistory();

  } catch (error) {
    console.error(
      "Delete history error:",
      error
    );

    alert(
      "Could not delete your history."
    );

  } finally {
    clearBtn.disabled = false;
    clearBtn.textContent =
      "Clear History";
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

if (refreshBtn) {
  refreshBtn.addEventListener(
    "click",
    loadHistory
  );
}

if (clearBtn) {
  clearBtn.addEventListener(
    "click",
    clearHistory
  );
}

document.addEventListener(
  "DOMContentLoaded",
  loadHistory
);
