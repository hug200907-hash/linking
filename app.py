import streamlit as st
import json
import random
import pandas as pd
from openai import OpenAI

# ==========================================
# 1. CẤU HÌNH & KHỞI TẠO SESSION STATE
# ==========================================
st.set_page_config(page_title="VocabStream - 5WordsAI", page_icon="🧠", layout="centered")

if "user_profile" not in st.session_state:
    st.session_state.user_profile = {"target": "Giao tiếp", "level": "B1", "topic": "Đời sống"}
if "daily_words" not in st.session_state:
    st.session_state.daily_words = []
if "learning_history" not in st.session_state:
    st.session_state.learning_history = {}
if "flashcard_index" not in st.session_state:
    st.session_state.flashcard_index = 0
if "show_answer" not in st.session_state:
    st.session_state.show_answer = False

# ==========================================
# 2. HÀM TƯƠNG TÁC AI (KIỂM TRA KEY AN TOÀN)
# ==========================================
def get_ai_client(api_key):
    # Kiểm tra key hợp lệ trước khi khởi tạo OpenAI Client
    if not api_key or not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("API Key không hợp lệ hoặc đang để trống.")
    
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key.strip(),
    )

def generate_daily_words(api_key, target, level, topic):
    try:
        client = get_ai_client(api_key)
        prompt = f"""
        Đóng vai một chuyên gia ngôn ngữ. Dựa trên mục tiêu học: {target}, trình độ: {level}, chủ đề yêu thích: {topic}.
        Hãy chọn đúng 5 từ vựng tiếng Anh phù hợp nhất để học hôm nay.
        Trả về KẾT QUẢ DUY NHẤT LÀ ĐỊNH DẠNG JSON ARRAY, không giải thích gì thêm.
        Cấu trúc mỗi object:
        [
            {{
                "word": "từ tiếng Anh",
                "pronunciation": "phát âm IPA",
                "meaning": "nghĩa tiếng Việt",
                "examples": ["ví dụ 1", "ví dụ 2"],
                "mnemonic": "câu gợi nhớ hoặc mẹo nhớ (tiếng Việt)",
                "collocation": "1 cụm từ đi kèm phổ biến"
            }}
        ]
        """
        response = client.chat.completions.create(
            model="minimax/minimax-m3:free",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        content = response.choices[0].message.content
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        words = json.loads(content)
        return words
    except ValueError as ve:
        st.error(f"⚠️ {ve}")
        return []
    except Exception as e:
        st.error(f"❌ Lỗi khi gọi AI API: {e}")
        return []

def generate_quiz(api_key, word):
    try:
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
    except Exception as e:
        st.error(f"Lỗi tạo câu hỏi: {e}")
        return None

# ==========================================
# 3. GIAO DIỆN CHÍNH
# ==========================================
st.title("🧠 VocabStream - Daily5AI")
st.caption("5 từ mỗi ngày – Nhớ sâu, không quên")

# --- LẤY API KEY AN TOÀN BÊN SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Cài đặt hệ thống")
    
    api_key = ""
    # 1. Ưu tiên lấy key từ Secrets
    if "MINIMAX_API_KEY" in st.secrets and st.secrets["MINIMAX_API_KEY"].strip():
        api_key = st.secrets["MINIMAX_API_KEY"].strip()
        st.success("✅ Đã kết nối API tự động (từ Secrets)")
    else:
        # 2. Nếu Secrets không có, cho phép nhập tay
        api_key = st.text_input("🔑 Nhập OpenRouter API Key", type="password", help="Dùng cho Minimax API")
        if not api_key.strip():
            st.warning("⚠️ Vui lòng nhập API Key để ứng dụng hoạt động.")

    st.markdown("---")
    st.markdown("""
    **Core Values:**
    - 🎯 Học đúng 5 từ/ngày
    - 🔄 Spaced Repetition
    - 🤖 AI Cá nhân hóa 100%
    """)

tab1, tab2, tab3, tab4 = st.tabs(["👤 Cá nhân hóa", "📚 5 Từ Hôm Nay", "🎮 Ôn Tập", "📈 Tiến Độ"])

# --- TAB 1: ONBOARDING ---
with tab1:
    st.subheader("Thiết lập lộ trình học")
    col1, col2 = st.columns(2)
    with col1:
        target = st.selectbox("Mục tiêu học tập", ["IELTS", "TOEIC", "Giao tiếp", "Công việc", "Du lịch"], index=2)
        level = st.selectbox("Trình độ hiện tại", ["A1 - Người mới", "A2 - Cơ bản", "B1 - Trung cấp", "B2 - Khá", "C1 - Cao cấp"], index=2)
    with col2:
        topic = st.selectbox("Chủ đề yêu thích", ["Công nghệ", "Y tế", "Kinh doanh", "Đời sống", "Du lịch", "Giáo dục", "Giải trí"], index=3)
        time_commit = st.slider("Thời gian học/ngày (phút)", 5, 30, 10)
    
    if st.button("Lưu cấu hình", type="primary"):
        st.session_state.user_profile = {"target": target, "level": level, "topic": topic}
        st.success("✅ Đã lưu lộ trình học cá nhân!")

# --- TAB 2: DAILY STREAM (5 TỪ) ---
with tab2:
    st.subheader("Bài học hôm nay của bạn")
    
    if not api_key.strip():
        st.error("❌ Vui lòng cung cấp OpenRouter API Key ở sidebar bên trái để tiếp tục.")
    else:
        if st.button("✨ Nhờ AI Tạo 5 Từ Mới", use_container_width=True):
            with st.spinner("🤖 AI đang phân tích và chọn 5 từ phù hợp..."):
                p = st.session_state.user_profile
                words = generate_daily_words(api_key, p["target"], p["level"].split(" ")[0], p["topic"])
                
                if words and len(words) > 0:
                    st.session_state.daily_words = words
                    for w in words:
                        if w["word"] not in st.session_state.learning_history:
                            st.session_state.learning_history[w["word"]] = {"retention": 0, "reviews": 0}
                    st.success("🎉 Đã tạo xong bài học!")

        if st.session_state.daily_words:
            st.markdown("---")
            for i, word_data in enumerate(st.session_state.daily_words):
                with st.expander(f"**{i+1}. {word_data.get('word', '')}** (/{word_data.get('pronunciation', '')}/) - {word_data.get('meaning', '')}"):
                    st.markdown(f"**💡 Mẹo nhớ:** {word_data.get('mnemonic', '')}")
                    st.markdown(f"**🔗 Collocation:** {word_data.get('collocation', '')}")
                    st.markdown("**📝 Ví dụ:**")
                    for ex in word_data.get('examples', []):
                        st.markdown(f"- *{ex}*")

# --- TAB 3: ÔN TẬP ---
with tab3:
    st.subheader("Ôn tập đa dạng (Active Recall)")
    
    if not st.session_state.daily_words:
        st.info("Hãy sang tab '5 Từ Hôm Nay' để tạo bài học trước.")
    else:
        mode = st.radio("Chọn phương pháp ôn tập:", ["🗂️ Flashcard thông minh", "📝 Trắc nghiệm AI (Điền từ)"], horizontal=True)
        st.markdown("---")
        
        if mode == "🗂️ Flashcard thông minh":
            idx = st.session_state.flashcard_index % len(st.session_state.daily_words)
            current_word = st.session_state.daily_words[idx]
            
            st.markdown(f"""
            <div style="padding: 40px; border-radius: 10px; border: 2px solid #ccc; text-align: center; background-color: #f9f9f9; color: #333; margin-bottom: 20px;">
                <h1 style="margin:0; font-size: 40px;">{current_word['word']}</h1>
                <p style="color: #666; font-size: 18px;">/{current_word.get('pronunciation', '')}/</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.show_answer:
                st.success(f"**Nghĩa:** {current_word['meaning']}")
                st.write(f"**Mẹo nhớ:** {current_word.get('mnemonic', '')}")
                
                col1, col2, col3 = st.columns(3)
                if col1.button("🔴 Quên"):
                    st.session_state.learning_history[current_word['word']]['retention'] -= 10
                    st.session_state.show_answer = False
                    st.session_state.flashcard_index += 1
                    st.rerun()
                if col2.button("🟡 Nhớ mang máng"):
                    st.session_state.learning_history[current_word['word']]['reviews'] += 1
                    st.session_state.show_answer = False
                    st.session_state.flashcard_index += 1
                    st.rerun()
                if col3.button("🟢 Nhớ rất rõ"):
                    st.session_state.learning_history[current_word['word']]['retention'] += 20
                    st.session_state.learning_history[current_word['word']]['reviews'] += 1
                    st.session_state.show_answer = False
                    st.session_state.flashcard_index += 1
                    st.rerun()
            else:
                if st.button("Lật thẻ (Show Answer)", use_container_width=True, type="primary"):
                    st.session_state.show_answer = True
                    st.rerun()

        elif mode == "📝 Trắc nghiệm AI (Điền từ)":
            if not api_key.strip():
                st.warning("Cần API Key để tạo câu hỏi trắc nghiệm bằng AI.")
            else:
                word_to_quiz = random.choice(st.session_state.daily_words)["word"]
                if st.button("Tạo câu hỏi ngữ cảnh thực tế", type="primary"):
                    with st.spinner("AI đang tạo ngữ cảnh..."):
                        quiz_data = generate_quiz(api_key, word_to_quiz)
                        if quiz_data:
                            st.session_state.current_quiz = quiz_data
                
                if "current_quiz" in st.session_state:
                    q = st.session_state.current_quiz
                    st.markdown(f"### {q.get('question', '')}")
                    
                    with st.form("quiz_form"):
                        choice = st.radio("Chọn đáp án đúng:", q.get('options', []))
                        submitted = st.form_submit_button("Kiểm tra đáp án")
                        
                        if submitted:
                            if choice.lower() == q['answer'].lower():
                                st.success(f"Chính xác! 🎉 Đáp án là: **{q['answer']}**")
                                if q['answer'] in st.session_state.learning_history:
                                    st.session_state.learning_history[q['answer']]['retention'] += 15
                            else:
                                st.error(f"Sai rồi. Đáp án đúng là: **{q['answer']}**")
                                if q['answer'] in st.session_state.learning_history:
                                    st.session_state.learning_history[q['answer']]['retention'] -= 5

# --- TAB 4: TIẾN ĐỘ ---
with tab4:
    st.subheader("Phân tích độ nhớ (Spaced Repetition)")
    
    if not st.session_state.learning_history:
        st.info("Chưa có dữ liệu học tập.")
    else:
        words_mastered = sum(1 for w, data in st.session_state.learning_history.items() if data['retention'] > 50)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Streak", "1 ngày", "🔥")
        col2.metric("Tổng từ đang học", str(len(st.session_state.learning_history)))
        col3.metric("Từ đã thành thạo", str(words_mastered), f"+{words_mastered}")
        
        df = pd.DataFrame.from_dict(st.session_state.learning_history, orient='index').reset_index()
        df.columns = ['Từ vựng', 'Điểm Retention (%)', 'Số lần ôn']
        df['Điểm Retention (%)'] = df['Điểm Retention (%)'].clip(0, 100)
        
        st.markdown("---")
        st.bar_chart(data=df.set_index('Từ vựng')['Điểm Retention (%)'])
        
        with st.expander("Xem bảng dữ liệu chi tiết"):
            st.dataframe(df, use_container_width=True)
