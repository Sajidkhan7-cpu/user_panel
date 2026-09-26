# 🎓 College Enquiry Chatbot

An AI-powered college enquiry chatbot built with **FastAPI + Supabase
(PostgreSQL)** on the backend and **HTML/CSS/JavaScript** on the frontend.
Students can ask natural-language questions about **admission, fees, seat
availability, courses offered, and eligibility percentage**, and get
instant, accurate answers pulled directly from the college's database.

> Uses Supabase (a free hosted PostgreSQL database) instead of a local
> MySQL/XAMPP install — no local database server to install, configure, or
> keep running. Just paste a connection string and go.

# ✨ Features

- ## 🤖 Chatbot

The chatbot can answer questions related to:

- Admission process
- Required admission documents
- Courses offered
- Course fees
- Admission fees
- Yearly fees
- Total course fees
- Scholarships
- Seat availability
- Eligibility percentage
- Student percentage eligibility checking
- Frequently Asked Questions
- Greetings and general enquiries

- 🎙️ **Voice assistant** — ask questions by speech (mic button) and hear
  answers read aloud, using the browser's built-in Web Speech API

- 🔐 **JWT Authentication** for students and admins, including a
  key-protected **admin registration** page (`admin_register.html`)
- 🗂️ **Admin Dashboard** — CRUD for courses & FAQs, live stats
- 🎨 Clean, distinctive "enquiry desk" themed UI

## 🗂️ Project Structure

user-panel/
│
├── .venv/
│
├── backend/   Pyhton,FastAPI app, models, routers, services
│   │
│   └── app/
│       ├── __pycache__/
│       │
│       ├── dataset/
│       │   └── faq.json
│       │
│       ├── models/
│       │   ├── __pycache__/
│       │   ├── __init__.py
│       │   ├── chat.py
│       │   ├── course.py
│       │   ├── faq.py
│       │   └── user.py
│       │
│       ├── routers/
│       │   ├── __pycache__/
│       │   ├── __init__.py
│       │   ├── admin.py
│       │   ├── auth.py
│       │   ├── chatbot.py
│       │   ├── course.py
│       │   ├── faq.py
│       │   └── student.py
│       │
│       ├── schemas/
│       │   ├── __pycache__/
│       │   ├── __init__.py
│       │   ├── chat_schema.py
│       │   ├── course_schema.py
│       │   └── faq_schema.py
│       │
│       └── services/
│           ├── __pycache__/
│           ├── __init__.py
│           └── chatbot_service.py
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   │
│   └── services/
│       ├── __pycache__/
│       ├── __init__.py
│       ├── chatbot_service.py
│       ├── llm_service.py
│       ├── nlp.py
│       ├── pdf_reader.py
│       └── suggestion_service.py
│
├── database/   PostgreSQL schema + seed
│   ├── college_chatbot.sql
│   └── sample_data.sql
│
├── frontend/     HTML/CSS/JS pages
│   ├── assets/
│   │   ├── css/
│   │   │   ├── chatbot.css
│   │   │   ├── home.css
│   │   │   └── login.css
│   │   │
│   │   └── js/
│   │       ├── chatbot.js
│   │       ├── home.js
│   │       └── login.js
│   │
│   ├── about.html
│   ├── chatbot.html
│   ├── contact.html
│   ├── index.html
│   ├── login.html
│   └── register.html
│
├── .env
├── .gitignore
├── backfill_categories.py
├── export_training_data.py
├── requirements.txt
└── README.md

See inline comments in each file for details — every module has a docstring
explaining its purpose.

## 🚀 Setup Instructions

### ⚙️ Requirements

   Before running the project, install:

      Python 3.11 or 3.12
      Git
      Supabase account
      Internet connection


### Create your Supabase project
1. Go to https://supabase.com and sign up (GitHub/Google login works)
2. Click **New Project**
3. Pick any name, set a **database password** (write it down — you'll
   need it in step 4), choose the region closest to you
4. Wait ~2 minutes for the project to finish provisioning

### Create the tables
1. In your Supabase project, open the **SQL Editor** (left sidebar)
2. Click **New query**, paste the entire contents of
   `database/college_chatbot.sql`, click **Run**
3. Click **New query** again, paste the entire contents of
   `database/sample_data.sql`, click **Run**
4. Check it worked: go to **Table Editor** (left sidebar) — you should
   see `users`, `courses`, `faqs`, `chat_history`, and `admissions`
   tables, with `courses` and `faqs` already containing 7 rows each

### Get your connection string
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

## 📦 Package Installation

   From the `backend` folder:

   **powershell**
      cd backend

      Create virtual environment:

         python -m venv venv

      Activate it:

         .\venv\Scripts\Activate.ps1

      Install all required packages:

         pip install -r requirements.txt

   **Or install manually**

      pip install fastapi
      pip install uvicorn
      pip install sqlalchemy
      pip install psycopg2-binary
      pip install python-dotenv
      pip install python-jose
      pip install passlib
      pip install bcrypt
      pip install python-multipart
      pip install openai
      pip install rapidfuzz
      pip install pypdf

   **Check installed packages**

      pip list

   **Update pip**

      python -m pip install --upgrade pip

   **Recommended:** 
   
      Use `pip install -r requirements.txt` because it installs the exact packages configured for your project.


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

> Prefer to serve the frontend separately (e.g. VS Code Live Server)?
> That works too — each JS file auto-detects this and points API calls at
> `http://localhost:8000` instead of using relative paths.

## 🧠 How the Chatbot Works

The chatbot processing flow is:

               Student Question
                       │
                       ▼
              Clean & Tokenize
                       │
                       ▼
                Detect Intent
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
    Course Question            General Question
          │                         │
          ▼                         ▼
   Fuzzy Course Match          FAQ Matching
          │                         │
          └────────────┬────────────┘
                       │
                       ▼
               Supabase Database
                       │
                       ▼
                 Generate Answer
                       │
                       ▼
                   Student

## 🧠 Optional LLM Fallback

   The chatbot can optionally use an LLM for questions that cannot be handled by the normal rule-based system.

   The normal chatbot works without an external AI API.

   The optional LLM layer can be configured using providers that support an OpenAI-compatible API.

   For example:

      Google Gemini
      Groq
      OpenAI

   The LLM fallback is disabled by default.

## 🎙️ Voice Assistant

   The frontend supports browser-based voice features using the Web Speech API.

   Users can:

      Ask questions using their microphone.
      Convert speech into text.
      Receive chatbot answers.
      Listen to answers using text-to-speech.

## ⚙️ Requirements

   Before running the project, install:

      Python 3.11 or 3.12
      Git
      Supabase account
      Internet connection

## 🔐 Authentication

   The application uses JWT authentication.

   It supports authentication for:

      Students
      Administrators

   Authentication features include:

      Login
      Password hashing
      JWT tokens
      Protected API routes
      Admin registration protection


## 🔑 Database Configuration

      Create or edit:

      backend/.env

      Example:

         DATABASE_URL=your_supabase_postgresql_connection_string

         SECRET_KEY=your_long_random_secret_key

         ADMIN_REGISTRATION_KEY=your_admin_registration_key

         USE_LLM_FALLBACK=False

         OPENAI_API_KEY=
         OPENAI_BASE_URL=
         OPENAI_MODEL=

      Your .gitignore should contain:

         .env
         venv/
         __pycache__/
         *.pyc
         node_modules/

## 🗄️ Supabase Database Setup

   This project uses Supabase PostgreSQL instead of a local MySQL/XAMPP database.

   Step 1 — Create Supabase Project

      Create a project in Supabase.

      After creating the project, open:

      SQL Editor
      Step 2 — Create Database Tables

      Run:

         college_chatbot.sql

      in the Supabase SQL Editor.

      Then run:

         sample_data.sql

      This creates and populates the required database tables.

## 🐍 Backend Installation

   Open PowerShell in the project folder:

   cd D:\admin-panel\backend

   Create a virtual environment:

      python -m venv venv

   ctivate it:

      .\venv\Scripts\Activate.ps1

   Install dependencies:

      pip install -r requirements.txt

## 👤 Create Admin Account

   After configuring the database, run:

      python create_admin.py

   Follow the instructions to create the first administrator account.

   Passwords should be securely hashed before being stored in the database.

## 🌐 Run the Frontend

   The frontend is located inside:

      frontend/

   If the FastAPI application mounts the frontend as static files, the website can be accessed through:

      http://localhost:8080/

   You can also use VS Code Live Server for frontend development if the JavaScript API configuration points to the backend:

      http://localhost:8080

## ▶️ Run the Backend

   From the backend directory:

      python -m uvicorn app.main:app --reload --port 8080

   The backend will run at:

      http://localhost:8080

## 📚 API Documentation

   FastAPI automatically provides interactive API documentation.

   Open:

      http://localhost:8080/docs

   You can use the Swagger interface to test API endpoints.

## 🤖 Optional LLM Configuration

   The rule-based chatbot works without an LLM.

   To enable an OpenAI-compatible LLM provider, update:

      USE_LLM_FALLBACK=True
      OPENAI_API_KEY=your_api_key
      OPENAI_BASE_URL=provider_base_url
      OPENAI_MODEL=model_name

   The exact API endpoint, model name, pricing, and free-tier limits depend on the provider and may change.

   After changing .env, restart the backend.

## 🔒 Security

   The project includes several security mechanisms:

      JWT authentication
      Password hashing
      Protected admin routes
      Admin registration key
      Environment variables for secrets
      Database-backed authentication

## 🧩 Future Enhancements

   Possible future improvements include:

      Advanced NLP/intent classification
      RAG-based college knowledge system
      PDF document question answering
      Student admission application system
      Email notifications
      Student profile management
      Admin analytics
      Course recommendation system
      Multi-language chatbot
      WhatsApp integration
      Mobile application
      Deployment to cloud hosting

## 🧪 Development

   Useful development command:

      python -m uvicorn app.main:app --reload --port 8080

   Check the API:

      http://localhost:8080/docs

## 📌 Important Project Information

   Backend
      FastAPI
   Database
      Supabase PostgreSQL
   Frontend
      HTML
      CSS
      JavaScript
   Authentication
      JWT
   Chatbot
      Keyword Matching
      +
      Fuzzy Matching
      +
      FAQ Database
      +
      Optional LLM Fallback

## 👨‍🎓Project

   Project Title:

      College Enquiry Chatbot

      Purpose:
         To provide students with an automated system for getting college-related information quickly and efficiently.

## 📄 License

See `LICENSE`.