/**
 * chatbot.js
 * Authenticated college enquiry chatbot.
 * Every message is sent with the logged-in user's JWT.
 */

const API_BASE =
  window.location.port === "8000"
    ? ""
    : "http://localhost:8000";

const chatMessages = document.getElementById("chatMessages");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const quickChips = document.getElementById("quickChips");
const ledgerBody = document.getElementById("ledgerBody");
const micBtn = document.getElementById("micBtn");
const voiceStatus = document.getElementById("voiceStatus");
const voiceReplyToggle =
  document.getElementById("voiceReplyToggle");

const sleep = (ms) =>
  new Promise((resolve) => setTimeout(resolve, ms));

// ------------------------------------------------------------
// Authentication
// ------------------------------------------------------------

function getToken() {
  return localStorage.getItem("access_token");
}

function requireToken() {
  if (!getToken()) {
    window.location.replace("login.html");
    return false;
  }

  return true;
}

// ------------------------------------------------------------
// Session
// ------------------------------------------------------------

function getSessionId() {
  let sessionId =
    localStorage.getItem("chatbot_session_id");

  if (!sessionId) {
    const user = JSON.parse(
      localStorage.getItem("user") || "{}"
    );

    sessionId =
      `user-${user.id || "unknown"}-${Date.now()}-${Math.random()
        .toString(36)
        .slice(2, 7)}`;

    localStorage.setItem(
      "chatbot_session_id",
      sessionId
    );
  }

  return sessionId;
}

// ------------------------------------------------------------
// Chat UI
// ------------------------------------------------------------

function appendMessage(text, sender) {
  const msg = document.createElement("div");
  msg.className = `msg ${sender}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.style.whiteSpace = "pre-line";
  bubble.textContent = text;

  msg.appendChild(bubble);
  chatMessages.appendChild(msg);

  chatMessages.scrollTop =
    chatMessages.scrollHeight;

  return msg;
}

function clearSuggestions() {
  document
    .querySelectorAll(".suggestions")
    .forEach((el) => el.remove());
}

function appendSuggestions(list) {
  if (!Array.isArray(list) || !list.length) return;

  const wrap = document.createElement("div");
  wrap.className = "suggestions";

  list.forEach((text) => {
    const button = document.createElement("button");

    button.type = "button";
    button.className = "suggestion-chip";
    button.textContent = text;

    button.addEventListener(
      "click",
      () => sendMessage(text)
    );

    wrap.appendChild(button);
  });

  chatMessages.appendChild(wrap);
  chatMessages.scrollTop =
    chatMessages.scrollHeight;
}

function appendTypingIndicator() {
  const msg = document.createElement("div");

  msg.className = "msg bot";
  msg.id = "typingIndicator";

  msg.innerHTML = `
    <div class="bubble typing-dots">
      <span></span>
      <span></span>
      <span></span>
    </div>
  `;

  chatMessages.appendChild(msg);
  chatMessages.scrollTop =
    chatMessages.scrollHeight;
}

function removeTypingIndicator() {
  const element =
    document.getElementById(
      "typingIndicator"
    );

  if (element) element.remove();
}

// ------------------------------------------------------------
// SEND MESSAGE
// ------------------------------------------------------------

async function sendMessage(text, options = {}) {
  if (!requireToken()) return;

  if (!text || !text.trim()) return;

  const spokenByVoice =
    !!options.viaVoice;

  clearSuggestions();

  appendMessage(text, "user");

  chatInput.value = "";
  sendBtn.disabled = true;

  appendTypingIndicator();

  const startedAt = Date.now();

  try {
    const response = await fetch(
      `${API_BASE}/api/chatbot/ask`,
      {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
          Authorization:
            `Bearer ${getToken()}`,
        },

        body: JSON.stringify({
          message: text,
          session_id: getSessionId(),
        }),
      }
    );

    if (response.status === 401) {
      logoutUser();
      return;
    }

    if (!response.ok) {
      const errorData =
        await response.json().catch(
          () => ({})
        );

      throw new Error(
        errorData.detail ||
        `Server responded with ${response.status}`
      );
    }

    const data =
      await response.json();

    const reply =
      data.reply || "No reply received.";

    const humanDelay =
      Math.min(
        1200,
        400 + reply.length * 4
      );

    await sleep(
      Math.max(
        0,
        humanDelay -
          (Date.now() - startedAt)
      )
    );

    removeTypingIndicator();

    appendMessage(
      reply,
      "bot"
    );

    appendSuggestions(
      data.suggestions
    );

    speakReply(
      reply,
      { force: spokenByVoice }
    );

    if (data.session_id) {
      localStorage.setItem(
        "chatbot_session_id",
        data.session_id
      );
    }

  } catch (error) {
    removeTypingIndicator();

    appendMessage(
      "Sorry, I couldn't reach the server right now. Please try again.",
      "bot"
    );

    console.error(
      "Chatbot error:",
      error
    );

  } finally {
    sendBtn.disabled = false;
    chatInput.focus();
  }
}

// ------------------------------------------------------------
// EVENTS
// ------------------------------------------------------------

if (sendBtn) {
  sendBtn.addEventListener(
    "click",
    () => sendMessage(chatInput.value)
  );
}

if (chatInput) {
  chatInput.addEventListener(
    "keydown",
    (event) => {
      if (event.key === "Enter") {
        sendMessage(chatInput.value);
      }
    }
  );
}

if (quickChips) {
  quickChips.addEventListener(
    "click",
    (event) => {
      const chip =
        event.target.closest(".chip");

      if (chip) {
        sendMessage(
          chip.dataset.msg
        );
      }
    }
  );
}

// ------------------------------------------------------------
// COURSE LEDGER
// ------------------------------------------------------------

function escapeHtml(value) {
  return String(value).replace(
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

function seatClass(
  available,
  total
) {
  if (available <= 0)
    return "seats-full";

  if (
    total > 0 &&
    available / total <= 0.2
  ) {
    return "seats-low";
  }

  return "seats-ok";
}

async function loadLedger() {
  if (!ledgerBody) return;

  try {
    const response =
      await fetch(
        `${API_BASE}/api/courses/`,
        {
          headers: {
            Authorization:
              `Bearer ${getToken()}`,
          },
        }
      );

    if (response.status === 401) {
      logoutUser();
      return;
    }

    if (!response.ok) {
      throw new Error(
        "Failed to load courses"
      );
    }

    const courses =
      await response.json();

    if (!courses.length) {
      ledgerBody.innerHTML =
        `<div class="ledger-item">
          <span class="name">
            No course data yet
          </span>
        </div>`;

      return;
    }

    ledgerBody.innerHTML =
      courses
        .map((course) => {
          const cls =
            seatClass(
              course.available_seats,
              course.total_seats
            );

          const seatLabel =
            course.available_seats <= 0
              ? "Full"
              : `${course.available_seats}/${course.total_seats} open`;

          return `
            <div class="ledger-item">
              <span class="name">
                ${escapeHtml(course.name)}
              </span>

              <div class="row">
                <span>Eligibility</span>
                <span>
                  ${course.eligibility_percentage}%
                </span>
              </div>

              <div class="row">
                <span>Fees / yr</span>
                <span>
                  ₹${Number(
                    course.fees_per_year
                  ).toLocaleString("en-IN")}
                </span>
              </div>

              <div class="row">
                <span>Seats</span>
                <span class="${cls}">
                  ${seatLabel}
                </span>
              </div>
            </div>
          `;
        })
        .join("");

  } catch (error) {
    console.error(
      "Ledger error:",
      error
    );

    ledgerBody.innerHTML =
      `<div class="ledger-item">
        <span class="name">
          Could not load course data.
        </span>
      </div>`;
  }
}

// ------------------------------------------------------------
// VOICE REPLY
// ------------------------------------------------------------

if (voiceReplyToggle) {
  const savedVoicePref =
    localStorage.getItem(
      "chatbot_voice_replies"
    );

  voiceReplyToggle.checked =
    savedVoicePref === null
      ? true
      : savedVoicePref === "true";

  voiceReplyToggle.addEventListener(
    "change",
    () => {
      localStorage.setItem(
        "chatbot_voice_replies",
        voiceReplyToggle.checked
      );

      if (
        !voiceReplyToggle.checked &&
        "speechSynthesis" in window
      ) {
        window.speechSynthesis.cancel();
      }
    }
  );
}

function speakReply(
  text,
  options = {}
) {
  if (
    !options.force &&
    voiceReplyToggle &&
    !voiceReplyToggle.checked
  ) {
    return;
  }

  if (
    !("speechSynthesis" in window)
  ) {
    return;
  }

  const cleanText =
    text
      .replace(
        /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/gu,
        ""
      )
      .replace(/[•\n]+/g, ". ")
      .replace(/₹/g, "rupees ");

  window.speechSynthesis.cancel();

  const utterance =
    new SpeechSynthesisUtterance(
      cleanText
    );

  utterance.rate = 1;
  utterance.pitch = 1;
  utterance.lang = "en-IN";

  window.speechSynthesis.speak(
    utterance
  );
}

// ------------------------------------------------------------
// VOICE INPUT
// ------------------------------------------------------------

const SpeechRecognition =
  window.SpeechRecognition ||
  window.webkitSpeechRecognition;

let recognition = null;
let isListening = false;

if (SpeechRecognition && micBtn) {
  recognition =
    new SpeechRecognition();

  recognition.lang = "en-IN";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    isListening = true;

    micBtn.classList.add(
      "listening"
    );

    voiceStatus.textContent =
      "🎙️ Listening... speak your question now.";
  };

  recognition.onresult =
    (event) => {
      const transcript =
        event.results[0][0]
          .transcript;

      chatInput.value =
        transcript;

      voiceStatus.textContent =
        `Heard: "${transcript}"`;

      sendMessage(
        transcript,
        { viaVoice: true }
      );
    };

  recognition.onerror =
    (event) => {
      voiceStatus.textContent =
        event.error ===
        "not-allowed"
          ? "Microphone access was denied."
          : `Voice input error: ${event.error}`;
    };

  recognition.onend = () => {
    isListening = false;

    micBtn.classList.remove(
      "listening"
    );

    setTimeout(() => {
      if (!isListening) {
        voiceStatus.textContent =
          "";
      }
    }, 3000);
  };

  micBtn.addEventListener(
    "click",
    () => {
      if (isListening) {
        recognition.stop();
      } else {
        window.speechSynthesis.cancel();
        recognition.start();
      }
    }
  );

} else if (micBtn) {
  micBtn.disabled = true;
  micBtn.title =
    "Voice input is not supported in this browser.";
  micBtn.style.opacity = "0.4";
}

// ------------------------------------------------------------
// START
// ------------------------------------------------------------

requireToken();
loadLedger();

if (chatInput) {
  chatInput.focus();
}
