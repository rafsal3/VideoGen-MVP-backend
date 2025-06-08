from services.aitools import script_ai
def generate_script(summary: str,) -> dict:
    final_summary = script_ai(summary)
    return final_summary
