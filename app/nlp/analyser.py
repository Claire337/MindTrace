"""
NLP Sentiment Analysis Module
Uses TextBlob for sentiment polarity analysis and keyword extraction
"""

from textblob import TextBlob
import json
from typing import Dict, List

# Emotion classification rules (keyword matching)
EMOTION_KEYWORDS = {
    'anxiety': ['worry', 'worried', 'anxious', 'anxiety', 'nervous', 'panic', 'dread', 'uneasy', 'overwhelm', 'stressed'],
    'stress': ['stress', 'stressed', 'pressure', 'deadline', 'exam', 'test', 'overload', 'overwhelmed', 'busy'],
    'loneliness': ['lonely', 'alone', 'isolated', 'isolation', 'solitude', 'nobody', 'miss', 'left out', 'abandoned'],
    'anger': ['angry', 'anger', 'furious', 'frustrated', 'annoy', 'annoyed', 'irritate', 'irritated', 'hate', 'conflict', 'argue'],
    'sadness': ['sad', 'sadness', 'depressed', 'depression', 'down', 'empty', 'numb', 'hopeless', 'desperate', 'cry', 'crying'],
    'satisfaction': ['happy', 'happiness', 'proud', 'proud', 'accomplish', 'accomplished', 'achieve', 'relief', 'relieved', 'great', 'wonderful', 'excellent'],
}

# Stop words (used to filter meaningless words)
STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
    'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
    'i', 'me', 'my', 'we', 'you', 'he', 'she', 'it', 'this', 'that', 'these', 'those',
    'just', 'very', 'so', 'too', 'also', 'not', 'no', 'as', 'if', 'about', 'from',
}


def analyse(text: str) -> Dict:
    """
    Analyse the sentiment and emotions in the text

    Args:
        text: Input text (journal entry)

    Returns:
        dict: {
            'sentiment_label': str,         # Positive / Neutral / Negative
            'sentiment_polarity': float,    # -1.0 ~ 1.0
            'emotion_labels': list,         # Detected emotion labels
            'keywords': list,               # Extracted keywords
            'nlp_summary': str              # One-sentence summary
        }
    """

    if not text or not text.strip():
        return {
            'sentiment_label': 'Neutral',
            'sentiment_polarity': 0.0,
            'emotion_labels': [],
            'keywords': [],
            'nlp_summary': 'You recorded a mood entry today.'
        }

    # 1. Sentiment polarity analysis
    blob = TextBlob(text.lower())
    polarity = blob.sentiment.polarity

    # Classify polarity
    if polarity > 0.1:
        sentiment_label = 'Positive'
    elif polarity < -0.1:
        sentiment_label = 'Negative'
    else:
        sentiment_label = 'Neutral'

    # 2. Fine-grained emotion classification (keyword matching)
    text_lower = text.lower()
    detected_emotions = []

    for emotion, keywords in EMOTION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                if emotion not in detected_emotions:
                    detected_emotions.append(emotion)
                break

    # 3. Keyword extraction
    noun_phrases = blob.noun_phrases
    keywords = []

    for phrase in noun_phrases:
        # Filter stop words and single-character words
        words = phrase.split()
        if len(words) > 0:
            # Keep the longest valid phrase
            valid = True
            for word in words:
                if word in STOP_WORDS:
                    valid = False
                    break
            if valid and len(phrase) > 2:  # Avoid phrases that are too short
                keywords.append(phrase)

    # Remove duplicates and limit results
    keywords = list(set(keywords))[:8]  # Keep the first 8

    # 4. Generate a one-sentence summary
    if detected_emotions:
        top_emotion = detected_emotions[0]
        top_keyword = keywords[0] if keywords else 'this feeling'

        if top_emotion == 'anxiety':
            summary = f"You seem mainly concerned about anxiety today, possibly triggered by {top_keyword}."
        elif top_emotion == 'stress':
            summary = f"Stress appears to be a dominant emotion today, related to {top_keyword}."
        elif top_emotion == 'loneliness':
            summary = f"You're experiencing loneliness, possibly related to {top_keyword}."
        elif top_emotion == 'anger':
            summary = f"You seem frustrated or angry today, possibly about {top_keyword}."
        elif top_emotion == 'sadness':
            summary = f"You're feeling down today, possibly related to {top_keyword}."
        elif top_emotion == 'satisfaction':
            summary = f"You seem satisfied and happy today, possibly because of {top_keyword}."
        else:
            summary = f"Your emotional state seems to relate to {top_keyword} today."
    elif sentiment_label == 'Positive':
        summary = "Your journal reflects a positive emotional state today."
    elif sentiment_label == 'Negative':
        summary = "Your journal reflects a challenging emotional state today."
    else:
        summary = "You recorded a neutral emotional state today."

    return {
        'sentiment_label': sentiment_label,
        'sentiment_polarity': round(polarity, 3),
        'emotion_labels': detected_emotions,
        'keywords': keywords,
        'nlp_summary': summary
    }


def analyse_entry(mood_entry):
    """
    Analyse a mood entry and update its NLP fields

    Args:
        mood_entry: MoodEntry database object
    """

    # Combine text (mood type + journal entry)
    text = f"{mood_entry.mood_type} {mood_entry.journal_text}"

    # Analyse
    result = analyse(text)

    # Update entry
    mood_entry.sentiment_label = result['sentiment_label']
    mood_entry.sentiment_polarity = result['sentiment_polarity']
    mood_entry.emotion_labels = json.dumps(result['emotion_labels'])
    mood_entry.keywords = json.dumps(result['keywords'])
    mood_entry.nlp_summary = result['nlp_summary']
