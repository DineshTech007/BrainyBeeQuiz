-- First, optionally drop the old table if it exists to keep DB clean
DROP TABLE IF EXISTS chess_study_concepts;

-- Create the new powerful V2 table with JSONB array for interactive steps
CREATE TABLE IF NOT EXISTS chess_study_concepts_v2 (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    book_source TEXT NOT NULL,
    concept_name_en TEXT NOT NULL,
    concept_name_hi TEXT NOT NULL,
    concept_name_mr TEXT NOT NULL,
    steps JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Note for `steps` JSONB structure:
-- [
--   {
--     "fen": "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
--     "notation": "Bb5",
--     "explanation_en": "White develops the bishop to attack the knight...",
--     "explanation_hi": "सफेद अपने ऊंट को...",
--     "explanation_mr": "पांढरा आपला उंट..."
--   },
--   ...
-- ]
