import streamlit as st
import json
import random
import pandas as pd
from openai import OpenAI
from datetime import datetime

# ==========================================
# 1. CẤU HÌNH & KHỞI TẠO SESSION STATE
# ==========================================
st.set_page_config(page_title="VocabStream - 5WordsAI", page_icon="🧠", layout="centered")

if "user_profile" not in st.session_state:
    st.session_state.user_profile = {"target": "Giao tiếp", "level": "B1", "topic": "Đời sống"}
if "daily_words" not in st.session_state:
    st.session_state.daily_words = []
if "learning_history" not in st.session_state:
    st.session_state.learning_history = {} # Lưu điểm SRS cho mỗi từ
if "flashcard_index" not in st.session_state:
    st.session_state.flashcard_index = 0
if "show_answer" not in st.session_state:
    st.session_state.show_answer = False

# ==========================================
# 2. HÀM TƯƠNG TÁC AI (MINIMAX API)
# ==========================================
def get_ai_client(api_key):
    # Sử dụng OpenRouter làm endpoint cho model minimax/minimax-m3:free
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

def generate_daily_words(api_key, target, level, topic):
    client = get_ai_client(api_key)
    prompt = f"""
    Đóng vai một chuyên gia ngôn ngữ. Dựa trên mục tiêu học: {target}, trình độ: {level}, chủ đề yêu thích: {topic}.
    Hãy chọn đúng 5 từ vựng tiếng Anh phù hợp nhất để học hôm nay.
    Trả về KẾT QUẢ DUY NHẤT LÀ ĐỊNH DẠNG JSON ARRAY, không giải thích gì thêm.
    Cấu trúc mỗi object:
    {{
        "word": "từ tiếng Anh",
        "pronunciation": "phát âm IPA",
        "meaning": "nghĩa tiếng Việt",
        "examples": ["ví dụ 1", "ví dụ 2"],
        "mnemonic": "câu gợi nhớ hoặc mẹo nhớ (tiếng Việt)",
        "collocation": "1 cụm từ đi kèm phổ biến"
    }}
    """
    try:
        response = client.chat.completions.create(
            model="minimax/minimax-m3:free",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        content = response.choices[0].message.content
        # Làm sạch chuỗi JSON nếu AI trả về kèm markdown ```json
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        words = json.loads(content)
        return words
    except Exception as e:
        st.error(f"Lỗi khi gọi AI API: {e}")
        return []

def generate_quiz(api_key, word):
    client = get_ai_client(api_key)
    prompt = f"""
    Tạo 1 câu hỏi trắc nghiệm điền từ vào chỗ trống tiếng Anh để kiểm tra từ "{word}".
    Trả về DUY NHẤT JSON:
    {{
        "question": "Câu tiếng Anh có chỗ trống chứa dấu ___",
        "options": ["A", "B", "C", "D"],
        "answer": "Từ đúng"
    }}
    """
    try:
        response = client.chat.completions.create(
            model="minimax/minimax-m3:free",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        content = response.choices[0].message.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return json.loads(content)
    except:
        return None

# ==========================================
# 3. GIAO DIỆN CHÍNH
# ==========================================
st.title("🧠 VocabStream - Daily5AI")
st.caption("5 từ mỗi ngày – Nhớ sâu, không quên")

with st.sidebar:
    st.header("⚙️ Cài đặt & AI")
    api_key = st.text_input("Nhập OpenRouter API Key (hỗ trợ Minimax)", type="password")
    st.markdown("---")
    st.markdown("**Core Values:**\n- Học 5 từ/ngày\n- Active Recall\n- AI Cá nhân hóa")

tab1, tab2, tab3, tab4 = st.tabs(["👤 Cá nhân hóa", "📚 5 Từ Hôm Nay", "🎮 Ôn Tập", "📈 Tiến Độ"])

# --- TAB 1: ONBOARDING ---
with tab1:
    st.subheader("Thiết lập lộ trình học")
    col1, col2 = st.columns(2)
    with col1:
        target = st.selectbox("Mục tiêu", ["IELTS", "TOEIC", "Giao tiếp", "Công việc", "Du lịch"], index=2)
        level = st.selectbox("Trình độ hiện tại", ["A1 - Người mới", "A2 - Cơ bản", "B1 - Trung cấp", "B2 - Khá", "C1 - Cao cấp"], index=2)
    with col2:
        topic = st.selectbox("Chủ đề yêu thích", ["Công nghệ", "Y tế", "Kinh doanh", "Đời sống", "Du lịch", "Giáo dục"], index=3)
        time_commit = st.slider("Thời gian học/ngày (phút)", 5, 30, 10)
    
    if st.button("Lưu cấu hình", type="primary"):
        st.session_state.user_profile = {"target": target, "level": level, "topic": topic}
        st.success("Đã lưu lộ trình cá nhân hóa!")

# --- TAB 2: DAILY STREAM (5 TỪ) ---
with tab2:
    st.subheader("Bài học hôm nay")
    if not api_key:
        st.warning("Vui lòng nhập API Key ở menu bên trái để AI tạo bài học.")
    else:
        if st.button("✨ Nhờ AI Tạo 5 Từ Mới", use_container_width=True):
            with st.spinner("AI đang phân tích và chọn 5 từ phù hợp nhất..."):
                p = st.session_state.user_profile
                words = generate_daily_words(api_key, p["target"], p["level"].split(" ")[0], p["topic"])
                if words and len(words) == 5:
                    st.session_state.daily_words = words
                    for w in words:
                        if w["word"] not in st.session_state.learning_history:
                            # Khởi tạo điểm SRS cơ bản
                            st.session_state.learning_history[w["word"]] = {"retention": 0, "reviews": 0}
                    st.success("Đã tạo xong bài học!")
                else:
                    st.error("AI không trả về đúng định dạng. Vui lòng thử lại.")

        if st.session_state.daily_words:
            for i, word_data in enumerate(st.session_state.daily_words):
                with st.expander(f"**{i+1}. {word_data['word']}** (/{word_data.get('pronunciation', '')}/) - {word_data.get('meaning', '')}"):
                    st.markdown(f"**💡 Mẹo nhớ (Mnemonic):** {word_data.get('mnemonic', '')}")
                    st.markdown(f"**🔗 Collocation:** {word_data.get('collocation', '')}")
                    st.markdown("**📝 Ví dụ:**")
                    for ex in word_data.get('examples', []):
                        st.markdown(f"- *{ex}*")

# --- TAB 3: ÔN TẬP (ACTIVE RECALL) ---
with tab3:
    st.subheader("Ôn tập đa dạng (Active Recall & Interleaving)")
    
    if not st.session_state.daily_words:
        st.info("Hãy tạo 5 từ hôm nay ở tab trước để bắt đầu ôn tập.")
    else:
        mode = st.radio("Chọn chế độ ôn tập:", ["🗂️ Flashcard thông minh", "📝 Điền từ vào câu (AI Quiz)"], horizontal=True)
        st.markdown("---")
        
        if mode == "🗂️ Flashcard thông minh":
            idx = st.session_state.flashcard_index % len(st.session_state.daily_words)
            current_word = st.session_state.daily_words[idx]
            
            # Khung Flashcard
            st.markdown(f"""
            <div style="padding: 30px; border-radius: 15px; border: 2px solid #4CAF50; text-align: center; margin-bottom: 20px;">
                <h2 style="margin:0;">{current_word['word']}</h2>
                <p style="color: gray;">/{current_word.get('pronunciation', '')}/</p>
            </div>
            """, unsafe_allow_html=True) # Dùng markdown HTML cơ bản để trang trí an toàn, không dùng html component
            
            if st.session_state.show_answer:
                st.info(f"**Nghĩa:** {current_word['meaning']}")
                st.write(f"**Mẹo nhớ:** {current_word.get('mnemonic', '')}")
                
                col1, col2, col3 = st.columns(3)
                if col1.button("Quên (Lặp lại ngay)"):
                    st.session_state.learning_history[current_word['word']]['retention'] -= 10
                    st.session_state.show_answer = False
                    st.session_state.flashcard_index += 1
                    st.rerun()
                if col2.button("Nhớ mang máng"):
                    st.session_state.learning_history[current_word['word']]['reviews'] += 1
                    st.session_state.show_answer = False
                    st.session_state.flashcard_index += 1
                    st.rerun()
                if col3.button("Nhớ rõ (Tăng khoảng cách ôn)"):
                    st.session_state.learning_history[current_word['word']]['retention'] += 20
                    st.session_state.learning_history[current_word['word']]['reviews'] += 1
                    st.session_state.show_answer = False
                    st.session_state.flashcard_index += 1
                    st.rerun()
            else:
                if st.button("Lật thẻ (Show Answer)", use_container_width=True):
                    st.session_state.show_answer = True
                    st.rerun()

        elif mode == "📝 Điền từ vào câu (AI Quiz)":
            if api_key:
                word_to_quiz = random.choice(st.session_state.daily_words)["word"]
                if st.button(f"Tạo câu hỏi trắc nghiệm cho từ ngẫu nhiên", use_container_width=True):
                    with st.spinner("AI đang tạo ngữ cảnh thực tế..."):
                        quiz_data = generate_quiz(api_key, word_to_quiz)
                        if quiz_data:
                            st.session_state.current_quiz = quiz_data
                
                if "current_quiz" in st.session_state:
                    q = st.session_state.current_quiz
                    st.markdown(f"### {q['question']}")
                    choice = st.radio("Chọn đáp án đúng:", q['options'])
                    if st.button("Kiểm tra"):
                        if choice.lower() == q['answer'].lower():
                            st.success("Chính xác! 🎉")
                            st.session_state.learning_history[q['answer']]['retention'] += 15
                        else:
                            st.error(f"Sai rồi. Đáp án đúng là: **{q['answer']}**")
                            st.session_state.learning_history[q['answer']]['retention'] -= 5
            else:
                st.warning("Cần API Key để sử dụng chế độ AI Quiz.")

# --- TAB 4: THEO DÕI TIẾN ĐỘ ---
with tab4:
    st.subheader("Phân tích Retention (Spaced Repetition)")
    
    if not st.session_state.learning_history:
        st.info("Chưa có dữ liệu học tập. Hãy hoàn thành các bài ôn tập!")
    else:
        # Gamification đơn giản
        words_mastered = sum(1 for w, data in st.session_state.learning_history.items() if data['retention'] > 50)
        col1, col2, col3 = st.columns(3)
        col1.metric("Streak hiện tại", "1 ngày", "🔥")
        col2.metric("Tổng từ đang học", str(len(st.session_state.learning_history)))
        col3.metric("Từ đã thành thạo", str(words_mastered), f"+{words_mastered}")
        
        # Biểu đồ DataFrame hiển thị Retention
        df = pd.DataFrame.from_dict(st.session_state.learning_history, orient='index').reset_index()
        df.columns = ['Từ vựng', 'Điểm Retention (%)', 'Số lần ôn']
        # Normalize retention to max 100% for UI
        df['Điểm Retention (%)'] = df['Điểm Retention (%)'].clip(0, 100)
        
        st.markdown("**Biểu đồ độ ghi nhớ từ vựng**")
        st.bar_chart(data=df.set_index('Từ vựng')['Điểm Retention (%)'])
        
        st.dataframe(df, use_container_width=True)
