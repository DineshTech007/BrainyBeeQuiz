import json
import urllib.request
import urllib.error
import os

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        from dotenv import load_dotenv
        load_dotenv(override=True)
        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("NO API KEY")
        return

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={api_key}"

    print("Loading payload.json...")
    with open("payload.json", "r", encoding="utf-8") as f:
        payload = json.load(f)

    data = json.dumps(payload).encode('utf-8')
    print("Sending request...")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read()
            print("Response received successfully!")
            print(res_body.decode('utf-8')[:200])
    except urllib.error.HTTPError as e:
        print(f"HTTPError: {e.code} {e.reason}")
        print(e.read().decode('utf-8')[:200])
    except Exception as e:
        print(f"Other Error: {e}")

if __name__ == "__main__":
    main()
