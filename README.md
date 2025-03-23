---
title: "Hindi News Summarizer with TTS"
emoji: "📰"
colorFrom: "blue"
colorTo: "red"
sdk: "streamlit"
sdk_version: "1.32.0"
app_file: "app.py"
pinned: false
---
 Project Overview
This web-based application allows users to:
- Fetch news related to a company from NewsAPI
- Perform sentiment analysis (Positive, Negative, Neutral)
- Extract key topics from the articles
- Generate a Hindi Text-to-Speech (TTS) summary
- Provide a comparative sentiment report

The application is built using FastAPI for the backend and Streamlit for the frontend, with APIs enabling communication between them.

-------------------------------------------------------------------------------------------------------------------------------------
1. Project Setup
A. Clone the Repository

Run the following command:
git clone https://github.com/Arnav4664/news-summarizer 
cd news-summarizer

B. Install Dependencies 
Ensure Python 3.10+ is installed. Then run:
pip install -r requirements.txt

C. Download Required Models  
Run the following commands to download NLP models:
python -m spacy download en_core_web_sm

---------------------------------------------------------------------------------------------------------------------------

2. Running the Application
A. Start the Backend (FastAPI)  
Run this command in the terminal:
uvicorn api:app --host 0.0.0.0 --port 8000

Once it starts, open http://127.0.0.1:8000/docs to test the API.

B. Start the Frontend (Streamlit)  
Open a new terminal and run:
streamlit run app.py

The app will open in your browser at http://localhost:8501.

---------------------------------------------------------------------------------------------------------------------------

3. API Usage
A. Fetch News  
Endpoint:
GET /fetch_news?company=<company_name>

Example Request:
http://127.0.0.1:8000/fetch_news?company=Tesla

Response Format:

{
  "company": "Tesla",
  "articles": [
    {
      "title": "Tesla's New Model Breaks Sales Records",
      "summary": "Tesla's latest EV sees record sales in Q3...",
      "sentiment": "Positive",
      "topics": ["Electric Vehicles", "Stock Market", "Innovation"]
    }
  ],
  "report": {
    "Sentiment Distribution": {"Positive": 1, "Negative": 0, "Neutral": 0},
    "Most Common Topics": [["Electric Vehicles", 1]]
  }
}
B. Generate Hindi TTS
Endpoint:
GET /generate_tts?company=<company_name>
Example Request:

http://127.0.0.1:8000/generate_tts?company=Tesla
This returns an MP3 file with a Hindi voice summary.

---------------------------------------------------------------------------------------------------------------------------

4. Model Details 
A. Summarization
The application fetches news articles using NewsAPI.
It extracts relevant information (title, summary, topics) using BeautifulSoup.

B. Sentiment Analysis
Uses NLTK’s VADER for sentiment classification.
Uses TextBlob for additional polarity scoring.
The sentiment is classified as Positive, Negative, or Neutral.

C. Text-to-Speech (TTS)
Translates summaries to Hindi using Deep Translator.
Converts translated text to audio (MP3) using gTTS (Google TTS).

Deployment- Deploying on Hugging Face Spaces

The deployed app will be available at:
https://huggingface.co/spaces/Arnav4664/news-tts

---------------------------------------------------------------------------------------------------------------------------

5. Assumptions & Limitations

-The application works best with English-language news.
-NewsAPI has a limited free-tier quota (100 requests/day).
-The Deep Translator API may not be 100% accurate for Hindi translation.
-TTS quality depends on Google Text-to-Speech (gTTS).

---------------------------------------------------------------------------------------------------------------------------

6. Folder Structure

/news-summarizer/
│── api.py            # Backend FastAPI server
│── app.py            # Streamlit frontend
│── utils.py          # Helper functions (TTS, JSON handling, etc.)
│── requirements.txt  # Dependencies
│── README.md         # Documentation
│── news_data.json    # Saved fetched news data
│── report.json       # Sentiment & topic report

---------------------------------------------------------------------------------------------------------------------------

7. Technologies Used

Component       | Technology
--------------- | ------------------
Backend API     | FastAPI
Frontend UI     | Streamlit
Data Processing | BeautifulSoup, NLTK, TextBlob
Text-to-Speech  | Google TTS (gTTS)
Translation     | Deep Translator
Deployment      | Hugging Face Spaces

---------------------------------------------------------------------------------------------------------------------------

8. Contribution Guidelines

Fork the repo.

Open a pull request with proper comments and documentation.

Ensure your code follows PEP8 guidelines.

License This project is licensed under the MIT License.

---------------------------------------------------------------------------------------------------------------------------

9. Contact For any queries, feel free to reach out:
Email: arnavbankar17@gmail.com
GitHub: github.com/Arnav4664

