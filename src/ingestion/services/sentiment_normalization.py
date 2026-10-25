def normalize_sentiment_signal(data):
    if not data:
        return 0.0
    if isinstance(data, list):
        return 0.0
    return data.get('score', 0.0)
