import os
import sys

# Ensure backend root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.chess_parser import parse_chess_variations_from_text

def main():
    print("Testing Gemini API...")
    try:
        # A small fake text
        text = "The Alapin Sicilian starts with 1. e4 c5 2. c3. White aims to build a strong center with d4."
        variations = parse_chess_variations_from_text(text, "Alapin")
        print(f"Variations: {variations}")
    except Exception as e:
        print(f"Exception caught: {e}")

if __name__ == "__main__":
    main()
