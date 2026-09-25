/**
 * chatbot.js
 * Enquiry chatbot UI: sends messages to /api/chatbot/ask, renders the chat,
 * shows follow-up suggestion chips returned by the backend, and (optionally)
 * fills a course ledger if an element with id="ledgerBody" exists.
 */

const API_BASE = window.location.port === "8000" ? "" : "http://localhost:8000";

const chatMessages = document.getElementById("chatMessages");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const quickChips = document.getElementById("quickChips");
const ledgerBody = document.getElementById("ledgerBody"); // optional (not in current HTML)
const micBtn = document.getElementById("micBtn");
const voiceStatus = document.getElementById("voiceStatus");
const voiceReplyToggle = document.getElementById("voiceReplyToggle");

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

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
  bubble.style.whiteSpace = "pre-line"; // keeps the bullet lists / line breaks from the backend
  bubble.textContent = text;
  msg.appendChild(bubble);
  chatMessages.appendChild(msg);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return msg;
}

// ---- follow-up suggestion chips (rendered under the latest bot reply) ----
function clearSuggestions() {
  document.querySelectorAll(".suggestions").forEach((el) => el.remove());
}

function appendSuggestions(list) {
  if (!Array.isArray(list) || !list.length) return;
  const wrap = document.createElement("div");
  wrap.className = "suggestions";
  list.forEach((text) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "suggestion-chip";
    btn.textContent = text;
    btn.addEventListener("click", () => sendMessage(text));
    wrap.appendChild(btn);
  });
  chatMessages.appendChild(wrap);
  chatMessages.scrollTop = chatMessages.scrollHeight;
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

  clearSuggestions();
  appendMessage(text, "user");
  chatInput.value = "";
  sendBtn.disabled = true;
  appendTypingIndicator();
  const startedAt = Date.now();

  try {
    const res = await fetch(`${API_BASE}/api/chatbot/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: getSessionId() }),
    });

    if (!res.ok) throw new Error(`Server responded with ${res.status}`);
    const data = await res.json();

    // Feels more human: the "typing" dots last a moment, longer for longer replies.
    const humanDelay = Math.min(1200, 400 + data.reply.length * 4);
    await sleep(Math.max(0, humanDelay - (Date.now() - startedAt)));

    removeTypingIndicator();
    appendMessage(data.reply, "bot");
    appendSuggestions(data.suggestions);
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
// Optional course ledger (only runs if #ledgerBody exists in the page)
// ---------------------------------------------------------------------------
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function seatClass(available, total) {
  if (available <= 0) return "seats-full";
  if (available / total <= 0.2) return "seats-low";
  return "seats-ok";
}

async function loadLedger() {
  if (!ledgerBody) return; // FIX: the current chatbot.html has no ledger, so skip quietly
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
        const seatLabel = c.available_seats <= 0 ? "Full" : `${c.available_seats}/${c.total_seats} open`;
        return `
          <div class="ledger-item">
            <span class="name">${escapeHtml(c.name)}</span>
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
// Voice Assistant — speech-to-text (mic) + text-to-speech (bot replies)
// ---------------------------------------------------------------------------
const savedVoicePref = localStorage.getItem("chatbot_voice_replies");
voiceReplyToggle.checked = savedVoicePref === null ? true : savedVoicePref === "true";

voiceReplyToggle.addEventListener("change", () => {
  localStorage.setItem("chatbot_voice_replies", voiceReplyToggle.checked);
  if (!voiceReplyToggle.checked) window.speechSynthesis.cancel();
});

function speakReply(text, opts = {}) {
  if (!opts.force && !voiceReplyToggle.checked) return;
  if (!("speechSynthesis" in window)) return;

  // Remove emojis/bullets so the voice doesn't read symbol names aloud.
  const cleanText = text
    .replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/gu, "")
    .replace(/[•\n]+/g, ". ")
    .replace(/₹/g, "rupees ");

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(cleanText);
  utterance.rate = 1;
  utterance.pitch = 1;
  utterance.lang = "en-IN";
  window.speechSynthesis.speak(utterance);
}

setTimeout(() => {
  const greeting = chatMessages.querySelector(".msg.bot .bubble");
  if (greeting) speakReply(greeting.textContent);
}, 600);

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
      window.speechSynthesis.cancel();
      recognition.start();
    }
  });
} else {
  micBtn.disabled = true;
  micBtn.title = "Voice input isn't supported in this browser. Try Chrome or Edge.";
  micBtn.style.opacity = "0.4";
}