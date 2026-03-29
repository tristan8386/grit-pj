import streamlit as st
import random
import json
import re
import time
from modules.db_handler import save_reading, get_reading_history, delete_reading
from modules.ai_handler import configure_ai


class ReadingAI:
    @staticmethod
    def generate_content(topic):
        """Tạo bài đọc IELTS bằng AI theo chuẩn prompt"""
        from modules.data_store import all_cards     
        topic_words = [w['word'] for w in all_cards if w['topic'].lower() == topic.lower()]
        seeds = ", ".join(random.sample(topic_words, min(len(topic_words), 8))) if topic_words else ""

        model = configure_ai()
        if not model:
            st.error("Không thể kết nối AI. Vui lòng kiểm tra cấu hình.")
            return None

        prompt = f"""
You are a Cambridge IELTS Senior Examiner with 20+ years experience.

Create a full IELTS Academic Reading test on the topic: "{topic.upper()}".

**Passage Requirements:**
- 750-900 words
- 6-8 paragraphs labeled clearly as Paragraph A, B, C, D, E, F, G, H...
- Formal academic tone, Band 8.5+ vocabulary
- Naturally use some of these words: {seeds}

**Questions (exactly 13):**
1-5: Matching Headings (provide 7-8 headings) (Paragraph A-G for each of them on the question box)
6-9: True / False / Not Given (these questions should be tricky, for students to really think and analyze the passage carefully)
10-13: Summary Completion (NO MORE THAN TWO WORDS from the passage)

**Output ONLY valid JSON:**
{{
  "title": "Academic title here",
  "topic": "{topic}",
  "passage_id": {random.randint(1000, 9999)},
  "content": "Full passage text with Paragraph A:\\nParagraph B: ...",
  "questions": [
    {{
      "number": 1,
      "type": "Matching Headings",
      "q": "question text",
      "options": ["i. Heading...", "ii. Heading..."],
      "ans": "vi",
      "location": "Paragraph C"
    }},
    ... 
    {{
      "number": 10,
      "type": "Summary Completion",
      "summary": "The summary paragraph with gaps like ___ .",
      "gaps": ["placeholder1", "placeholder2", "placeholder3", "placeholder4"],
      "ans": ["word1", "word2", "word3", "word4"]
    }}
  ]
}}
Make "Not Given" answers logically correct according to official IELTS standards.
"""

        try:
            response = model.generate_content(prompt)
            clean_text = re.sub(r'```(?:json)?\s*|\s*```', '', response.text).strip()
            data = json.loads(clean_text)
            return data
        except json.JSONDecodeError:
            st.error("AI trả về định dạng không hợp lệ. Vui lòng thử tạo lại.")
            return None
        except Exception as e:
            st.error(f"Lỗi khi tạo bài đọc: {e}")
            return None

    @staticmethod
    def render_ui():
        # CSS
        st.markdown("""
        <style>
            .reading-container {
                background: rgba(0, 0, 0, 0.45);
                padding: 30px;
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,0.1);
                backdrop-filter: blur(20px);
                margin-bottom: 20px;
            }
            .question-box {
                background: rgba(255,255,255,0.04);
                padding: 22px;
                border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.06);
                margin-bottom: 18px;
            }
            .summary-box {
                background: rgba(59, 130, 246, 0.1);
                padding: 25px;
                border-radius: 18px;
                border: 2px dashed #3B82F6;
                font-style: italic;
                line-height: 1.85;
                margin: 15px 0;
            }
            .timer-box {
                background: rgba(0,0,0,0.7);
                padding: 15px;
                border-radius: 12px;
                text-align: center;
                font-size: 1.55rem;
                font-weight: bold;
                margin: 15px 0;
            }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("<h1 style='text-align: center;'>📖 IELTS Reading Simulator</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94A3B8;'>Thực chiến bài đọc IELTS cùng Lexi AI</p>", unsafe_allow_html=True)

        # Kiểm tra word bank
        if len(st.session_state.get('word_bank', [])) < 5:
            st.warning(f"🔒 Cần ít nhất 5 từ trong Sổ tay để mở khóa. Hiện có: {len(st.session_state.get('word_bank', []))}")
            return

        # Chọn chủ đề & thời gian
        topics = {
            "🌍 Environment": "environment", "💻 Technology": "technology",
            "🎓 Education": "education", "🏥 Health": "health",
            "💼 Work": "work", "✈️ Travel": "travel",
            "🍎 Food": "food", "🎨 Art": "art",
            "🏀 Sports": "sports", "📢 Media": "media"
        }

        col1, col2, col3 = st.columns([3, 1.2, 1.2])
        with col1:
            selected_label = st.selectbox("Chọn chủ đề:", list(topics.keys()))
            selected_topic = topics[selected_label]

        with col2:
            time_options = [20, 30, 40, 60]
            selected_minutes = st.selectbox("⏱ Thời gian làm bài (phút):", time_options, index=2)

        with col3:
            if st.button("✨ Tạo bài đọc mới", use_container_width=True):
                with st.spinner(f"Đang tạo bài đọc về {selected_label}..."):
                    generated = ReadingAI.generate_content(selected_topic)
                    if generated:
                        st.session_state.current_reading = generated
                        st.session_state.answers_state = {}
                        st.session_state.scored_questions = set()
                        st.session_state.timer_start = time.time()
                        st.session_state.time_limit = selected_minutes * 60
                        st.session_state.timer_active = True
                        st.rerun()

        # Hiển thị bài nếu đã tạo
        if "current_reading" in st.session_state and st.session_state.current_reading:
            data = st.session_state.current_reading

            # Timer
            if st.session_state.get("timer_active", False):
                elapsed = time.time() - st.session_state.get("timer_start", time.time())
                remaining = max(0, st.session_state.get("time_limit", 2400) - elapsed)
                mins, secs = divmod(int(remaining), 60)
                color = "#EF4444" if remaining < 300 else "#FBBF24"
                
                st.markdown(f"""
                <div class="timer-box" style="color:{color};">
                    ⏳ {mins:02d}:{secs:02d}
                </div>
                """, unsafe_allow_html=True)

                if remaining <= 0:
                    st.error("⏰ Hết thời gian làm bài!")
                    st.session_state.timer_active = False

            st.divider()

            # Nút lưu bài
            if st.button("💾 Lưu bài đọc này", use_container_width=True):
                correct_count = sum(1 for v in st.session_state.answers_state.values() if v == "correct")
                data["score"] = correct_count * 10
                data["correct_count"] = correct_count
                if save_reading(data):
                    st.success("✅ Đã lưu vào thư viện!")
                else:
                    st.error("Lỗi khi lưu bài.")

            # Layout Passage + Quiz
            left, right = st.columns([1.3, 1])

            with left:
                st.markdown(f"### 📄 {data.get('topic', '').upper()} PASSAGE")
                st.markdown(f"""
                <div class="reading-container" style="height: 650px; overflow-y: auto;">
                    <h2 style="color:#3B82F6;">{data.get('title', 'IELTS Academic Reading')}</h2>
                    <p style="font-size: 17px; line-height: 1.85; color:#E2E8F0; text-align: justify;">
                        {data.get('content', '').replace('\\n', '<br>')}
                    </p>
                </div>
                """, unsafe_allow_html=True)

            with right:
                st.markdown("### 🎯 13 Câu hỏi")

                correct_count = 0
                for item in data.get("questions", []):
                    q_num = item.get("number", 0)
                    q_type = item.get("type", "Question")

                    st.markdown(f"""
                    <div class="question-box">
                        <b style='color:#3B82F6;'>Question {q_num}</b> 
                        <small style='color:#64748B;'>[{q_type}]</small><br>
                        {item.get('q', '')}
                    </div>
                    """, unsafe_allow_html=True)

                    # Summary Completion - Giao diện đẹp
                    if q_type == "Summary Completion":
                        st.markdown(f"""
                        <div class="summary-box">
                            {item.get('summary', item.get('q', ''))}
                        </div>
                        """, unsafe_allow_html=True)

                        st.caption("Nhập **tối đa 2 từ** cho mỗi chỗ trống:")
                        gap_cols = st.columns(4)
                        user_answers = []
                        correct_ans = [str(a).strip().lower() for a in item.get("ans", [])]

                        for i in range(4):
                            with gap_cols[i]:
                                ans = st.text_input(
                                    label=f"Gap {i+1}",
                                    key=f"sum_gap_{q_num}_{i}",
                                    placeholder="...",
                                    label_visibility="collapsed"
                                )
                                user_answers.append(ans.strip().lower())

                        is_correct = (user_answers == correct_ans)

                    else:
                        # Các loại khác (Matching Headings, TFNG)
                        options = item.get("options", ["True", "False", "Not Given"])
                        user_choice = st.radio(
                            "Chọn đáp án:", 
                            options, 
                            key=f"rd_q_{q_num}",
                            label_visibility="collapsed"
                        )
                        correct_answer = str(item.get("ans", "")).strip().lower()
                        is_correct = str(user_choice).strip().lower() == correct_answer

                    # Nút nộp
                    if st.button(f"Nộp Question {q_num}", key=f"submit_{q_num}", use_container_width=True):
                        if is_correct:
                            st.session_state.answers_state[f"q{q_num}"] = "correct"
                            if f"scored_{q_num}" not in st.session_state:
                                st.session_state.xp = st.session_state.get("xp", 0) + 10
                                st.session_state[f"scored_{q_num}"] = True
                                st.success("✅ Chính xác! +10 XP")
                        else:
                            st.session_state.answers_state[f"q{q_num}"] = "wrong"
                            st.error(f"❌ Đáp án đúng: **{item.get('ans', '')}**")

                    # Hiển thị kết quả đã nộp
                    if f"q{q_num}" in st.session_state.answers_state:
                        if st.session_state.answers_state[f"q{q_num}"] == "correct":
                            st.success("✅ Chính xác")
                            correct_count += 1
                        else:
                            st.error(f"Đáp án: **{item.get('ans','')}**")

                    st.markdown("---")

                # Kết quả tổng
                total_q = len(data.get("questions", []))
                if total_q > 0:
                    percent = int((correct_count / total_q) * 100)
                    band_map = {0:0,1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:8.5,10:9,11:9,12:9,13:9}
                    estimated_band = band_map.get(correct_count, 0)

                    st.markdown("### 📊 Kết quả hiện tại")
                    st.progress(correct_count / total_q)
                    st.metric("Điểm", f"{correct_count * 10} XP", f"{correct_count}/{total_q} câu")
                    st.caption(f"Hoàn thành: **{percent}%** — Band ước tính: **{estimated_band}**")

        # Thư viện bài đọc (giữ nguyên logic cũ)
        st.divider()
        st.markdown("<h2 style='text-align: center;'>📚 Thư viện bài đọc của bạn</h2>", unsafe_allow_html=True)
        history = get_reading_history()

        if not history:
            st.info("Chưa có bài đọc nào. Hãy tạo và lưu bài để ôn tập.")
        else:
            for item in history:
                with st.expander(f"📖 {item.get('title', 'Untitled')} — [{item.get('topic','').upper()}]"):
                    col1, col2 = st.columns([1.3, 1])
                    with col1:
                        st.markdown(f"""
                        <div class="reading-container" style="max-height: 420px; overflow-y: auto;">
                            <h3 style="color:#3B82F6;">{item.get('title','')}</h3>
                            {item.get('content','').replace('\\n', '<br>')}
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.write("#### Đáp án:")
                        for q in item.get("questions", []):
                            st.write(f"**Q{q.get('number')}**: {q.get('ans','')}")
                        if "score" in item:
                            st.success(f"Điểm khi làm: **{item['score']} XP**")
                        
                        if st.button("🗑 Xóa bài này", key=f"del_{item.get('id')}"):
                            delete_reading(item.get('id'))
                            st.rerun()
