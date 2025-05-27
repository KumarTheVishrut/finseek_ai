# app.py
import streamlit as st
import requests

st.title("🤑 Multi-Agent Finance Assistant")
st.caption("Ask me about Asia tech – I speak too!")

# 1. Record or upload audio
audio_file = st.file_uploader("Record your question", type=["wav","mp3"])
if audio_file:
    # 2. STT
    st.info("Transcribing...")
    st.spinner()
    st.write("Transcript:")
    r = requests.post("http://lang-agent:8003/stt", files={"audio": audio_file})
    text = r.json()["transcript"]
    st.write(text)

    # 3. Orchestrate retrieval + LLM
    st.info("Analyzing...")
    # get market & surprise data
    mr = requests.get(f"http://api-agent:8000/risk-exposure?ticker_list=2330.TW,005930.KS")
    sr = requests.get("http://scraper-agent:8001/earnings-surprises?symbol=2330")
    prompt = (
        f"Today, Asia tech allocation is {mr.json()['allocation_pct']}% of AUM. "
        f"TSMC surprise {sr.json()['surprise_pct']}%. "
        f"User asked: {text}"
    )
    llm = requests.post("http://lang-agent:8003/generate", json={"prompt": prompt})
    answer = llm.json()["text"]
    st.write("🗣️ Response:")
    st.write(answer)

    # 4. TTS
    tt = requests.post("http://lang-agent:8003/tts", json={"text": answer})
    st.audio(tt.json()["audio_file"])
