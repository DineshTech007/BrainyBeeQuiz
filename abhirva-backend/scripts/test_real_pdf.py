import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.chess_parser import extract_text_from_pdf, parse_chess_variations_from_text

def main():
    path = r"F:\AbhirvaLearning\chess\opening\white\alapin\vdoc.pub_the-complete-c3-sicilian.pdf"
    print(f"Reading {path}...")
    text = extract_text_from_pdf(path, 20, 22)
    print(f"Extracted {len(text)} characters.")
    
    print("Calling Gemini...")
    try:
        variations = parse_chess_variations_from_text(text, "Alapin")
        print(f"Got {len(variations)} variations.")
        with open("test_output.json", "w", encoding="utf-8") as f:
            import json
            json.dump(variations, f, indent=2)
    except BaseException as e:
        import traceback
        with open("test_error.txt", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        print(f"Caught exception: {e}")

if __name__ == "__main__":
    main()
