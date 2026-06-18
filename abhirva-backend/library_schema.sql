-- SQL Schema for Abhirva Learning Book Library
-- You can run this in your Supabase SQL Editor if you want to store Book Quizzes in dedicated tables.
-- (Currently, the app reuses the existing `quizzes` and `questions` tables to achieve this).

-- 1. Library Books (Quizzes) Table
CREATE TABLE library_quizzes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    grade VARCHAR(50) NOT NULL,
    language VARCHAR(50) NOT NULL,
    book_title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure we don't generate duplicate quizzes for the same book
    UNIQUE(grade, language, book_title)
);

-- 2. Library Questions Table
CREATE TABLE library_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    library_quiz_id UUID REFERENCES library_quizzes(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    options JSONB NOT NULL, -- Array of strings
    correct_option TEXT NOT NULL,
    marks INTEGER DEFAULT 1, -- 1 mark per question
    explanation_description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Update Profiles Table (for points)
-- Add this if you haven't already!
ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS book_points INTEGER DEFAULT 0;

-- 4. Book Quiz Attempts Table (Optional, for tracking individual student attempts)
CREATE TABLE library_test_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    library_quiz_id UUID REFERENCES library_quizzes(id) ON DELETE CASCADE,
    score INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    points_earned INTEGER NOT NULL,
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
