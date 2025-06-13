import os
import json
import re
import time
import uuid
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from urllib.parse import quote

# Load environment variables
load_dotenv()
google_api_key = os.getenv("GEMINI_API_KEY")
unsplash_api_key = os.getenv("UNSPLASH_ACCESS_KEY")
genai.configure(api_key=google_api_key)

# Ensure output directory exists
BASE_ASSET_DIR = "output/assets"

# --- UTILITIES ---

def extract_json_from_response(response_text):
    try:
        match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            print("No valid JSON found in Gemini response.")
            return []
    except Exception as e:
        print(f"Error extracting JSON: {e}")
        return []

def search_and_save_image_unsplash(keyword, save_path):
    try:
        query = quote(keyword)
        url = f"https://api.unsplash.com/search/photos?query={query}&client_id={unsplash_api_key}&per_page=1"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"[Unsplash] Failed for {keyword}: {response.text}")
            return None

        data = response.json().get("results", [])
        if not data:
            print(f"[Unsplash] No image found for: {keyword}")
            return None

        image_url = data[0]["urls"]["regular"]
        image_data = requests.get(image_url).content
        with open(save_path, "wb") as f:
            f.write(image_data)
        return save_path
    except Exception as e:
        print(f"Error saving image for {keyword}: {e}")
        return None

def get_image_keywords(text):
    instruction = """
You are an AI assistant helping generate video content.
Extract only the meaningful image-based visual keywords from this sentence.
Ignore anything that should be text or gif.

Output format (JSON):
[
  {"order_id": 1, "type": "image", "keyword": "example keyword"},
  ...
]
"""
    prompt = instruction + "\n\nSentence:\n" + text
    model = genai.GenerativeModel("gemini-1.5-flash")

    safety = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    try:
        res = model.generate_content(prompt, safety_settings=safety)
        keywords = extract_json_from_response(res.text)
        return [kw for kw in keywords if kw["type"] == "image"]
    except Exception as e:
        print(f"Gemini error: {e}")
        return []

# --- MAIN FUNCTION ---

def generate_assets(script_chunk: str) -> list:
    # Create unique session folder
    session_id = str(uuid.uuid4())
    session_folder = os.path.join(BASE_ASSET_DIR, session_id)
    os.makedirs(session_folder, exist_ok=True)

    # Get image keywords
    keywords = get_image_keywords(script_chunk)
    assets = []

    for kw in keywords:
        keyword = kw["keyword"]
        order_id = kw["order_id"]

        filename = f"{order_id}_{re.sub(r'[^a-zA-Z0-9]+', '_', keyword.lower())}.jpg"
        filepath = os.path.join(session_folder, filename)

        # Download image
        result_path = search_and_save_image_unsplash(keyword, filepath)
        if result_path:
            assets.append({
                "order_id": order_id,
                "type": "image",
                "keyword": keyword,
                "url": f"/assets/{session_id}/{filename}"  # assumes FastAPI static route
            })

        time.sleep(1)  # to avoid rate limits

    return assets


# if __name__ == "__main__":
#     script = "a police jumping"
#     result = generate_assets(script)
#     print(json.dumps(result, indent=2))
