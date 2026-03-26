import streamlit as st
import random
import base64
from modules.db_handler import insert_all_cards, get_cards_by_topic, save_word, get_all_saved_words
from modules.ai_handler import get_word_info, speak
from views import speaking, notebook, reading, writing, coaching
from views.ui_components import load_css, render_sidebar_logo, render_header, render_word_card, render_flashcard

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def get_img_with_href(local_img_path):
    img_format = local_img_path.split('.')[-1]
    binary_data = get_base64_of_bin_file(local_img_path)
    html_code = f'data:image/{img_format};base64,{binary_data}'
    return html_code

# Define logo before sidebar use
logo_base64 = get_img_with_href("img/logo.png")

# ================= 1. CẤU HÌNH & DỮ LIỆU =================
st.set_page_config(page_title="Lexi AI - English Master", layout="wide")

if "db_initialized" not in st.session_state:
    insert_all_cards()
    st.session_state.db_initialized = True

if "word_bank" not in st.session_state: 
    st.session_state.word_bank = get_all_saved_words()
if "xp" not in st.session_state: st.session_state.xp = 0

# CSS Premium - Dark Theme
load_css("assets/style.css")

# ================= 2. SIDEBAR NAVIGATION =================
with st.sidebar:
    render_sidebar_logo(logo_base64)
    st.title("LEXI SKILLS")
    word_count = len(st.session_state.word_bank)
    st.progress(min(word_count/80, 1.0))
    st.caption(f"Tiến độ: {word_count}/80 từ")
    
    st.divider()
    page = st.radio("Chọn kỹ năng:", 
                    ["🔍 Học từ mới", "📚 Chủ đề", "🗣️ Speaking", "📒 Sổ tay", "🎓 Ôn tập", "📖 Reading", "✍️ Writing", "🤖 Coaching"])

# ================= 3. HEADER =================
render_header(logo_base64, st.session_state.xp)

# ================= 4. NỘI DUNG =================
if page == "🔍 Học từ mới":
    st.subheader("Tra cứu & Phân tích từ vựng AI")
    word_input = st.text_input("Nhập từ cần giải mã:", placeholder="Ví dụ: Sustainable...")
    if word_input:
        if "last_word" not in st.session_state or st.session_state.last_word != word_input:
            with st.spinner("Lexi đang phân tích chuyên sâu..."):
                st.session_state.word_data = get_word_info(word_input)
                st.session_state.last_word = word_input
                st.session_state.quiz_done = False

        data = st.session_state.word_data
        if "error" not in data:
            # Main Info
            render_word_card(word_input, data)
            
            # Action Buttons
            col_save, col_audio = st.columns([1, 1])
            if col_save.button("💾 Lưu vào Sổ tay"):
                if word_input not in [w['word'] for w in st.session_state.word_bank]:
                    word_to_save = {
                        "word": word_input,
                        "phonetic": data.get('phonetic'),
                        "definition_vi": data.get('definition_vi'),
                        "definition_en": data.get('definition_en'),
                        "word_class": data.get('word_class')
                    }
                    if save_word(word_to_save):
                        st.session_state.word_bank = get_all_saved_words()
                        st.balloons(); st.rerun()
            if col_audio.button("🔊 Nghe phát âm"):
                speak(word_input)

            # 1. Examples & 4. Collocations
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### 📝 Example Sentences")
                for ex in data.get('examples', []):
                    st.markdown(f"- **{ex['en']}**")
                    st.caption(ex['vi'])
            
            with c2:
                st.markdown("### 🔗 Collocations")
                for col in data.get('collocations', []):
                    st.markdown(f"- `{col}`")

            # 2. Word Family & 3. Synonyms/Antonyms
            st.divider()
            c3, c4 = st.columns(2)
            with c3:
                st.markdown("### 👨‍👩‍👧‍👦 Word Family")
                for item in data.get('word_family', []):
                    st.markdown(f"- **{item['word']}** ({item['class']}): {item['meaning']}")
            
            with c4:
                st.markdown("### 🔄 Synonyms & Antonyms")
                st.write("**Synonyms:** " + ", ".join(data.get('synonyms', [])))
                st.write("**Antonyms:** " + ", ".join(data.get('antonyms', [])))

            # 5. Quiz Section
            st.divider()
            st.markdown("### ⚡ Quick Quiz")
            st.info(f"Hãy chọn nghĩa đúng nhất cho từ **{word_input.upper()}**:")
            
            # Generate dummy options
            correct_ans = data.get('definition_vi')
            wrong_options = ["Sự phát triển không ngừng", "Một cách nhanh chóng", "Không có giá trị", "Sự thay đổi đột ngột"]
            options = [correct_ans] + random.sample(wrong_options, 2)
            random.shuffle(options)
            
            user_choice = st.radio("Lựa chọn của bạn:", options, key="mini_quiz_radio")
            if st.button("Kiểm tra đáp án"):
                if user_choice == correct_ans:
                    st.success("Chính xác! Bạn đã ghi nhớ từ này rất tốt. +5 XP")
                    if not st.session_state.quiz_done:
                        st.session_state.xp += 5
                        st.session_state.quiz_done = True
                else:
                    st.error(f"Opps! Chưa đúng rồi. Nghĩa đúng là: {correct_ans}")

            # Nuance
            with st.expander("💡 IELTS Nuance (Cách dùng chuyên sâu)"):
                st.write(data.get('nuance'))
        else:
            st.error(data['error'])

elif page == "📚 Chủ đề":
    if "topic_active" not in st.session_state: st.session_state.topic_active = False
    
    if not st.session_state.topic_active:
        st.subheader("Chọn chủ đề từ vựng IELTS:")
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
        
        # Display topics in columns
        cols = st.columns(2)
        for i, (label, topic_id) in enumerate(topics):
            if cols[i % 2].button(label, use_container_width=True, key=f"btn_{topic_id}"):
                st.session_state.current_cards = get_cards_by_topic(topic_id)
                st.session_state.current_topic_name = label
                if st.session_state.current_cards:
                    st.session_state.card_idx = 0
                    st.session_state.topic_active = True
                    st.rerun()
                else:
                    st.error(f"Chủ đề {label} chưa có dữ liệu trong DB!")
    else:
        # PREMIUM FLASHCARD FLOW
        cards = st.session_state.current_cards
        idx = st.session_state.card_idx
        card = cards[idx]
        
        st.markdown(f"#### 🔎 Chủ đề: {st.session_state.current_topic_name}")
        st.progress((idx + 1) / len(cards))
        
        render_flashcard(card)
        
        col1, col2, col3 = st.columns(3)
        if col1.button("Tiếp tục", use_container_width=True):
            if idx < len(cards) - 1: st.session_state.card_idx += 1; st.rerun()
            else: st.success("🎉 Hoàn thành!"); st.session_state.topic_active = False; st.rerun()
        if col2.button("🔊 Nghe", use_container_width=True): speak(card['word'])
        if col3.button("✅ Thuộc rồi", use_container_width=True):
            if card['word'] not in [w['word'] for w in st.session_state.word_bank]:
                word_to_save = {
                    "word": card['word'],
                    "phonetic": card.get('phonetic'),
                    "definition_vi": card['meaning'],
                    "definition_en": card.get('example'), # Fallback
                    "word_class": "Vocabulary"
                }
                if save_word(word_to_save):
                    st.session_state.word_bank = get_all_saved_words()
            if idx < len(cards) - 1: st.session_state.card_idx += 1; st.rerun()
            else: st.session_state.topic_active = False; st.rerun()
        
        if st.button("⬅️ Thoát chủ đề", use_container_width=True):
            st.session_state.topic_active = False
            st.rerun()

elif page == "🗣️ Speaking":
    speaking.SpeakingAI.render_ui()

elif page == "📒 Sổ tay":
    notebook.NotebookAI.render_ui()

elif page == "📖 Reading":
    reading.ReadingAI.render_ui()

elif page == "✍️ Writing":
    writing.WritingAI.render_ui()

elif page == "🤖 Coaching":
    coaching.CoachingAI.render_ui()

elif page == "🎓 Ôn tập":
    st.subheader("🎯 Đấu trường Ôn tập")
    if len(st.session_state.word_bank) < 4:
        st.warning("Cần ít nhất 4 từ.")
    else:
        if "review_quiz" not in st.session_state:
            correct = random.choice(st.session_state.word_bank)
            wrong = random.sample([w for w in st.session_state.word_bank if w['word'] != correct['word']], 3)
            options = [correct['definition_vi']] + [w['definition_vi'] for w in wrong]
            random.shuffle(options)
            st.session_state.review_quiz = {
                'correct': correct,
                'options': options,
                'answered': False,
                'is_correct': False
            }

        quiz = st.session_state.review_quiz
        choice = st.radio(f"Nghĩa của {quiz['correct']['word'].upper()} là gì?", quiz['options'], disabled=quiz['answered'])
        
        if not quiz['answered']:
            if st.button("Kiểm tra"):
                quiz['answered'] = True
                if choice == quiz['correct']['definition_vi']: 
                    quiz['is_correct'] = True
                    st.session_state.xp += 10
                else: 
                    quiz['is_correct'] = False
                st.rerun()
        else:
            if quiz['is_correct']:
                st.success("Chuẩn! +10 XP")
            else:
                st.error(f"Sai! Đáp án: {quiz['correct']['definition_vi']}")
                
            if st.button("Câu tiếp theo"):
                del st.session_state.review_quiz
                st.rerun()