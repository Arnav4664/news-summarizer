import streamlit as st
import subprocess
import time
import requests
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from api import fetch_news_api, analyze_sentiment, extract_topics
from utils import save_to_json, generate_report, text_to_speech, clean_hindi_text
import os
import spacy
import tempfile

# Ensure spaCy model is downloaded
subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])

app = FastAPI()

# Start FastAPI backend in a subprocess
backend_process = subprocess.Popen(["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"])

# Wait for backend to start
time.sleep(5)

# Backend API URL
BASE_URL = "http://127.0.0.1:8000"

# Streamlit Frontend
st.title("Hindi News Summarizer with TTS")

with st.form("news_form"):
    company = st.text_input("Enter company name", "")
    submitted = st.form_submit_button("Fetch News")

if submitted:
    if company:
        response = requests.get(f"{BASE_URL}/fetch_news", params={"company": company})
        
        if response.status_code == 200:
            data = response.json()
            news_articles = data.get("articles", [])
            report = data.get("report", {})

            if news_articles:
                st.subheader("Latest News in English")
                for article in news_articles:
                    st.write(f"### {article['title']}")
                    st.write(f"📅 {article['published_date']} | 🏢 {article['source']}")
                    st.write(f"**Summary:** {article['summary']}")
                    st.write(f"🔹 Sentiment: {article.get('sentiment', 'Unknown')}")
                    st.write(f"🔍 Topics: {', '.join(article.get('topics', [])) if article.get('topics') else 'N/A'}")
                    st.markdown(f"[Read More]({article['link']})", unsafe_allow_html=True)
                    st.write("---")

                st.subheader("Sentiment & Topics Report")
                st.json(report.get("Sentiment Distribution", {}))

                common_topics = report.get("Most Common Topics", [])
                for topic, count in common_topics:
                    st.write(f"- **{topic}**: {count} times")

                st.subheader("Hindi TTS Audio Summary")
                tts_response = requests.get(f"{BASE_URL}/generate_tts", params={"company": company}, stream=True)

                if tts_response.ok:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
                        temp_audio.write(tts_response.content)
                        temp_audio_path = temp_audio.name
                    st.audio(temp_audio_path, format="audio/mp3")
                else:
                    st.error(f"Failed to fetch TTS audio. Status Code: {tts_response.status_code}")
            else:
                st.error("No news articles found.")
        else:
            st.error("Failed to fetch news.")
    else:
        st.warning("Please enter a company name.")

app = FastAPI()

@app.get("/fetch_news", response_model=dict)
def fetch_news(company: str = Query(..., description="Enter the company name")):
    news = fetch_news_api(company)

    if not news or (isinstance(news, dict) and "error" in news):
        raise HTTPException(status_code=404, detail=f"No news articles found for '{company}'.")

    news = analyze_sentiment(news)
    news = extract_topics(news)

    save_to_json(news, "news_data.json")
    report = generate_report(news)
    save_to_json(report, "report.json")

    return JSONResponse(status_code=200, content={"news": news, "report": report})

@app.get("/analyze_sentiment", response_model=dict)
def sentiment_analysis(company: str = Query(..., description="Enter the company name")):
    news = fetch_news_api(company)

    if not news or (isinstance(news, dict) and "error" in news):
        raise HTTPException(status_code=404, detail=f"No news articles found for '{company}'.")

    news = analyze_sentiment(news)
    save_to_json(news, "sentiment_data.json")

    return JSONResponse(status_code=200, content={"sentiment_analysis": news})

@app.get("/generate_tts")
def generate_tts(company: str = Query(..., description="Enter the company name")):
    news = fetch_news_api(company)

    if not news or (isinstance(news, dict) and "error" in news):
        raise HTTPException(status_code=404, detail=f"No news articles found for '{company}'.")

    news_summaries = [
        f"समाचार {i+1}: {clean_hindi_text(article['summary'])}"
        for i, article in enumerate(news) if article.get("summary")
    ]

    full_text = "\n\n".join(news_summaries).strip()

    if not full_text:
        raise HTTPException(status_code=400, detail=f"No valid text for TTS conversion for '{company}'.")

    output_file = "news_summary.mp3"
    generated_file = text_to_speech(full_text, output_file, lang="hi")

    if not generated_file or not os.path.exists(output_file):
        raise HTTPException(status_code=500, detail="Audio file generation failed.")

    return FileResponse(output_file, media_type="audio/mpeg", filename="news_summary.mp3")
