import google.generativeai as genai

# Configure the API key (do this once before using the model)
genai.configure(api_key="AIzaSyBi3iPOsqyifA5WF--2FV79W9ZIGnVg4hk")

# Create the model instance
model = genai.GenerativeModel(model_name="gemini-1.5-flash")  # or "gemini-1.5-pro"

def script_ai(summary: str) -> dict:
    response = model.generate_content(
        f"Explain the meaning of the word '{summary}' in three line."
    )
    print(response.text)
    return response.text
