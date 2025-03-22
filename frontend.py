import streamlit as st
import requests
import tempfile

BASE_URL = "http://127.0.0.1:8000"

st.title("📰 Hindi News Summarizer with TTS 🎤")

# ✅ Wrap input inside `st.form`
with st.form("news_form"):
    company = st.text_input("Enter company name", "")
    submitted = st.form_submit_button("Fetch News")  # ✅ Pressing Enter now triggers this

if submitted:  # ✅ This triggers when Enter is pressed or button is clicked
    if company:
        response = requests.get(f"{BASE_URL}/fetch_news", params={"company": company})

        if response.status_code == 200:
            data = response.json()
            news_articles = data.get("articles", [])  # ✅ FIXED: Use correct key
            report = data.get("report", {})

            if news_articles:
                st.subheader("📢 Latest News in English")
                for article in news_articles:
                    st.write(f"### {article['title']}")
                    st.write(f"📅 {article['published_date']} | 🏢 {article['source']}")
                    st.write(f"**Summary:** {article['summary']}")
                    st.write(f"🔹 Sentiment: {article.get('sentiment', 'Unknown')}")  # ✅ Prevents KeyError
                    st.write(f"🔍 Topics: {', '.join(article.get('topics', [])) if article.get('topics') else 'N/A'}")
                    st.markdown(f"[Read More]({article['link']})", unsafe_allow_html=True)
                    st.write("---")

                st.subheader("📊 Sentiment & Topics Report")
                st.write("### Sentiment Distribution")
                st.json(report.get("Sentiment Distribution", {}))

                st.write("### Common Topics")
                common_topics = report.get("Most Common Topics", [])
                for topic, count in common_topics:
                    st.write(f"- **{topic}**: {count} times")

                st.subheader("🎤 Hindi TTS Audio Summary")

                # 🔹 Fetch the audio file and store it temporarily
                tts_response = requests.get(f"{BASE_URL}/generate_tts", params={"company": company}, stream=True)

                if tts_response.ok:  # ✅ FIXED: Handle response correctly
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
                        temp_audio.write(tts_response.content)  # ✅ FIXED: Write full content at once
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
