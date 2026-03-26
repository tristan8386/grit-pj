import streamlit as st

def load_css(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        st.markdown(f'<style>\n{f.read()}\n</style>', unsafe_allow_html=True)

def render_sidebar_logo(logo_base64):
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <img src="{logo_base64}" style="width: 120px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
    </div>
    """, unsafe_allow_html=True)

def render_header(logo_base64, xp):
    st.markdown(f"""
    <div class="header-container" style="display: flex; justify-content: space-between; align-items: center;">
        <div style="display: flex; align-items: center; gap: 15px;">
            <img src="{logo_base64}" style="width: 50px; height: 50px; border-radius: 10px; object-fit: cover;">
            <div><b style="font-size: 20px;">SIÊU NHÂN LEXI</b> <small>| AI Learning Flow</small></div>
        </div>
        <div style="background: #3B82F6; color: white; padding: 5px 15px; border-radius: 10px; font-weight: bold;">✨ {xp} XP</div>
    </div>
    """, unsafe_allow_html=True)

def render_word_card(word_input, data):
    st.markdown(f"""
    <div class="mochi-card">
        <h2 style="color: #3B82F6 !important;">{word_input.upper()}</h2>
        <p>/{data.get('phonetic')}/ • {data.get('word_class')}</p>
        <div style="background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 12px; border-left: 5px solid #3B82F6;">
            <b>{data.get('definition_vi')}</b><br>
            <i>{data.get('definition_en')}</i>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_flashcard(card):
    # Dùng regex hoặc thay thế chuẩn để tô đậm từ khóa
    example_sentence = card['example'].replace(card['word'], f"<b>{card['word']}</b>")
    # Lấy thêm ảnh tĩnh (nếu không có thì dùng ảnh mặc định)
    image_word = card['word'].replace(' ', ',')
    
    st.markdown(f"""
    <div class="flashcard-container">
        <div class="main-flashcard">
            <img src="https://loremflickr.com/500/500/{image_word},nature" class="flashcard-image">
            <h2 style="color: #3B82F6 !important;">{card['word'].upper()}</h2>
            <p style="color: #94A3B8; font-size: 1.1em;">/{card.get('phonetic', '')}/</p>
            <p style="color: #F8FAFC; font-weight: bold;">{card['meaning']}</p>
            <p class="example-sentence">{example_sentence}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
