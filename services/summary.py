def generate_summary(news_text: str, model: str, duration: str) -> str:
    # Dummy summary
    # return "you typed " + news_text + " and  you selected " + model + " and " + duration + " as duration"
    return [
        {
            "text": f"Summary of {news_text} using model {model} with duration {duration}",
            "model": model,
            "duration": duration
        }
    ]
