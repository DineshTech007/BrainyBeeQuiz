CREATE TABLE IF NOT EXISTS chess_study_concepts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    book_source TEXT,
    concept_name_en TEXT NOT NULL,
    concept_name_hi TEXT NOT NULL,
    concept_name_mr TEXT NOT NULL,
    explanation_en TEXT NOT NULL,
    explanation_hi TEXT NOT NULL,
    explanation_mr TEXT NOT NULL,
    fen TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
