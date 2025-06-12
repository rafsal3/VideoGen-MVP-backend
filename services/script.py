import json
from services.aitools import script_ai

def generate_script(summary: str) -> dict:
    final_summary = script_ai(summary)
    
    # Split by periods and clean up the sentences
    sentences = [sentence.strip() for sentence in final_summary.split('.') if sentence.strip()]
    
    # Return as JSON structure
    result = {
        "original_text": final_summary,
        "sentences": sentences,
        "sentence_count": len(sentences)
    }
    
    return result

# Alternative version if you want just the sentences array
def generate_script_simple(summary: str) -> dict:
    final_summary = script_ai(summary)
    
    # Split by periods and clean up
    sentences = [sentence.strip() for sentence in final_summary.split('.') if sentence.strip()]
    
    return {"sentences": sentences}

# If you want to return actual JSON string instead of dict
def generate_script_json_string(summary: str) -> str:
    final_summary = script_ai(summary)
    
    sentences = [sentence.strip() for sentence in final_summary.split('.') if sentence.strip()]
    
    result = {"sentences": sentences}
    
    return json.dumps(result, indent=2)