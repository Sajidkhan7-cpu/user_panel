/**
 * home.js
 * Optional enhancement: pulls a couple of live course stats from the
 * backend to keep the homepage catalog card accurate. Fails silently
 * (falls back to the static values already in the HTML) if the API
 * isn't running yet.
 */

const API_BASE = window.location.port === "8000" ? "" : "http://localhost:8000";

async function refreshHomeStats() {
  try {
    const res = await fetch(`${API_BASE}/api/courses/`);
    if (!res.ok) return;
    const courses = await res.json();
    if (!courses.length) return;

    const totalCourses = courses.length;
    const minFee = Math.min(...courses.map((c) => c.fees_per_year));
    const maxFee = Math.max(...courses.map((c) => c.fees_per_year));
    const minAdmissionFee = Math.min(...courses.map((c) => c.admission_fee));
    const avgEligibility = (
      courses.reduce((sum, c) => sum + Number(c.eligibility_percentage), 0) / totalCourses
    ).toFixed(0);

    const dl = document.querySelector(".catalog-card dl");
    if (!dl) return;
    dl.innerHTML = `
      <dt>Courses offered</dt><dd>${totalCourses} UG / PG programs</dd>
      <dt>Avg. eligibility</dt><dd>${avgEligibility}%+ in qualifying exam</dd>
      <dt>Fee range / yr</dt><dd>₹${minFee.toLocaleString("en-IN")} – ₹${maxFee.toLocaleString("en-IN")}</dd>
      <dt>Admission fee</dt><dd>From ₹${minAdmissionFee.toLocaleString("en-IN")}</dd>
      <dt>Assistant availability</dt><dd>24 × 7</dd>
    `;
  } catch (err) {
    // Backend not reachable yet — keep the static placeholder values.
    console.warn("Home stats not loaded (backend offline):", err.message);
  }
}

refreshHomeStats();
