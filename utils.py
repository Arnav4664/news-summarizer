import json
import logging
import os
import re
import unicodedata
from collections import Counter
from gtts import gTTS
from deep_translator import GoogleTranslator

# Fixes encoding issues and removes unnecessary control characters
def normalize_text(text):
    if isinstance(text, str):
        text = unicodedata.normalize("NFKC", text)
        text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)  
        text = re.sub(r"\s+", " ", text).strip()
    return text

logging.basicConfig(level=logging.INFO)

# Translates text 
def translate_text(text, source_lang="en", target_lang="hi"):
    try:
        clean_text = re.sub(r"^समाचार\s*\d+:?\s*", "", text).strip()
        translated_text = GoogleTranslator(source=source_lang, target=target_lang).translate(clean_text)
        return translated_text.strip()
    except Exception as e:
        logging.error(f"Translation Error: {e}")
        return text  

# Converts translated Hindi text to speech using gTTS
def text_to_speech(text, filename="news_summary.mp3", lang="hi"):
    try:
        text = unicodedata.normalize("NFKC", text)

        if not text.strip():
            logging.error("Translated text is empty. Cannot generate TTS.")
            return None

        logging.info(f"Generating TTS for:\n{text}")

        tts = gTTS(text=text, lang=lang, slow=False)
        output_path = os.path.abspath(filename)
        tts.save(output_path)

        if os.path.exists(output_path):
            logging.info(f"Audio file generated successfully: {output_path}")
            return output_path
        else:
            logging.error("TTS file generation failed.")
            return None
    except Exception as e:
        logging.error(f"TTS Generation Error: {e}")
        return None

# Saves structured data into a JSON file
def save_to_json(data, filename="news_data.json"):
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        logging.info(f"Data saved to {filename}")
    except Exception as e:
        logging.error(f"Error saving JSON: {e}")

# Generates a structured report based on sentiment analysis and topics
def generate_report(news_articles):
    try:
        sentiment_counts = Counter(article.get("sentiment", "Unknown") for article in news_articles)
        all_topics = [normalize_text(topic) for article in news_articles for topic in article.get("topics", [])]
        topic_counts = Counter(all_topics)

        return {
            "Sentiment Distribution": sentiment_counts,
            "Most Common Topics": topic_counts.most_common(5),
            "Unique Topics": list(set(all_topics))
        }
    except Exception as e:
        logging.error(f"Error generating report: {e}")
        return {}

# Cleans Hindi text for better pronunciation in TTS
def clean_hindi_text(text):
    replacements = {
        "google": "गूगल",
        "microsoft": "माइक्रोसॉफ्ट",
        "apple": "एप्पल",
        "tesla": "टेस्ला",
        "india": "भारत",
        "company": "कंपनी",
        "news": "समाचार",
        "facebook": "फेसबुक",
        "twitter": "ट्विटर"
    }

    for eng, hindi in replacements.items():
        text = text.replace(eng, hindi).replace(eng.capitalize(), hindi)

    text = re.sub(r'[^a-zA-Z\u0900-\u097F0-9.,:!?()\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()

    return text