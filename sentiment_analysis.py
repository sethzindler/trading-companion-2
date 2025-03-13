#!/usr/bin/env python3
# Sentiment analysis for Stock Trading Companion

from textblob import TextBlob

def analyze_sentiment(news_data, console):
    """Analyze sentiment from news headlines"""
    if not news_data:
        return 0.5  # Neutral sentiment
        
    try:
        headlines = [news['headline'] for news in news_data if 'headline' in news]
        if not headlines:
            return 0.5
            
        sentiments = [TextBlob(headline).sentiment.polarity for headline in headlines]
        avg_sentiment = sum(sentiments) / len(sentiments)
        
        # Normalize to 0-1 range
        normalized_sentiment = (avg_sentiment + 1) / 2
        return normalized_sentiment
        
    except Exception as e:
        console.print(f"[yellow]Error analyzing sentiment: {e}[/yellow]")
        return 0.5