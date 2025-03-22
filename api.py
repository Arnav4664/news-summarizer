from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import requests
import logging
import nltk
import spacy
import os
import re
from nltk.sentiment import SentimentIntensityAnalyzer
from utils import save_to_json, generate_report, text_to_speech, clean_hindi_text
from googletrans import Translator
import unicodedata
from textblob import TextBlob
from deep_translator import GoogleTranslator
from nltk.tokenize import sent_tokenize
nltk.download("punkt")  # Ensure NLTK tokenizer is available

# Ensure necessary resources are downloaded
nltk.download("vader_lexicon")
sia = SentimentIntensityAnalyzer()
nlp = spacy.load("en_core_web_sm")

app = FastAPI()

# 🔹 Replace with your actual NewsAPI key
API_KEY = "18d39fb98e7e42d8bd18b622f17c0bcf"

# 🔹 Configure logging
logging.basicConfig(level=logging.INFO)

def normalize_text(text):
    """Fixes encoding issues like 'Elon Muskâs' by normalizing Unicode characters."""
    if isinstance(text, str):
        return unicodedata.normalize("NFKD", text)
    return text

def fetch_news_api(company_name):
    """ Fetches news articles from NewsAPI **in English**. """
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": company_name,
        "apiKey": API_KEY,
        "language": "en",
        "pageSize": 10,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        logging.info(f"🔍 Fetching news for '{company_name}' | Status Code: {response.status_code}")

        if response.status_code != 200:
            logging.error(f"❌ Error fetching news: {response.text}")
            return []

        data = response.json()

        if not data.get("articles"):
            logging.warning(f"⚠️ No news articles found for '{company_name}'.")
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

        logging.info(f"✅ Retrieved {len(news_list)} articles.")
        return news_list

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ API Request Failed: {e}")
        return []

def analyze_sentiment(news_articles):
    """Performs sentiment analysis using VADER and TextBlob."""
    for article in news_articles:
        text = article.get("summary", "") or article.get("title", "")

        if text.strip():
            # VADER Sentiment Analysis
            vader_score = sia.polarity_scores(text)["compound"]
            
            # TextBlob Sentiment Analysis
            textblob_analysis = TextBlob(text)
            textblob_polarity = textblob_analysis.sentiment.polarity  # (-1 to 1 scale)

            # Combining results
            if vader_score > 0.05 and textblob_polarity > 0:
                final_sentiment = "Positive"
            elif vader_score < -0.05 and textblob_polarity < 0:
                final_sentiment = "Negative"
            else:
                final_sentiment = "Neutral"

            article["sentiment"] = final_sentiment
        else:
            article["sentiment"] = "Unknown"

    logging.info("✅ Sentiment Analysis Completed.")
    return news_articles

def clean_topic(topic):
    """Fixes encoding issues, removes unwanted characters, and ensures proper formatting."""
    topic = topic.encode("utf-8").decode("utf-8", "ignore")  
    topic = re.sub(r"[\uFFFD]", "", topic)  # Remove unknown characters
    topic = re.sub(r"[^\w\s.,'-]", "", topic)  
    topic = re.sub(r"\s+", " ", topic).strip()  
    return topic

def extract_topics(news_articles):
    """Extracts and properly cleans key topics from news summaries using spaCy."""
    for article in news_articles:
        text = article.get("summary", "").strip()
        doc = nlp(text)

        # Extract raw entity names (organization, geopolitical entities, etc.)
        raw_topics = [ent.text for ent in doc.ents if ent.label_ in ["ORG", "GPE", "MONEY", "LAW", "EVENT"]]

        # Clean the extracted topics
        cleaned_topics = [clean_topic(topic) for topic in raw_topics if topic]

        # Remove duplicates and store cleaned topics
        article["topics"] = list(set(cleaned_topics))  # Remove duplicates
        logging.info(f"🟢 Final Topics (Filtered): {article['topics']}")  # Debugging step

    return news_articles

translator = Translator()
# translator = GoogleTranslator(source="en", target="hi")
import logging
import os
import nltk
from nltk.tokenize import sent_tokenize
from googletrans import Translator
from utils import text_to_speech  # ✅ Ensure correct import

nltk.download("punkt")  # ✅ Ensure sentence tokenizer is available
translator = Translator()

def generate_news_audio(news_articles, filename="news_summary.mp3"):
    """
    Translates news summaries to Hindi and generates a Hindi speech audio file.
    Ensures "समाचार X:" appears for each article only once.
    """
    if not news_articles:
        logging.error("⚠️ No valid news articles found for TTS.")
        return None

    translated_texts = []
    news_count = 1  # ✅ Correctly track article numbers

    for article in news_articles:
        original_text = article.get("summary") or article.get("title") or ""
        original_text = original_text.strip()

        if not original_text:
            logging.warning(f"⚠️ Skipping empty article.")
            continue  # ✅ Skip empty articles properly

        logging.info(f"📄 Original English Text {news_count}: {original_text}")

        try:
            # ✅ Use NLTK for **proper** sentence splitting
            sentences = sent_tokenize(original_text)

            translated_sentences = []
            for sent in sentences:
                translated_text = translator.translate(sent, src="en", dest="hi").text.strip()
                if translated_text:  # ✅ Ensure translation isn't empty
                    translated_sentences.append(translated_text)

            # ✅ Join translated sentences properly
            translated_summary = " ".join(translated_sentences)

            if not translated_summary.strip():
                logging.warning(f"⚠️ Empty translation for article {news_count}, skipping...")
                continue  # ✅ Skip if translation fails

        except Exception as e:
            logging.error(f"❌ Translation failed for article {news_count}: {e}")
            translated_summary = f"अनुवाद विफल हुआ: {original_text}"  # ✅ Fallback to English

        # ✅ Ensure "समाचार X:" is added **only once** after translation
        formatted_text = f"समाचार {news_count}: {translated_summary}"
        translated_texts.append(formatted_text)

        news_count += 1  # ✅ Move increment **outside** the sentence loop

    if not translated_texts:
        logging.error("⚠️ No valid text for TTS generation after processing all articles.")
        return None

    full_text = "\n\n".join(translated_texts).strip()

    # ✅ Debugging: Log exactly what is being passed to TTS
    logging.info(f"🗣️ Final Full Hindi Text for TTS:\n{full_text}")

    if not full_text:
        logging.error("⚠️ No valid text for TTS generation.")
        return None

    # ✅ Generate TTS
    output_path = os.path.abspath(filename)
    try:
        tts_file = text_to_speech(full_text, output_path, lang="hi")
        if tts_file and os.path.exists(tts_file):
            logging.info(f"✅ TTS file successfully generated: {tts_file}")
            return tts_file
        else:
            logging.error("❌ TTS file generation failed.")
            return None
    except Exception as e:
        logging.error(f"⚠️ Error generating TTS: {e}")
        return None

    
@app.get("/generate_tts")
def generate_tts(company: str = Query(..., description="Enter the company name")):
    """ Fetches news, generates text-to-speech (TTS) audio in **Hindi**, and provides a downloadable link. """
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

@app.get("/fetch_news")

def fetch_news(company: str = Query(..., description="Enter the company name")):
    """Fetches news articles for the given company, performs sentiment analysis, and returns JSON."""
    news = fetch_news_api(company)

    if not news:
        raise HTTPException(status_code=404, detail="No news articles found")

    # ✅ Apply Sentiment Analysis to each article
    analyzed_news = analyze_sentiment(news)

    # ✅ Extract topics properly
    final_news = extract_topics(analyzed_news)

    # ✅ Generate report
    report = generate_report(final_news)

    return JSONResponse(content={"company": company, "articles": final_news, "report": report})
