import streamlit as st
from modules.ai_handler import configure_ai
import random

class SpeakingAI:
    @staticmethod
    def render_ui():
        st.markdown("""
        <style>
            .stApp {
                background: radial-gradient(circle at top left, #0F172A, #1E293B);
                color: #F8FAFC;
            }
            h1, h2, h3, h5, p, span, small, b { color: #F1F5F9 !important; }
            .stTextArea textarea {
                background-color: rgba(255, 255, 255, 0.05) !important;
                color: white !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
            }
            .stButton>button {
                background: linear-gradient(135deg, #3B82F6, #2563EB) !important;
                color: white !important;
                border: none !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        st.title("🎙️ IELTS Speaking Coach")
        st.caption("Luyện nói cùng AI theo tiêu chuẩn IELTS.")

        if "speaking_topic" not in st.session_state:
            st.session_state.speaking_topic = None
        if "speaking_feedback" not in st.session_state:
            st.session_state.speaking_feedback = None

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### 🎯 Chọn chủ đề luyện nói")
            topics = [
                ("🌍 Environment", "environment"),
                ("💻 Technology", "technology"),
                ("🎓 Education", "education"),
                ("🏥 Health", "health"),
                ("💼 Work & Business", "work"),
                ("✈️ Travel", "travel"),
                ("🍎 Food & Nutrition", "food"),
                ("🎨 Art & Culture", "art"),
                ("🏀 Sports & Hobbies", "sports"),
                ("📢 Media & Comms", "media")
            ]
            
            selected_topic_label = st.selectbox("IELTS Speaking Topics:", [t[0] for t in topics], label_visibility="collapsed")
            selected_topic_id = next(t[1] for t in topics if t[0] == selected_topic_label)

            if st.button("🆕 Lấy đề bài mới", use_container_width=True):
                model = configure_ai()
                if not model:
                    st.error("Lỗi cấu hình AI!")
                    return
                # Randomized prompt generation based on selected topic
                prompt = f"""
                Bạn là giám khảo IELTS. Hãy tạo 1 đề bài Speaking Part 2 (Cue Card) độc nhất vô nhị về chủ đề: {selected_topic_label}.
                
                YÊU CẦU:
                - Đề bài phải cụ thể, không trùng lặp các đề quan thuộc.
                - Bao gồm: Đề bài chính (Describe...) và ít nhất 4 gợi ý (You should say...).
                - Ngôn ngữ: Chỉ dùng TIẾNG ANH.
                - Định dạng: Rõ ràng, dễ đọc.
                """
                with st.spinner("Lexi đang soạn đề bài cho bạn..."):
                    st.session_state.speaking_topic = model.generate_content(prompt).text
                st.session_state.speaking_feedback = None
                st.rerun()

            if st.session_state.speaking_topic:
                st.markdown(f"""
                <div style="background: rgba(59, 130, 246, 0.1); padding: 20px; border-radius: 15px; border-left: 5px solid #3B82F6; margin-top: 15px;">
                    <div style="color: #93C5FD; font-weight: bold; margin-bottom: 10px;">📋 ĐỀ BÀI CỦA BẠN:</div>
                    <div style="color: #F8FAFC; line-height: 1.6;">{st.session_state.speaking_topic}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Hãy chọn một chủ đề và nhấn nút để nhận thử thách nhé!")

        with col2:
            tab_text, tab_voice = st.tabs(["✍️ Bản nháp (Text)", "🎙️ Ghi âm (Voice)"])
            
            with tab_text:
                user_speech_text = st.text_area("Nhập nội dung bạn định nói:", height=200, placeholder="Ví dụ: Today I would like to talk about...", key="speaking_text_area")
                if st.button("🚀 Chấm điểm (Text)", use_container_width=True):
                    if not user_speech_text:
                        st.warning("Vui lòng nhập nội dung!")
                    else:
                        with st.spinner("Lexi AI đang phân tích bài nói của bạn..."):
                            from modules.ai_handler import get_speaking_feedback
                            st.session_state.speaking_feedback = get_speaking_feedback(st.session_state.speaking_topic, user_speech_text)
            
            with tab_voice:
                st.write("Nhấn nút micro bên dưới để bắt đầu ghi âm bài nói của bạn:")
                audio_file = st.audio_input("Bạn đang nghe?")
                if audio_file:
                    if st.button("🚀 Chấm điểm (Voice)", use_container_width=True):
                        with st.spinner("Lexi AI đang nghe và phân tích giọng nói của bạn..."):
                            from modules.ai_handler import get_speaking_feedback
                            audio_bytes = audio_file.read()
                            st.session_state.speaking_feedback = get_speaking_feedback(st.session_state.speaking_topic, audio_bytes, is_audio=True)

        if st.session_state.speaking_feedback:
            st.divider()
            st.markdown("### 📊 Kết quả phân tích từ AI")
            st.markdown(st.session_state.speaking_feedback)
