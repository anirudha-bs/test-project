def normalize_sentiment_signal(feeds):
    if not feeds: return 0.0
    scores = [f.get('score', 0.0) for f in feeds]
    return sum(scores) / len(scores)
