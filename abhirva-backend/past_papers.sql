-- SQL Schema for Dedicated Past Papers Feature

CREATE TABLE IF NOT EXISTS past_papers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    board VARCHAR(50) NOT NULL,
    grade VARCHAR(50) NOT NULL,
    subject VARCHAR(50) NOT NULL,
    year VARCHAR(10) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicate generations of the same past paper
    UNIQUE(board, grade, subject, year)
);

CREATE TABLE IF NOT EXISTS past_paper_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    past_paper_id UUID REFERENCES past_papers(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) DEFAULT 'MCQ',
    difficulty_level VARCHAR(50) DEFAULT 'Medium',
    options JSONB NOT NULL, -- Array of strings
    correct_option TEXT NOT NULL,
    solution_steps TEXT,
    explanation_description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
