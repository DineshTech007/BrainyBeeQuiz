-- Create the chess_variations table
CREATE TABLE IF NOT EXISTS chess_variations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    opening_name TEXT NOT NULL,
    variation_name_en TEXT NOT NULL,
    variation_name_mr TEXT,
    variation_name_hi TEXT,
    moves JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Note for `moves` JSONB structure:
-- [
--   {
--     "notation": "e4",
--     "board": [["r","n",...], ...],
--     "coach_text_en": "White opens with the King's Pawn...",
--     "coach_text_mr": "...",
--     "coach_text_hi": "...",
--     "tips_en": "Controls the center.",
--     "tips_mr": "...",
--     "tips_hi": "..."
--   },
--   ...
-- ]
