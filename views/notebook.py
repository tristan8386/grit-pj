import streamlit as st
import pandas as pd
from modules.db_handler import delete_word, toggle_star, get_all_saved_words
from modules.ai_handler import speak

class NotebookAI:
    @staticmethod
    def render_ui():
        # Premium CSS for Cards and Stats
        st.markdown("""
        <style>
            .stat-container {
                display: flex;
                justify-content: space-between;
                gap: 20px;
                margin-bottom: 30px;
            }
            .stat-box {
                flex: 1;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                padding: 20px;
                text-align: center;
                backdrop-filter: blur(10px);
            }
            .stat-val { font-size: 28px; font-weight: bold; color: #3B82F6; }
            .stat-label { color: #94A3B8; font-size: 14px; margin-top: 5px; }
            
            .word-card {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 24px;
                padding: 20px;
                margin-bottom: 20px;
                transition: transform 0.3s ease;
                position: relative;
                min-height: 180px;
            }
            .word-card:hover { 
                transform: translateY(-5px);
                background: rgba(255, 255, 255, 0.07);
                border-color: rgba(59, 130, 246, 0.4);
            }
            .tag {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
                text-transform: uppercase;
                margin-bottom: 10px;
            }
            .tag-noun { background: rgba(59, 130, 246, 0.2); color: #60A5FA; }
            .tag-verb { background: rgba(16, 185, 129, 0.2); color: #34D399; }
            .tag-adj { background: rgba(245, 158, 11, 0.2); color: #FBBF24; }
            .tag-adv { background: rgba(139, 92, 246, 0.2); color: #A78BFA; }
            .tag-other { background: rgba(148, 163, 184, 0.2); color: #CBD5E1; }
            
            .card-word { font-size: 20px; font-weight: bold; color: #F1F5F9; margin-bottom: 5px; }
            .card-ipa { color: #94A3B8; font-size: 14px; margin-bottom: 10px; }
            .card-meaning { color: #E2E8F0; font-size: 16px; font-weight: 500; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 10px; }
            
            div[data-testid="column"] { display: flex; flex-direction: column; }
        </style>
        """, unsafe_allow_html=True)

        st.title("📓 Sổ tay Siêu nhân Lexi")

        # Sync with DB
        word_bank = get_all_saved_words()
        
        # 1. STATISTICS HEADER
        total_words = len(word_bank)
        starred_words = sum(1 for w in word_bank if w.get('is_starred'))
        streak = st.session_state.get('xp', 0) // 50 # Dummy streak based on XP for now
        
        st.markdown(f"""
        <div class="stat-container">
            <div class="stat-box">
                <div class="stat-val">📚 {total_words}</div>
                <div class="stat-label">Tổng vũ khí</div>
            </div>
            <div class="stat-box">
                <div class="stat-val">⭐ {starred_words}</div>
                <div class="stat-label">Cần luyện tập</div>
            </div>
            <div class="stat-box">
                <div class="stat-val">🔥 {streak}</div>
                <div class="stat-label">Ngày rực cháy</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not word_bank:
            st.info("Sổ tay đang trống. Hãy bắt đầu học và lưu từ nhé! 🚀")
            return

        # 2. SEARCH & TABS
        search_query = st.text_input("🔍 Truy tìm vũ khí trong kho:", placeholder="Nhập từ hoặc nghĩa...")
        
        tab_starred, tab_all, tab_new = st.tabs(["⭐ Cần ôn tập", "📚 Tất cả từ", "🆕 Từ mới lưu"])

        def render_cards(data_list, prefix=""):
            if not data_list:
                st.write("Chưa có từ nào ở nhóm này.")
                return

            # Filtering if search active
            if search_query:
                q = search_query.lower()
                data_list = [w for w in data_list if q in w['word'].lower() or q in (w.get('definition_vi') or "").lower()]

            # Grid creation: 3 cards per row
            rows = [data_list[i:i + 3] for i in range(0, len(data_list), 3)]
            for i, row in enumerate(rows):
                cols = st.columns(3)
                for j, word_obj in enumerate(row):
                    with cols[j]:
                        w_class = (word_obj.get('word_class') or "other").lower()
                        tag_color = "tag-noun" if "noun" in w_class else "tag-verb" if "verb" in w_class else "tag-adj" if "adj" in w_class else "tag-adv" if "adv" in w_class else "tag-other"
                        
                        st.markdown(f"""
                        <div class="word-card">
                            <span class="tag {tag_color}">{w_class}</span>
                            <div class="card-word">{word_obj['word'].upper()}</div>
                            <div class="card-ipa">/{word_obj.get('phonetic', '')}/</div>
                            <div class="card-meaning">{word_obj.get('definition_vi', '')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Interactive Row (Invisible containers for buttons)
                        btn_col1, btn_col2, btn_col3 = st.columns(3)
                        
                        if btn_col1.button("🔊", key=f"{prefix}speak_{word_obj['word']}_{i}_{j}", help="Phát âm"):
                            speak(word_obj['word'])
                        
                        star_icon = "⭐" if word_obj.get('is_starred') else "☆"
                        if btn_col2.button(star_icon, key=f"{prefix}star_{word_obj['word']}_{i}_{j}", help="Đánh dấu ôn tập"):
                            toggle_star(word_obj['word'], not word_obj.get('is_starred'))
                            st.rerun()
                            
                        if btn_col3.button("🗑", key=f"{prefix}del_{word_obj['word']}_{i}_{j}", help="Xóa từ"):
                            delete_word(word_obj['word'])
                            st.rerun()

        with tab_starred:
            starred_list = [w for w in word_bank if w.get('is_starred')]
            render_cards(starred_list, "starred")

        with tab_all:
            render_cards(word_bank, "all")

        with tab_new:
            # Sort by potentially saved date if available, or just first 10
            render_cards(word_bank[:10], "new")
