import streamlit as st
import random
import json
import re
from modules.db_handler import save_reading, get_reading_history, delete_reading
from modules.ai_handler import configure_ai

class ReadingAI:
    @staticmethod
    def generate_content(topic):
        """Gọi Gemini AI để tạo bài đọc và câu hỏi dựa trên Topic được chọn"""
        from modules.data_store import all_cards
        
        # Lấy các từ vựng thuộc chủ đề này để gợi ý cho AI
        topic_words = [w['word'] for w in all_cards if w['topic'].lower() == topic.lower()]
        seeds = ", ".join(random.sample(topic_words, min(len(topic_words), 8)))
        
        model = configure_ai()
        if not model: return None
        
        prompt = f"""
        You are an IELTS Reading Specialist. 
        TASK: Write an IELTS-style Academic Reading passage (approx 350-400 words) about the topic: "{topic.upper()}".
        TARGET VOCABULARY: Try to naturally incorporate some of these terms: {seeds}.
        
        STRUCTURE:
        - Title: Catchy Academic Title.
        - Content: 3-4 paragraphs of high-level academic English.
        - Questions: 5 multiple-choice questions (A, B, C, D) covering:
            1. Main Idea (Gist)
            2. Specific Detail
            3. Vocabulary in Context
            4. Inference (What can be inferred...)
            5. Author's Purpose or Attitude
            
        OUTPUT: Return ONLY a valid JSON object (no Markdown blocks):
        {{
          "title": "Title here",
          "topic": "{topic}",
          "passage_id": {random.randint(100, 999)},
          "content": "Paragraph 1...\\n\\nParagraph 2...",
          "questions": [
            {{"type": "Main Idea", "q": "...", "options": ["A", "B", "C", "D"], "ans": "Correct Option Text"}},
            ...
          ]
        }}
        """
        try:
            response = model.generate_content(prompt)
            clean_text = re.sub(r'```json|```', '', response.text).strip()
            return json.loads(clean_text)
        except Exception as e:
            st.error(f"Lỗi AI: {e}")
            return None

    @staticmethod
    def render_ui():
        st.markdown("""
        <style>
            .reading-container {
                background: rgba(0, 0, 0, 0.4);
                padding: 30px;
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(20px);
                margin-bottom: 20px;
            }
            .question-box {
                background: rgba(255, 255, 255, 0.03);
                padding: 20px;
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.05);
                margin-bottom: 15px;
            }
            h1, h2, h3, h5, p, span, small, b { color: #F1F5F9 !important; }
            .stButton>button {
                background: linear-gradient(135deg, #3B82F6, #2563EB) !important;
                color: white !important;
                border: none !important;
                border-radius: 12px !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("<h1 style='text-align: center;'>📖 IELTS Reading Simulator</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94A3B8 !important;'>Thực chiến bài đọc theo chủ đề IELTS cùng Lexi AI.</p>", unsafe_allow_html=True)
        
        # Kiểm tra điều kiện mở khóa
        word_bank = st.session_state.get('word_bank', [])
        word_count = len(word_bank)
        if word_count < 5:
            st.warning(f"🔒 Cần ít nhất 5 từ trong Sổ tay để mở khóa Reading. Hiện có: {word_count}")
            return

        # TOPIC SELECTION
        topics = {
            "🌍 Environment": "environment",
            "💻 Technology": "technology",
            "🎓 Education": "education",
            "🏥 Health": "health",
            "💼 Work": "work",
            "✈️ Travel": "travel",
            "🍎 Food": "food",
            "🎨 Art": "art",
            "🏀 Sports": "sports",
            "📢 Media": "media"
        }
        
        col_topic, col_gen = st.columns([2, 1])
        with col_topic:
            selected_label = st.selectbox("Chọn chủ đề thử thách:", list(topics.keys()))
            selected_topic = topics[selected_label]
            
        with col_gen:
            st.write(""); st.write("") 
            if st.button("✨ Sáng tác bài đọc mới", use_container_width=True):
                with st.spinner(f"Lexi đang soạn bài đọc về {selected_label}..."):
                    st.session_state.current_reading = ReadingAI.generate_content(selected_topic)
                    st.session_state.answers_state = {}

        # DISPLAY CONTENT
        if "current_reading" in st.session_state and st.session_state.current_reading:
            data = st.session_state.current_reading
            st.divider()
            
            # Save Feature
            col_save, col_info = st.columns([1, 2])
            with col_save:
                if st.button("💾 Lưu bài đọc này", use_container_width=True):
                    if save_reading(data):
                        st.success("Đã ghi vào bộ sưu tập!")
                    else:
                        st.error("Lỗi khi lưu bài đọc.")
            with col_info:
                st.info("Bài đọc đã lưu có thể xem lại ở phần Thư viện phía dưới.")
            
            col_left, col_right = st.columns([1.2, 1])
            with col_left:
                st.markdown(f"### 📄 {data.get('topic', 'Reading').upper()} Passage")
                st.markdown(f"""
                <div class="reading-container" style="height: 600px; overflow-y: auto;">
                    <h2 style="color: #3B82F6 !important; margin-top:0;">{data['title']}</h2>
                    <p style="font-size: 17px; line-height: 1.8; color: #E2E8F0 !important; text-align: justify;">
                        {data['content'].replace('\\n', '<br>').replace('\n', '<br>')} 
                    </p>
                </div>
                """, unsafe_allow_html=True)

            with col_right:
                st.markdown("### 🎯 Comprehension Quiz")
                for i, item in enumerate(data['questions']):
                    with st.container():
                        st.markdown(f"""
                        <div class="question-box">
                            <b style='color: #3B82F6;'>Question {i+1}</b> <small style='color:#64748B;'>[{item['type']}]</small><br>
                            {item['q']}
                        </div>
                        """, unsafe_allow_html=True)
                        user_choice = st.radio("Chọn đáp án đúng:", item['options'], key=f"rd_q_{i}", label_visibility="collapsed")
                        
                        btn_col, res_col = st.columns([1, 2])
                        if btn_col.button(f"Nộp bài Q{i+1}", key=f"rd_btn_{i}"):
                            if user_choice == item['ans']:
                                st.session_state.answers_state[f"q{i}"] = "correct"
                                if f"scored_q{i}" not in st.session_state:
                                    st.session_state.xp += 10
                                    st.session_state[f"scored_q{i}"] = True
                            else:
                                st.session_state.answers_state[f"q{i}"] = "wrong"
                        
                        if f"q{i}" in st.session_state.answers_state:
                            if st.session_state.answers_state[f"q{i}"] == "correct":
                                st.success("✅ Tuyệt vời! +10 XP")
                            else:
                                st.error(f"❌ Chưa chính xác. Lời giải đúng: {item['ans']}")
                        st.write("") 

        # 📚 HISTORY SECTION
        st.divider()
        st.markdown("<h2 style='text-align: center;'>📚 Thư viện bài đọc của bạn</h2>", unsafe_allow_html=True)
        history = get_reading_history()
        
        if not history:
            st.info("Chưa có bài đọc nào được lưu. Hãy luyện tập và lưu lại để ôn tập nhé!")
        else:
            for item in history:
                with st.expander(f"📖 {item['title']} - [{item['topic'].upper()}] ({item['date_saved']})"):
                    h_col1, h_col2 = st.columns([1.2, 1])
                    with h_col1:
                        st.markdown(f"""
                        <div class="reading-container" style="max-height: 400px; overflow-y: auto;">
                            <h3 style='color:#3B82F6;'>{item['title']}</h3>
                            {item['content'].replace('\\n', '<br>').replace('\n', '<br>')}
                        </div>
                        """, unsafe_allow_html=True)
                    with h_col2:
                        st.write("#### Câu hỏi ôn tập:")
                        for i, q in enumerate(item['questions']):
                            st.markdown(f"**Q{i+1}:** {q['q']}")
                            st.write(f"*Đáp án:* {q['ans']}")
                        
                        st.divider()
                        if st.button("🗑 Xóa bài này", key=f"del_h_{item['id']}", use_container_width=True):
                            delete_reading(item['id'])
                            st.rerun()