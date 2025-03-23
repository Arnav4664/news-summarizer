from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import requests
import logging
import nltk
import spacy
import uvicorn
import os
import re
from nltk.sentiment import SentimentIntensityAnalyzer
from utils import save_to_json, generate_report, text_to_speech, clean_hindi_text
import unicodedata
from textblob import TextBlob
from deep_translator import GoogleTranslator
from nltk.tokenize import sent_tokenize

nltk.download("punkt")
nltk.download("vader_lexicon")
sia = SentimentIntensityAnalyzer()
nlp = spacy.load("en_core_web_sm")

app = FastAPI()

API_KEY = "18d39fb98e7e42d8bd18b622f17c0bcf"

logging.basicConfig(level=logging.INFO)

def normalize_text(text):
    #Fixes encoding issues by normalizing Unicode characters.
    if isinstance(text, str):
        return unicodedata.normalize("NFKD", text)
    return text

def fetch_news_api(company_name):
    """Fetches news articles from NewsAPI."""
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": company_name,
        "apiKey": API_KEY,
        "language": "en",
        "pageSize": 10,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return []

        data = response.json()
        if not data.get("articles"):
            return []

        news_list = [
            {
                "title": normalize_text(article["title"]),  
                "summary": normalize_text(article.get("description", article["title"])),  
                "link": article["url"],
                "source": article["source"]["name"],
                "published_date": normalize_text(article.get("publishedAt", "Unknown")),  
            }
            for article in data["articles"]
            if article.get("title") and article.get("url")
        ]
        return news_list

    except requests.exceptions.RequestException:
        return []

def analyze_sentiment(news_articles):
    #Performs sentiment analysis using VADER and TextBlob.
    for article in news_articles:
        text = article.get("summary", "") or article.get("title", "")

        if text.strip():
            vader_score = sia.polarity_scores(text)["compound"]
            textblob_polarity = TextBlob(text).sentiment.polarity

            if vader_score > 0.05 and textblob_polarity > 0:
                final_sentiment = "Positive"
            elif vader_score < -0.05 and textblob_polarity < 0:
                final_sentiment = "Negative"
            else:
                final_sentiment = "Neutral"

            article["sentiment"] = final_sentiment
        else:
            article["sentiment"] = "Unknown"
    return news_articles

def clean_topic(topic):
    #Cleans extracted topics by removing unwanted characters.
    topic = topic.encode("utf-8").decode("utf-8", "ignore")  
    topic = re.sub(r"[\uFFFD]", "", topic)
    topic = re.sub(r"[^\w\s.,'-]", "", topic)  
    topic = re.sub(r"\s+", " ", topic).strip()  
    return topic

def extract_topics(news_articles):
    """Extracts key topics from news summaries using spaCy."""
    for article in news_articles:
        text = article.get("summary", "").strip()
        doc = nlp(text)

        raw_topics = [ent.text for ent in doc.ents if ent.label_ in ["ORG", "GPE", "MONEY", "LAW", "EVENT"]]
        cleaned_topics = [clean_topic(topic) for topic in raw_topics if topic]

        article["topics"] = list(set(cleaned_topics))
    return news_articles

def generate_news_audio(news_articles, filename="news_summary.mp3"):
    #Translates news summaries to Hindi and generates a Hindi speech audio file.
    if not news_articles:
        return None

    translated_texts = []
    news_count = 1

    for article in news_articles:
        original_text = article.get("summary") or article.get("title") or ""
        original_text = original_text.strip()

        if not original_text:
            continue

        try:
            sentences = sent_tokenize(original_text)
            translated_sentences = [
                GoogleTranslator(source="en", target="hi").translate(sent).strip() for sent in sentences if sent.strip()
            ]
            translated_summary = " ".join(translated_sentences)

            if not translated_summary.strip():
                continue

        except Exception:
            translated_summary = f"अनुवाद विफल हुआ: {original_text}"

        formatted_text = f"समाचार {news_count}: {translated_summary}"
        translated_texts.append(formatted_text)
        news_count += 1

    if not translated_texts:
        return None

    full_text = "\n\n".join(translated_texts).strip()
    output_path = os.path.abspath(filename)

    try:
        tts_file = text_to_speech(full_text, output_path, lang="hi")
        if tts_file and os.path.exists(tts_file):
            return tts_file
        return None
    except Exception:
        return None

@app.get("/fetch_news")
def fetch_news(company: str = Query(..., description="Enter the company name")):
    #Fetches news articles, performs sentiment analysis, and returns JSON.
    news = fetch_news_api(company)
    if not news:
        raise HTTPException(status_code=404, detail="No news articles found")

    final_news = extract_topics(analyze_sentiment(news))
    report = generate_report(final_news)

    return JSONResponse(content={"company": company, "articles": final_news, "report": report})

@app.get("/generate_tts")
def generate_tts(company: str = Query(..., description="Enter the company name")):
    #Fetches news, generates text-to-speech (TTS) audio in Hindi, and provides a downloadable link.
    news = fetch_news_api(company)

    if not news:
        raise HTTPException(status_code=404, detail="No news articles found for TTS")

    valid_news = [article for article in news if article.get("summary") or article.get("title")]

    if not valid_news:
        raise HTTPException(status_code=400, detail="No valid news summaries for TTS")

    audio_file = generate_news_audio(valid_news)

    if audio_file and os.path.exists(audio_file):
        return FileResponse(audio_file, media_type="audio/mpeg", filename="news_summary.mp3")

    raise HTTPException(status_code=500, detail="Failed to generate audio file")

