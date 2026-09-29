-- =============================================================
-- college_chatbot.sql  (PostgreSQL / Supabase edition)
-- Creates all tables for the College Enquiry Chatbot.
-- Run this in the Supabase SQL Editor first, then sample_data.sql.
--
-- Note: unlike MySQL, you don't need to CREATE DATABASE here —
-- Supabase already gives every project a "postgres" database with
-- a "public" schema. These tables are created directly in it.
-- =============================================================

-- -------------------------------------------------------------
-- Enum types (Postgres requires these declared before use)
-- -------------------------------------------------------------
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('student', 'admin');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE admission_status AS ENUM ('pending', 'approved', 'rejected');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- -------------------------------------------------------------
-- Users (students + admins)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100)  NOT NULL,
    email           VARCHAR(150)  NOT NULL UNIQUE,
    phone           VARCHAR(20),
    password_hash   VARCHAR(255)  NOT NULL,
    role            user_role NOT NULL DEFAULT 'student',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- -------------------------------------------------------------
-- Courses (admission / fees / seats / eligibility)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS courses (
    id                      SERIAL PRIMARY KEY,
    name                    VARCHAR(150) NOT NULL UNIQUE,
    short_code              VARCHAR(20),
    duration_years          INT NOT NULL DEFAULT 4,
    total_seats             INT NOT NULL DEFAULT 0,
    available_seats         INT NOT NULL DEFAULT 0,
    total_fees              DECIMAL(12,2) NOT NULL DEFAULT 0,
    fees_per_year           DECIMAL(12,2) NOT NULL DEFAULT 0,
    admission_fee           DECIMAL(12,2) NOT NULL DEFAULT 0,
    eligibility_percentage  DECIMAL(5,2)  NOT NULL DEFAULT 0,
    eligibility_note        VARCHAR(255),
    scholarship_available   VARCHAR(255),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

-- Keep updated_at current on every UPDATE (Postgres has no built-in
-- "ON UPDATE CURRENT_TIMESTAMP" like MySQL, so we use a trigger).
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_courses_updated_at ON courses;
CREATE TRIGGER trg_courses_updated_at
    BEFORE UPDATE ON courses
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- -------------------------------------------------------------
-- FAQs (generic knowledge base, editable by admin)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS faqs (
    id          SERIAL PRIMARY KEY,
    category    VARCHAR(50) NOT NULL DEFAULT 'general',
    question    VARCHAR(255) NOT NULL,
    keywords    VARCHAR(255),
    answer      TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- -------------------------------------------------------------
-- Chat history
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chat_history (
    id          SERIAL PRIMARY KEY,
    user_id     INT REFERENCES users(id) ON DELETE SET NULL,
    session_id  VARCHAR(100),
    question    TEXT NOT NULL,
    answer      TEXT NOT NULL,
    intent      VARCHAR(50),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_history_session_id ON chat_history(session_id);

-- -------------------------------------------------------------
-- Admissions (optional: tracks a student's application per course)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admissions (
    id              SERIAL PRIMARY KEY,
    user_id         INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id       INT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    percentage      DECIMAL(5,2),
    status          admission_status DEFAULT 'pending',
    applied_at      TIMESTAMPTZ DEFAULT NOW()
);
