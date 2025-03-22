import json
import logging
import os
import re
import unicodedata
from collections import Counter
from gtts import gTTS
from googletrans import Translator  # ✅ Using googletrans

def normalize_text(text):
    """
    Fixes encoding issues like 'Elon Muskâs' by normalizing Unicode characters.
    Removes unnecessary control characters.
    """
    if isinstance(text, str):
        text = unicodedata.normalize("NFKC", text)  # Normalize Unicode
        text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)  # Remove zero-width characters
        text = re.sub(r"\s+", " ", text).strip()  # Remove extra spaces
    return text

# Configure Logging
logging.basicConfig(level=logging.INFO)

translator = Translator()  # ✅ Use googletrans instead of deep_translator
def translate_text(text, source_lang="en", target_lang="hi"):
    """
    Translates text while ensuring numbering (समाचार X) is not corrupted.
    """
    try:
        # ✅ Remove any existing "समाचार X:" before translation
        clean_text = re.sub(r"^समाचार\s*\d+:?\s*", "", text).strip()

        # ✅ Translate the content
        translated_text = translator.translate(clean_text, src=source_lang, dest=target_lang).text.strip()

        return translated_text
    except Exception as e:
        logging.error(f"❌ Translation Error: {e}")
        return text  # Return original text if translation fails

def text_to_speech(text, filename="news_summary.mp3", lang="hi"):
    """
    Converts translated Hindi text to speech using Google TTS (gTTS).
    Ensures that "समाचार X:" is added only in api.py.
    """
    try:
        # ✅ Normalize text to prevent encoding issues
        text = unicodedata.normalize("NFKC", text)

        if not text.strip():
            logging.error("⚠️ Translated text is empty. Cannot generate TTS.")
            return None

        # ✅ Log the clean text before passing to TTS
        logging.info(f"🗣️ Clean Hindi Text Before TTS:\n{text}")

        tts = gTTS(text=text, lang=lang, slow=False)
        output_path = os.path.abspath(filename)
        tts.save(output_path)

        if os.path.exists(output_path):
            logging.info(f"✅ Audio file generated successfully: {output_path}")
            return output_path
        else:
            logging.error("❌ TTS file generation failed.")
            return None

    except Exception as e:
        logging.error(f"⚠️ TTS Generation Error: {e}")
        return None

    
def save_to_json(data, filename="news_data.json"):
    """
    Saves structured data into a JSON file.
    """
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        logging.info(f"✅ Data saved to {filename}")
    except Exception as e:
        logging.error(f"❌ Error saving JSON: {e}")

def generate_report(news_articles):
    """
    Generates a structured report based on sentiment analysis and topics.
    """
    try:
        sentiment_counts = Counter(article.get("sentiment", "Unknown") for article in news_articles)
        all_topics = [normalize_text(topic) for article in news_articles for topic in article.get("topics", [])]
        topic_counts = Counter(all_topics)

        report = {
            "Sentiment Distribution": sentiment_counts,
            "Most Common Topics": topic_counts.most_common(5),
            "Unique Topics": list(set(all_topics))
        }

        return report
    except Exception as e:
        logging.error(f"❌ Error generating report: {e}")
        return {}

def clean_hindi_text(text):
    """
    Cleans Hindi text for better pronunciation in TTS.
    Keeps essential English words while removing unwanted symbols.
    """
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

    # Keep Hindi letters, English letters, numbers, sentence punctuation, and spaces
    text = re.sub(r'[^a-zA-Z\u0900-\u097F0-9.,:!?()\s]', '', text)

    # Ensure proper spacing
    text = re.sub(r'\s+', ' ', text).strip()

    return text
