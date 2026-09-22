/**
 * chatbot.js
 * Handles the enquiry chatbot UI: sending messages to the FastAPI
 * backend (/api/chatbot/ask), rendering the conversation, and
 * populating the "Course Quick Reference" ledger from /api/courses/.
 */

// If the frontend is served by FastAPI itself (StaticFiles mount in main.py),
// relative paths work directly. If you run the frontend separately
// (e.g. VS Code Live Server), change API_BASE to the backend URL below.
const API_BASE = window.location.port === "8000" ? "" : "http://localhost:8000";

const chatMessages = document.getElementById("chatMessages");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const quickChips = document.getElementById("quickChips");
const ledgerBody = document.getElementById("ledgerBody");
const micBtn = document.getElementById("micBtn");
const voiceStatus = document.getElementById("voiceStatus");
const voiceReplyToggle = document.getElementById("voiceReplyToggle");

// Persist a session id across page reloads so chat history stays linked.
function getSessionId() {
  let sid = localStorage.getItem("chatbot_session_id");
  if (!sid) {
    sid = "guest-" + Math.random().toString(36).slice(2) + Date.now();
    localStorage.setItem("chatbot_session_id", sid);
  }
  return sid;
}

function appendMessage(text, sender) {
  const msg = document.createElement("div");
  msg.className = `msg ${sender}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  msg.appendChild(bubble);
  chatMessages.appendChild(msg);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return msg;
}

function appendTypingIndicator() {
  const msg = document.createElement("div");
  msg.className = "msg bot";
  msg.id = "typingIndicator";
  msg.innerHTML = `<div class="bubble typing-dots"><span></span><span></span><span></span></div>`;
  chatMessages.appendChild(msg);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
  const el = document.getElementById("typingIndicator");
  if (el) el.remove();
}

async function sendMessage(text, opts = {}) {
  if (!text || !text.trim()) return;
  const spokenByVoice = !!opts.viaVoice;

  appendMessage(text, "user");
  chatInput.value = "";
  sendBtn.disabled = true;
  appendTypingIndicator();

  try {
    const res = await fetch(`${API_BASE}/api/chatbot/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: getSessionId() }),
    });

    if (!res.ok) throw new Error(`Server responded with ${res.status}`);
    const data = await res.json();

    removeTypingIndicator();
    appendMessage(data.reply, "bot");
    // Always speak the answer if the question itself was asked by voice,
    // even if "Voice replies" is switched off — that's the clear intent.
    speakReply(data.reply, { force: spokenByVoice });

    if (data.session_id) {
      localStorage.setItem("chatbot_session_id", data.session_id);
    }
  } catch (err) {
    removeTypingIndicator();
    appendMessage(
      "Sorry, I couldn't reach the server right now. Please make sure the backend is running and try again.",
      "bot"
    );
    console.error("Chatbot error:", err);
  } finally {
    sendBtn.disabled = false;
    chatInput.focus();
  }
}

sendBtn.addEventListener("click", () => sendMessage(chatInput.value));
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage(chatInput.value);
});

quickChips.addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (chip) sendMessage(chip.dataset.msg);
});

// ---------------------------------------------------------------------------
// Populate the course quick-reference ledger on the right
// ---------------------------------------------------------------------------
function seatClass(available, total) {
  if (available <= 0) return "seats-full";
  if (available / total <= 0.2) return "seats-low";
  return "seats-ok";
}

async function loadLedger() {
  try {
    const res = await fetch(`${API_BASE}/api/courses/`);
    if (!res.ok) throw new Error("Failed to load courses");
    const courses = await res.json();

    if (!courses.length) {
      ledgerBody.innerHTML = `<div class="ledger-item"><span class="name">No course data yet</span></div>`;
      return;
    }

    ledgerBody.innerHTML = courses
      .map((c) => {
        const cls = seatClass(c.available_seats, c.total_seats);
        const seatLabel =
          c.available_seats <= 0 ? "Full" : `${c.available_seats}/${c.total_seats} open`;
        return `
          <div class="ledger-item">
            <span class="name">${c.name}</span>
            <div class="row"><span>Eligibility</span><span>${c.eligibility_percentage}%</span></div>
            <div class="row"><span>Fees / yr</span><span>₹${Number(c.fees_per_year).toLocaleString("en-IN")}</span></div>
            <div class="row"><span>Seats</span><span class="${cls}">${seatLabel}</span></div>
          </div>`;
      })
      .join("");
  } catch (err) {
    ledgerBody.innerHTML = `<div class="ledger-item"><span class="name">Could not load course data. Is the backend running?</span></div>`;
    console.error("Ledger load error:", err);
  }
}

loadLedger();
chatInput.focus();

// ---------------------------------------------------------------------------
// Voice Assistant — speech-to-text (mic input) + text-to-speech (bot replies)
// Uses the browser's built-in Web Speech API. No backend changes needed.
// Supported in Chrome/Edge; not supported in Firefox or most iOS browsers.
// ---------------------------------------------------------------------------

// Remember the user's voice-reply preference across visits.
// Defaults to ON so answers are spoken automatically unless the user turns it off.
const savedVoicePref = localStorage.getItem("chatbot_voice_replies");
voiceReplyToggle.checked = savedVoicePref === null ? true : savedVoicePref === "true";

voiceReplyToggle.addEventListener("change", () => {
  localStorage.setItem("chatbot_voice_replies", voiceReplyToggle.checked);
  if (!voiceReplyToggle.checked) window.speechSynthesis.cancel();
});

function speakReply(text, opts = {}) {
  if (!opts.force && !voiceReplyToggle.checked) return;
  if (!("speechSynthesis" in window)) return;

  // Strip characters that read awkwardly aloud (bullets, extra symbols).
  const cleanText = text.replace(/[•\n]+/g, ". ").replace(/₹/g, "rupees ");

  window.speechSynthesis.cancel(); // stop any reply currently being read
  const utterance = new SpeechSynthesisUtterance(cleanText);
  utterance.rate = 1;
  utterance.pitch = 1;
  utterance.lang = "en-IN";
  window.speechSynthesis.speak(utterance);
}

// Speak the initial greeting aloud too, once voices are ready (browsers load
// speech synthesis voices asynchronously, so a short delay avoids silence).
setTimeout(() => {
  const greeting = chatMessages.querySelector(".msg.bot .bubble");
  if (greeting) speakReply(greeting.textContent);
}, 600);

// ---------------- Speech-to-text (mic button) ----------------
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let isListening = false;

if (SpeechRecognition) {
  recognition = new SpeechRecognition();
  recognition.lang = "en-IN";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    isListening = true;
    micBtn.classList.add("listening");
    voiceStatus.textContent = "🎙️ Listening... speak your question now.";
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    chatInput.value = transcript;
    voiceStatus.textContent = `Heard: "${transcript}"`;
    sendMessage(transcript, { viaVoice: true });
  };

  recognition.onerror = (event) => {
    voiceStatus.textContent =
      event.error === "not-allowed"
        ? "Microphone access was denied. Please allow mic permissions and try again."
        : `Voice input error: ${event.error}`;
  };

  recognition.onend = () => {
    isListening = false;
    micBtn.classList.remove("listening");
    setTimeout(() => {
      if (!isListening) voiceStatus.textContent = "";
    }, 3000);
  };

  micBtn.addEventListener("click", () => {
    if (isListening) {
      recognition.stop();
    } else {
      window.speechSynthesis.cancel(); // don't talk over the user
      recognition.start();
    }
  });
} else {
  // Browser doesn't support speech recognition (e.g. Firefox) — disable gracefully.
  micBtn.disabled = true;
  micBtn.title = "Voice input isn't supported in this browser. Try Chrome or Edge.";
  micBtn.style.opacity = "0.4";
}
