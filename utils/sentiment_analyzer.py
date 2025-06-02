import os
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.data import find
from nltk import download

# === Ensure VADER lexicon is available ===
try:
    find('sentiment/vader_lexicon.zip')
except LookupError:
    download('vader_lexicon')

# === Initialize VADER Sentiment Analyzer ===
sia = SentimentIntensityAnalyzer()

def analyze_sentiment(headlines):
    results = []
    sentiment_scores = {'Buy': 0, 'Hold': 0, 'Sell': 0}

    for article in headlines:
        title = article.get('title', '').strip()
        if not title:
            continue  # Skip if no title

        score = sia.polarity_scores(title)['compound']

        if score >= 0.2:
            sentiment = 'Buy'
        elif score <= -0.2:
            sentiment = 'Sell'
        else:
            sentiment = 'Hold'

        sentiment_scores[sentiment] += 1

        results.append({
            'title': title,
            'url': article.get('url', '#'),
            'source': article.get('source', 'Unknown'),
            'date': article.get('publishedAt', article.get('date', 'N/A'))[:10],  # Consistent date format
            'sentiment': sentiment,
            'score': round(score, 3)
        })

    if not results:
        return [], "NO HEADLINES"

    # Determine final sentiment with highest count
    final_sentiment = max(sentiment_scores, key=sentiment_scores.get)
    return results, final_sentiment
