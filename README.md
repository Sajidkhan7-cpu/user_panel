# 🎓 College Enquiry Chatbot — Final Year Project

An AI-powered college enquiry chatbot built with **FastAPI + Supabase
(PostgreSQL)** on the backend and **HTML/CSS/JavaScript** on the frontend.
Students can ask natural-language questions about **admission, fees, seat
availability, courses offered, and eligibility percentage**, and get
instant, accurate answers pulled directly from the college's database.

> Uses Supabase (a free hosted PostgreSQL database) instead of a local
> MySQL/XAMPP install — no local database server to install, configure, or
> keep running. Just paste a connection string and go.

---

## ✨ Features

- 🤖 **AI Chatbot** — keyword + fuzzy-matching intent classification (no
  heavy ML dependency required), answers questions about:
  - Admission process & required documents
  - Course fees (admission fee, per-year fee, total fee, scholarships)
  - Seat availability per course
  - List of courses offered
  - Eligibility percentage required, including checking a student's own
    percentage against the cutoff
- 🧠 **LLM fallback (OpenAI)** — optional GPT-powered layer that handles
  chit-chat or oddly-phrased questions the rule-based engine can't
  classify, grounded in the same course/FAQ data so it can't invent fees,
  seats, or eligibility numbers. Disabled by default cost/API-key-free
  until you add an `OPENAI_API_KEY` in `.env`.
- 🎙️ **Voice assistant** — ask questions by speech (mic button) and hear
  answers read aloud, using the browser's built-in Web Speech API
- 🔐 **JWT Authentication** for students and admins, including a
  key-protected **admin registration** page (`admin_register.html`)
- 🗂️ **Admin Dashboard** — CRUD for courses & FAQs, live stats
- 💬 **Chat History** stored in Supabase, viewable per student/session
- 📄 **PDF knowledge extraction** utility for a college brochure
- 🎨 Clean, distinctive "enquiry desk" themed UI

---

## 🗂️ Project Structure

```
college-chatbot/
├── backend/            FastAPI app, models, routers, services
├── frontend/            Static HTML/CSS/JS pages
├── database/            PostgreSQL schema + seed data (Supabase)
├── docs/                 Diagrams & project report (add your own)
├── README.md
├── .gitignore
└── LICENSE
```

See inline comments in each file for details — every module has a docstring
explaining its purpose.

---

## 🚀 Setup Instructions

### 1. Prerequisites
- Python 3.11 or 3.12 (avoid brand-new Python releases — some packages
  don't have pre-built wheels for them yet)
- A free Supabase account — no credit card required

### 2. Create your Supabase project
1. Go to https://supabase.com and sign up (GitHub/Google login works)
2. Click **New Project**
3. Pick any name, set a **database password** (write it down — you'll
   need it in step 4), choose the region closest to you
4. Wait ~2 minutes for the project to finish provisioning

### 3. Create the tables
1. In your Supabase project, open the **SQL Editor** (left sidebar)
2. Click **New query**, paste the entire contents of
   `database/college_chatbot.sql`, click **Run**
3. Click **New query** again, paste the entire contents of
   `database/sample_data.sql`, click **Run**
4. Check it worked: go to **Table Editor** (left sidebar) — you should
   see `users`, `courses`, `faqs`, `chat_history`, and `admissions`
   tables, with `courses` and `faqs` already containing 7 rows each

### 4. Get your connection string
1. In Supabase: **Project Settings** (gear icon) → **Database**
2. Under **Connection string**, select the **URI** tab
3. Copy it — it looks like:
   ```
   postgresql://postgres.xxxxxxxxxxxx:[YOUR-PASSWORD]@aws-0-xx-xxxx-1.pooler.supabase.com:6543/postgres
   ```
4. Replace `[YOUR-PASSWORD]` with the database password from step 2

> Use the **"Session pooler"** or **"Transaction pooler"** string (not
> "Direct connection") if you're on a restrictive network/firewall — the
> pooler works over standard IPv4 and is what the URI tab gives you by
> default.

### 5. Configure environment variables
Edit `backend/.env`:
```
DATABASE_URL=postgresql://postgres.xxxxxxxxxxxx:your-actual-password@aws-0-xx-xxxx-1.pooler.supabase.com:6543/postgres
SECRET_KEY=change_this_to_a_long_random_secret_key
```
Paste your real connection string from step 4 as-is — the app
automatically handles the driver prefix for you.

### 6. Install dependencies
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 7. Create your first admin account
```bash
python create_admin.py
```
This safely bcrypt-hashes the password — never insert admin rows with
plaintext or fake password hashes directly into SQL.

### 8. Run the server
```bash
uvicorn app.main:app --reload
```
(Windows: if `uvicorn` isn't recognized as a command, use
`python -m uvicorn app.main:app --reload` instead — same result.)

The API runs at **http://localhost:8000**, and interactive API docs are
available at **http://localhost:8000/docs**.

Because `main.py` mounts the `frontend/` folder as static files, you can
also open **http://localhost:8000/** directly in your browser to use the
full website — home page, chatbot, login, and admin dashboard — with no
separate web server needed.

> Prefer to serve the frontend separately (e.g. VS Code Live Server)?
> That works too — each JS file auto-detects this and points API calls at
> `http://localhost:8000` instead of using relative paths.

---

## 🧠 How the Chatbot Works

`backend/app/services/chatbot_service.py` is the core logic:

1. **Clean & tokenize** the student's message (`services/nlp.py`)
2. **Classify intent** via keyword matching: `fees`, `seats`, `eligibility`,
   `admission`, `courses`, `contact`, `greeting`, `thanks`
3. **Detect the course** being asked about using fuzzy string matching
   against course names/short codes in the `courses` table
4. **Build an answer** directly from live Supabase data — so if an admin
   updates a course's fee or seat count in the dashboard, the chatbot's
   answer updates immediately
5. If no course-specific intent matches, it **falls back to the FAQ
   table**, and finally to a helpful default message

Example exchanges it handles out of the box:
- "What are the fees for B.Tech CSE?"
- "How many seats are available in MBA?"
- "I have 62%, am I eligible for ECE?"
- "What courses are available?"
- "How can I apply for admission?"

---

## 🧩 Enabling the LLM Fallback (Optional)

The chatbot works fully on rules + FAQ with zero external calls by default.
To turn on the AI-powered fallback for open-ended questions:

1. Get a **free** Gemini API key (no credit card): https://aistudio.google.com/apikey
2. In `backend/.env`, set:
   ```
   USE_LLM_FALLBACK=True
   OPENAI_API_KEY=your-gemini-key-here
   ```
   (`OPENAI_BASE_URL` and `OPENAI_MODEL` are already set to Gemini's
   free-tier defaults — no need to touch them)
3. Restart the server. That's it — no code changes needed.

This project talks to the LLM through the standard OpenAI Python SDK, but
points it at Google Gemini's OpenAI-compatible endpoint by default — since
**OpenAI's own API has no free tier** (it requires billing setup), while
Gemini offers a genuinely free tier (~1,500 requests/day, no card needed).

**Want a different provider?** Just change the three `.env` values —
no code changes:

| Provider | `OPENAI_BASE_URL` | `OPENAI_MODEL` | Get a key |
|---|---|---|---|
| Google Gemini (default, free) | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-2.5-flash` | https://aistudio.google.com/apikey |
| Groq (free, very fast) | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` | https://console.groq.com/keys |
| OpenAI (paid) | *(leave blank)* | `gpt-5.4-mini` | https://platform.openai.com/api-keys |

Model names and free-tier limits change over time — double check the
provider's docs if something stops working after a few months.

If the key is missing or the API call fails for any reason, the chatbot
automatically degrades to its default rule-based message — it never
breaks or throws an error to the student.

## 🔑 Admin Registration

Beyond `create_admin.py` (CLI), there's also a web form at
`admin_register.html`. It requires the `ADMIN_REGISTRATION_KEY` set in
`backend/.env` — anyone creating an admin account must know this key, so
random visitors can't self-promote to admin. Change this key before
deploying anywhere public.

---

## 🛠️ Extending the Project

- **NLP upgrade**: swap the keyword/fuzzy matcher in `services/nlp.py` for
  a proper intent-classification model (e.g. spaCy or a small transformer).
- **PDF knowledge base**: drop a real brochure at
  `backend/app/dataset/college.pdf` and wire `services/pdf_reader.py`
  into `chatbot_service.py` as an additional fallback source.
- **Admissions tracking**: the `admissions` table in the SQL schema is
  ready for a "Apply Now" flow that links a student to a course.

---

## 📄 License

See `LICENSE`.
