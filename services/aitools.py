from google import genai

client = genai.Client(api_key="AIzaSyBi3iPOsqyifA5WF--2FV79W9ZIGnVg4hk")



def script_ai(summary: str) -> dict:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="explain the meaning of the word " + summary + " in one line."
    )
    print(response.text)
    return response.text
