from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from api import fetch_news_api, analyze_sentiment, extract_topics
from utils import save_to_json, generate_report, text_to_speech, clean_hindi_text
import os

app = FastAPI()

@app.get("/fetch_news", response_model=dict)
def fetch_news(company: str = Query(..., description="Enter the company name")):
    """
    Fetches news articles for a given company, performs sentiment analysis, and extracts topics.
    Returns structured news data and a report.
    """
    news = fetch_news_api(company)

    if not news or (isinstance(news, dict) and "error" in news):
        raise HTTPException(status_code=404, detail=f"No news articles found for '{company}'.")

    # Process news (sentiment + topic extraction)
    news = analyze_sentiment(news)
    news = extract_topics(news)

    # Save data & generate report
    save_to_json(news, "news_data.json")
    report = generate_report(news)
    save_to_json(report, "report.json")

    return JSONResponse(status_code=200, content={"news": news, "report": report})


@app.get("/analyze_sentiment", response_model=dict)
def sentiment_analysis(company: str = Query(..., description="Enter the company name")):
    """
    Fetches news and analyzes sentiment without extracting topics.
    """
    news = fetch_news_api(company)

    if not news or (isinstance(news, dict) and "error" in news):
        raise HTTPException(status_code=404, detail=f"No news articles found for '{company}'.")

    news = analyze_sentiment(news)
    save_to_json(news, "sentiment_data.json")

    return JSONResponse(status_code=200, content={"sentiment_analysis": news})


@app.get("/generate_tts")
def generate_tts(company: str = Query(..., description="Enter the company name")):
    """
    Fetches news, generates text-to-speech (TTS) audio, and provides a downloadable link.
    """
    news = fetch_news_api(company)

    if not news or (isinstance(news, dict) and "error" in news):
        raise HTTPException(status_code=404, detail=f"No news articles found for '{company}'.")

    # Generate Hindi TTS text from valid summaries
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
        raise HTTPException(status_code=500, detail="Audio file generation failed due to an unknown error.")

    return FileResponse(output_file, media_type="audio/mpeg", filename="news_summary.mp3")
