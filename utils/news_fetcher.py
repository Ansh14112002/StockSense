import requests
from bs4 import BeautifulSoup

NEWSAPI_KEY = '0a80d45db45a4355b50af19bfb7fb723'  # ✅ Replace with your key

def fetch_news(symbol):
    query = symbol + " stock"
    url = f'https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&language=en&apiKey={NEWSAPI_KEY}'

    headlines = []
    try:
        response = requests.get(url)
        data = response.json()
        if 'articles' in data and data['articles']:
            for article in data['articles'][:10]:
                headlines.append({
                    "title": article.get("title"),
                    "url": article.get("url"),
                    "source": article.get("source", {}).get("name", "Unknown"),
                    "publishedAt": article.get("publishedAt", "")[:10]
                })
            return headlines
    except Exception as e:
        print("NewsAPI Error:", e)

    # Fallback to Yahoo Finance
    try:
        print("Falling back to Yahoo scraping...")
        headers = {'User-Agent': 'Mozilla/5.0'}
        yahoo_url = f'https://finance.yahoo.com/quote/{symbol}/news?p={symbol}'
        res = requests.get(yahoo_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')

        articles = soup.select('li.js-stream-content h3 a')
        for article in articles[:10]:
            headlines.append({
                "title": article.text.strip(),
                "url": "https://finance.yahoo.com" + article['href'],
                "source": "Yahoo Finance",
                "publishedAt": "N/A"
            })
        return headlines if headlines else [{"title": "No fallback headlines available."}]
    except Exception as e:
        print("Fallback Error:", e)
        return [{"title": "No news could be fetched."}]
