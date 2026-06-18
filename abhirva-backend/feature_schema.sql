-- SQL Schema updates for English Comprehension and Maths Text Input features

-- 1. Add Passage column to quizzes table (for reading comprehension)
ALTER TABLE quizzes 
ADD COLUMN IF NOT EXISTS passage TEXT;

-- 2. Add question_type column to questions table (defaults to MCQ)
ALTER TABLE questions 
ADD COLUMN IF NOT EXISTS question_type VARCHAR(50) DEFAULT 'MCQ';

-- 3. Add difficulty_level to questions table
ALTER TABLE questions 
ADD COLUMN IF NOT EXISTS difficulty_level VARCHAR(50);
