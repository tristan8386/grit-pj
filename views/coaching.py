import streamlit as st
from modules.ai_handler import configure_ai


class CoachingAI:

    @staticmethod
    def generate_response(user_prompt):
        """Gọi Gemini AI để tư vấn học tiếng Anh"""

        model = configure_ai()
        if not model:
            return None

        prompt = f"""
        You are Lexi AI — an English Learning Coach.

        Your role:
        Help learners understand English clearly and improve effectively.

        You can:
        • explain vocabulary
        • analyse grammar
        • compare similar words
        • explain daily English expressions
        • give study strategies

        RESPONSE STRUCTURE:

        If vocabulary question:

        Meaning
        Pronunciation
        Word Family
        Collocations
        Example Sentence

        If comparing words:

        Comparison Table
        Key Differences
        Example Sentences

        If grammar question:

        Structure
        Usage
        Examples
        Common mistakes

        If learning advice:

        Problem
        Reason
        Suggestion
        Daily Practice Plan

        USER QUESTION:
        {user_prompt}

        Respond clearly with bullet points.
        """

        try:
            response = model.generate_content(prompt)
            return response.text

        except Exception as e:
            st.error(f"AI Error: {e}")
            return None


    @staticmethod
    def render_ui():

        st.markdown("""
        <style>
        .coach-container{
            background: rgba(0,0,0,0.4);
            padding:25px;
            border-radius:20px;
            border:1px solid rgba(255,255,255,0.1);
            backdrop-filter:blur(20px);
            margin-bottom:20px;
        }

        .chat-user{
            background:linear-gradient(135deg,#3B82F6,#2563EB);
            padding:12px;
            border-radius:12px;
            margin-bottom:10px;
            color:white;
        }

        .chat-ai{
            background:rgba(255,255,255,0.05);
            padding:12px;
            border-radius:12px;
            margin-bottom:15px;
        }

        h1,h2,h3,p{
            color:#F1F5F9 !important;
        }

        </style>
        """, unsafe_allow_html=True)

        st.markdown("<h1 style='text-align:center;'>🧠 Lexi AI Coach</h1>", unsafe_allow_html=True)

        st.markdown(
            "<p style='text-align:center;color:#94A3B8;'>Hỏi bất cứ điều gì về tiếng Anh: từ vựng, ngữ pháp, cách học.</p>",
            unsafe_allow_html=True
        )

        if "coach_chat" not in st.session_state:
            st.session_state.coach_chat = []

        # QUICK PROMPTS
        st.markdown("### 🚀 Gợi ý nhanh")

        col1, col2, col3 = st.columns(3)

        if col1.button("📚 How to remember vocabulary"):
            user_prompt = "How can I remember English vocabulary effectively?"
            st.session_state.coach_chat.append(("user", user_prompt))

        if col2.button("🗣 Improve speaking"):
            user_prompt = "How can I improve my English speaking?"
            st.session_state.coach_chat.append(("user", user_prompt))

        if col3.button("⚖️ Word difference"):
            user_prompt = "What is the difference between building, castle and palace?"
            st.session_state.coach_chat.append(("user", user_prompt))

        st.divider()

        user_input = st.chat_input("Ask Lexi AI Coach...")

        if user_input:
            st.session_state.coach_chat.append(("user", user_input))

        # GENERATE AI RESPONSE
        if st.session_state.coach_chat and st.session_state.coach_chat[-1][0] == "user":

            last_prompt = st.session_state.coach_chat[-1][1]

            with st.spinner("Lexi AI is thinking..."):
                ai_response = CoachingAI.generate_response(last_prompt)

            if ai_response:
                st.session_state.coach_chat.append(("ai", ai_response))

        # DISPLAY CHAT
        st.markdown('<div class="coach-container">', unsafe_allow_html=True)

        for role, msg in st.session_state.coach_chat:

            if role == "user":
                st.markdown(f'<div class="chat-user">👤 {msg}</div>', unsafe_allow_html=True)

            else:
                st.markdown(f'<div class="chat-ai">🤖 {msg}</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)