import google.generativeai as genai
import streamlit as st
import json
import re
import time
from gtts import gTTS
import io

def configure_ai():
    try:
        api_key = st.secrets["GENAI_API_KEY"]
        genai.configure(api_key=api_key)
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for m in models:
            if 'gemini-1.5-flash' in m:
                return genai.GenerativeModel(m)
        return genai.GenerativeModel(models[0]) if models else None
    except:
        return None

def extract_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            return None
    return None

def get_word_info(word):
    model = configure_ai()
    if not model: return {"error": "Lỗi cấu hình AI (API Key chưa đúng)"}

    prompt = f"""
    You are an IELTS Band 9 Expert. Analyze the word: "{word}".
    Return ONLY JSON with this format:
    {{
     "phonetic": "ipa",
     "word_class": "noun/verb...",
     "definition_en": "concise english definition",
     "definition_vi": "nghĩa tiếng Việt ngắn gọn",
     "examples": [
        {{"en": "sentence 1", "vi": "dịch 1"}},
        {{"en": "sentence 2", "vi": "dịch 2"}}
     ],
     "word_family": [
        {{"word": "related_word", "class": "verb/noun...", "meaning": "nghĩa"}}
     ],
     "synonyms": ["word1", "word2"],
     "antonyms": ["word1", "word2"],
     "collocations": ["verb + word", "word + noun"],
     "nuance": "giải thích chi tiết sắc thái và cách dùng từ này trong IELTS bằng tiếng Việt"
    }}
    Return NO text other than JSON.
    """
    
    for _ in range(2):
        try:
            res = model.generate_content(prompt)
            data = extract_json(res.text)
            if data: return data
        except Exception:
            time.sleep(1)
    return {"error": "Lexi đang bận một chút, em nhấn tìm lại lần nữa nhé!"}

def speak(text, slow=False):
    tts = gTTS(text=text, lang='en', slow=slow)
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    st.audio(fp, format='audio/mp3', autoplay=True)

def get_speaking_feedback(topic, user_content, is_audio=False):
    model = configure_ai()
    if not model: return "Lỗi cấu hình AI!"
    
    if is_audio:
        # UserContent is bytes (audio/wav or similar from st.audio_input)
        prompt = [
            f"Role: IELTS Speaking Examiner.\nTopic: {topic}\nTask: Analyze this spoken response for Pronunciation, Fluency, Vocabulary, and Grammar. Estimate Band Score (0-9). Provide a Band 8.0+ sample response and 5 new vocabulary words. Response in Vietnamese.",
            {"mime_type": "audio/wav", "data": user_content}
        ]
    else:
        # UserContent is text
        prompt = f"""
        Role: IELTS Speaking Examiner.
        Topic: {topic}
        User Response (Text): {user_content}
        
        Task:
        1. Estimated Band Score (0-9).
        2. Feedback on Fluency, Vocabulary, Grammar, and Pronunciation (based on text).
        3. A Band 8.0+ sample response.
        4. List of 5 high-level vocabulary words related to this topic with Vietnamese meanings.
        
        Response in Vietnamese.
        """
    
    try:
        res = model.generate_content(prompt)
        return res.text
    except Exception as e:
        return f"Lỗi phân tích: {str(e)}"
