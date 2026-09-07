import streamlit as st
import json
import random
import datetime
import pandas as pd
from openai import OpenAI

# ==========================================
# 1. TÙY CHỈNH TRANG & GIAO DIỆN (PAGE CONFIG)
# ==========================================
st.set_page_config(
    page_title="VocabStream - 5 từ mỗi ngày",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS cho giao diện
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #555;
        margin-bottom: 20px;
    }
    .word-card {
        background-color: #F8F9FA;
        border-radius: 12px;
        padding: 30px;
        border-top: 6px solid #1E88E5;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        margin-bottom: 20px;
        text-align: center;
    }
    .word-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #0D47A1;
        margin-bottom: 5px;
    }
    .ipa-text {
        font-size: 1.2rem;
        color: #E65100;
        font-style: italic;
    }
    .meaning-text {
        font-size: 1.4rem;
        font-weight: 600;
        color: #2E7D32;
        margin-top: 10px;
    }
    .mnemonic-box {
        background-color: #FFF9C4;
        border-left: 4px solid #FBC02D;
        padding: 15px;
        border-radius: 8px;
        margin: 20px 0;
        text-align: left;
        font-size: 1.1rem;
    }
    .badge-streak {
        background-color: #FFF3E0;
        color: #E65100;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: bold;
    }
    .flashcard-box {
        background-color: #FFFFFF;
        border: 2px solid #1E88E5;
        border-radius: 16px;
        padding: 40px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KHỞI TẠO STATE (SESSION STATE SAFEGUARD)
# ==========================================
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "onboarded": True,
        "goal": "IELTS 6.5+",
        "level": "B1",
        "topics": ["Technology", "Business"],
        "daily_minutes": 10,
        "streak": 5,
        "total_mastered": 28,
        "retention_rate": 88
    }

if "daily_words" not in st.session_state:
    st.session_state.daily_words = [
        {
            "word": "Resilient",
            "ipa": "/rɪˈzɪl.jənt/",
            "vietnamese": "Kiên cường, mau phục hồi",
            "english_meaning": "Able to withstand or recover quickly from difficult conditions.",
            "examples": ["The local economy is remarkably resilient despite global turbulence."],
            "collocations": ["resilient economy", "highly resilient"],
            "mnemonic": "💡 Gợi nhớ: 'Re' (Lại) + 'Silient' (im lặng âm thầm vượt qua) -> Kiên cường vươn lên.",
            "status": "Learning",
            "memory_strength": 75
        },
        {
            "word": "Foster",
            "ipa": "/ˈfɒs.tər/",
            "vietnamese": "Nuôi dưỡng, thúc đẩy",
            "english_meaning": "Encourage or promote the development of something.",
            "examples": ["The teacher aims to foster a creative environment in the classroom."],
            "collocations": ["foster innovation", "foster collaboration"],
            "mnemonic": "💡 Gợi nhớ: 'FOSter' phát âm gần như 'Phở' -> Ăn phở để bồi bổ, nuôi dưỡng cơ thể.",
            "status": "Learning",
            "memory_strength": 60
        },
        {
            "word": "Pragmatic",
            "ipa": "/præɡˈmæt.ɪk/",
            "vietnamese": "Thực tế, thực dụng",
            "english_meaning": "Dealing with things sensibly and realistically based on practical considerations.",
            "examples": ["We need a pragmatic approach to solving this budget issue."],
            "collocations": ["pragmatic approach", "pragmatic solution"],
            "mnemonic": "💡 Gợi nhớ: 'Prag' gần giống 'Practice' (Thực hành) -> Làm việc phải hướng tới thực tế.",
            "status": "Reviewing",
            "memory_strength": 85
        },
        {
            "word": "Lucid",
            "ipa": "/ˈluː.sɪd/",
            "vietnamese": "Rõ ràng, minh mẫn",
            "english_meaning": "Expressed clearly; easy to understand.",
            "examples": ["She gave a lucid explanation of a complex scientific theory."],
            "collocations": ["lucid explanation", "lucid dream"],
            "mnemonic": "💡 Gợi nhớ: 'Lucid' nghe như 'Lúc đi' -> Lúc đi học tư duy luôn phải sáng suốt, rõ ràng.",
            "status": "Learning",
            "memory_strength": 50
        },
        {
            "word": "Mitigate",
            "ipa": "/ˈmɪt.ɪ.ɡeɪt/",
            "vietnamese": "Giảm nhẹ, làm dịu",
            "english_meaning": "Make less severe, serious, or painful.",
            "examples": ["New safety measures were introduced to mitigate risks."],
            "collocations": ["mitigate risk", "mitigate impact"],
            "mnemonic": "💡 Gợi nhớ: 'Miti' -> Mi-ni (nhỏ lại) + 'gate' (cổng) -> Thu nhỏ cổng để giảm thiểu rủi ro.",
            "status": "Reviewing",
            "memory_strength": 90
        }
    ]

# Biến trạng thái cho tiến độ Daily Stream
if "stream_idx" not in st.session_state:
    st.session_state.stream_idx = 0

# Các biến trạng thái khác
if "learning_history" not in st.session_state:
    st.session_state.learning_history = {}
if "flashcard_index" not in st.session_state:
    st.session_state.flashcard_index = 0
if "show_answer" not in st.session_state:
    st.session_state.show_answer = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Đảm bảo tất cả từ hiện tại đều có record trong learning_history
for item in st.session_state.daily_words:
    w_key = item['word']
    if w_key not in st.session_state.learning_history:
        st.session_state.learning_history[w_key] = {
            "streak": 0, "reviews": 0, "last_reviewed": None, "status": item.get("status", "Learning")
        }

# ==========================================
# 3. AI HELPER FUNCTION
# ==========================================
def call_minimax_ai(prompt: str, system_prompt: str = "You are an expert AI English Tutor.", api_key: str = "", base_url: str = "https://openrouter.ai/api/v1") -> str:
    if not api_key:
        return "⚠️ Vui lòng nhập OpenRouter/MiniMax API Key ở thanh Sidebar bên trái để kích hoạt AI."
    try:
        client = OpenAI(base_url=base_url, api_key=api_key)
        response = client.chat.completions.create(
            model="minimax/minimax-m3:free",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            temperature=0.7, max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Lỗi kết nối AI API: {str(e)}"

# ==========================================
# 4. SIDEBAR & NAVIGATION
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/isometric-folders/100/book.png", width=60)
    st.title("VocabStream")
    st.caption("5 từ mỗi ngày – Nhớ sâu, không quên")
    st.markdown("---")
    
    st.subheader("🔑 Cấu hình AI Model")
    api_key_input = st.text_input("OpenRouter / MiniMax API Key:", type="password")
    base_url_input = st.text_input("Base URL:", value="https://openrouter.ai/api/v1")
    st.markdown("---")
    
    st.subheader("📌 Điều hướng")
    menu = st.radio(
        "Chọn màn hình:",
        [
            "🏠 Daily Stream (5 từ hôm nay)",
            "🎯 Ôn tập đa dạng (Practice)",
            "🤖 AI Tutor Assistant",
            "📊 Tiến độ & Gamification",
            "⚙️ Onboarding & Thiết lập"
        ]
    )
    st.markdown("---")
    st.markdown(f"🔥 **Streak:** <span class='badge-streak'>{st.session_state.user_profile['streak']} Ngày</span>", unsafe_allow_html=True)
    st.markdown(f"🏆 **Từ đã Master:** **{st.session_state.user_profile['total_mastered']} từ**")

# ==========================================
# 5. MÀN HÌNH 1: DAILY STREAM (HỌC DẠNG FLASHCARD CHUỖI)
# ==========================================
if menu == "🏠 Daily Stream (5 từ hôm nay)":
    st.markdown("<h1 class='main-header'>Daily Stream 📚</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Học từng từ một. Đọc kỹ nghĩa, mẹo nhớ và gõ lại từ để đi tiếp.</p>", unsafe_allow_html=True)
    
    col_btn1, col_btn2 = st.columns([3, 7])
    with col_btn1:
        if st.button("✨ AI Tạo Stream mới (5 từ)"):
            if api_key_input:
                with st.spinner("AI đang soạn 5 từ phù hợp nhất..."):
                    prompt = f"""Tạo danh sách 5 từ vựng tiếng Anh trình độ {st.session_state.user_profile['level']}, chủ đề {', '.join(st.session_state.user_profile['topics'])}.
                    Trả về JSON Array gồm 5 Object với các key: "word", "ipa", "vietnamese", "english_meaning", "examples" (mảng 2 câu), "collocations" (mảng 3 cụm), "mnemonic" (mẹo nhớ ngắn gọn tiếng Việt). Chỉ trả về JSON thuần."""
                    res = call_minimax_ai(prompt, api_key=api_key_input, base_url=base_url_input)
                    try:
                        clean_json = res.strip().strip("```json").strip("```").strip()
                        parsed_words = json.loads(clean_json)
                        for w in parsed_words:
                            w["status"], w["memory_strength"] = "Learning", 50
                            st.session_state.learning_history[w['word']] = {"streak": 0, "reviews": 0, "last_reviewed": None, "status": "Learning"}
                        st.session_state.daily_words = parsed_words
                        st.session_state.stream_idx = 0 # Reset quá trình học
                        st.success("Đã tạo thành công 5 từ mới từ MiniMax AI!")
                        st.rerun()
                    except Exception as e:
                        st.error("Lỗi khi đọc JSON từ AI. Vui lòng thử lại.")
            else:
                st.warning("Vui lòng nhập API Key ở sidebar để tạo từ mới.")

    st.markdown("---")

    # LOGIC FLASHCARD THÔNG MINH CHO DAILY STREAM
    total_words = len(st.session_state.daily_words)
    
    if st.session_state.stream_idx < total_words:
        idx = st.session_state.stream_idx
        current_word = st.session_state.daily_words[idx]
        
        # Thanh tiến độ
        progress_val = idx / total_words
        st.progress(progress_val)
        st.caption(f"Tiến độ hôm nay: Trải nghiệm từ {idx + 1} / {total_words}")
        
        # Thẻ hiển thị từ vựng (Front of Flashcard)
        st.markdown(f"""
        <div class='word-card'>
            <div class='word-title'>{current_word['word']}</div>
            <div class='ipa-text'>{current_word['ipa']}</div>
            <div class='meaning-text'>{current_word['vietnamese']}</div>
            <p style='color: #666; margin-top: 10px;'>{current_word['english_meaning']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Trình phát âm thanh (Iframe)
        st.write("🔊 **Nghe phát âm:**")
        sound_url = f"https://dict.youdao.com/dictvoice?audio={current_word['word']}&type=2"
        st.components.v1.iframe(src=sound_url, height=45, scrolling=False)
        
        # Mẹo nhớ và Ví dụ
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"<div class='mnemonic-box'>{current_word.get('mnemonic', '💡 Không có mẹo nhớ.')}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("**📝 Ví dụ thực tế:**")
            st.info(f"*{current_word['examples'][0]}*")
        
        st.markdown("---")
        
        # YÊU CẦU THỰC HÀNH (Trả lời để đi tiếp)
        st.subheader("✍️ Thực hành ghi nhớ cách viết")
        user_typing = st.text_input(f"Hãy gõ lại từ vựng vào ô bên dưới để chuyển sang từ tiếp theo:", placeholder="Nhập từ tiếng Anh...", key=f"stream_input_{idx}")
        
        if st.button("Kiểm tra & Tiếp tục ➡️", key=f"stream_btn_{idx}"):
            if user_typing.strip().lower() == current_word['word'].lower():
                st.session_state.stream_idx += 1
                st.rerun()
            else:
                st.error(f"❌ Sai chính tả. Hãy nhìn kỹ từ '{current_word['word']}' và gõ lại nhé!")
                
    else:
        # Khi đã học xong cả 5 từ
        st.progress(1.0)
        st.success("🎉 TUYỆT VỜI! Bạn đã hoàn thành Stream 5 từ vựng của ngày hôm nay.")
        st.balloons()
        
        if st.button("🔄 Học lại từ đầu (Review)"):
            st.session_state.stream_idx = 0
            st.rerun()

# ==========================================
# 6. MÀN HÌNH 2: HỆ THỐNG ÔN TẬP ĐA DẠNG
# ==========================================
elif menu == "🎯 Ôn tập đa dạng (Practice)":
    st.markdown("<h1 class='main-header'>Hệ Thống Ôn Tập Đa Dạng 🎯</h1>", unsafe_allow_html=True)
    
    words = st.session_state.daily_words
    tabs = st.tabs(["🃏 Flashcard", "⌨️ Typed Recall", "📝 Fill-in-the-blank", "🔘 Multiple Choice", "📖 Story Mode", "🎭 Situation Quiz", "🗣️ Speaking"])
    
    # 1. Flashcard (Fixed logic)
    with tabs[0]:
        st.subheader("🃏 Flashcard Nhắc Lại")
        if len(words) > 0:
            current_idx = st.session_state.flashcard_index % len(words)
            current_word = words[current_idx]
            word_str = current_word['word']
            
            st.markdown("<div class='flashcard-box'>", unsafe_allow_html=True)
            if not st.session_state.show_answer:
                st.markdown(f"## ❓ {current_word['vietnamese']}")
                st.caption("Hãy tự nhớ lại từ tiếng Anh tương ứng...")
            else:
                st.markdown(f"# 🔤 {current_word['word']} <span style='font-size: 1.2rem; color: gray;'>{current_word['ipa']}</span>", unsafe_allow_html=True)
                st.markdown(f"**Nghĩa Việt:** {current_word['vietnamese']}")
            st.markdown("</div>", unsafe_allow_html=True)

            if not st.session_state.show_answer:
                if st.button("👀 Hiện Mặt Sau", use_container_width=True):
                    st.session_state.show_answer = True
                    st.rerun()
            else:
                col1, col2, col3 = st.columns(3)
                if col1.button("🔴 Quên / Khó"):
                    st.session_state.show_answer = False
                    st.session_state.flashcard_index += 1
                    st.rerun()
                if col2.button("🟡 Quen thuộc"):
                    st.session_state.show_answer = False
                    st.session_state.flashcard_index += 1
                    st.rerun()
                if col3.button("🟢 Nhớ rất rõ"):
                    st.session_state.show_answer = False
                    st.session_state.flashcard_index += 1
                    st.rerun()

    # (Các tab còn lại giữ nguyên như bản chuẩn)
    with tabs[1]:
        st.subheader("⌨️ Typed Recall")
        target_w = words[st.session_state.flashcard_index % len(words)]
        st.write(f"Định nghĩa: **{target_w['english_meaning']}**")
        ans = st.text_input("Nhập từ tiếng Anh:", key="typed_recall")
        if st.button("Kiểm tra", key="btn_typed"):
            if ans.strip().lower() == target_w['word'].lower():
                st.success("🎉 Chính xác!")
            else:
                st.error(f"❌ Đáp án là: {target_w['word']}")
                
    with tabs[2]:
        st.subheader("📝 Điền từ vào chỗ trống")
        target_w = words[0]
        masked = target_w['examples'][0].replace(target_w['word'], "___").replace(target_w['word'].lower(), "___")
        st.markdown(f"**Câu:** {masked}")
        ans2 = st.text_input("Từ còn thiếu?", key="fill_blank")
        if st.button("Kiểm tra", key="btn_fill"):
            if target_w['word'].lower() in ans2.strip().lower():
                st.success("🎉 Xuất sắc!")
            else:
                st.error(f"❌ Đáp án đúng là: {target_w['word']}")

    with tabs[3]:
        st.subheader("🔘 Trắc nghiệm nhanh")
        q_word = words[1]
        options = [q_word['vietnamese']] + [w['vietnamese'] for w in words if w['word'] != q_word['word']][:3]
        random.shuffle(options)
        st.markdown(f"Từ **'{q_word['word']}'** có nghĩa là gì?")
        choice = st.radio("Chọn:", options, key="mc_choice")
        if st.button("Gửi đáp án", key="btn_mc"):
            if choice == q_word['vietnamese']:
                st.success("✅ Đúng rồi!")
            else:
                st.error(f"❌ Khái niệm đúng phải là: {q_word['vietnamese']}")

    with tabs[4]:
        st.subheader("📖 Story Mode (AI)")
        if st.button("🎬 Tạo đoạn văn với 5 từ hôm nay"):
            if api_key_input:
                word_list = ", ".join([w['word'] for w in words])
                prompt = f"Viết một đoạn văn ngắn tiếng Anh lồng ghép 5 từ: {word_list}. Bôi đen 5 từ đó và kèm dịch nghĩa tiếng Việt."
                with st.spinner("AI đang tạo..."):
                    story = call_minimax_ai(prompt, api_key=api_key_input, base_url=base_url_input)
                    st.markdown(story)
            else:
                st.warning("Vui lòng nhập API Key ở sidebar.")

    with tabs[5]:
        st.subheader("🎭 Tình huống thực tế")
        st.write("Bạn cần đưa ra giải pháp giảm thiểu tối đa rủi ro thiệt hại. Chọn hành động nào?")
        sit = st.selectbox("Chọn:", ["Pragmatic approach to mitigate risk", "Lucid dream", "Foster the problem"])
        if st.button("Kiểm tra tình huống"):
            if "mitigate risk" in sit:
                st.success("🎯 Chính xác!")
            else:
                st.info("💡 Hãy thử lại.")

    with tabs[6]:
        st.subheader("🗣️ Luyện phát âm")
        spk_w = words[0]
        st.markdown(f"Đọc to: **'{spk_w['examples'][0]}'**")
        sp_text = st.text_input("Văn bản câu bạn vừa đọc:")
        if st.button("🤖 AI Chấm điểm"):
            if api_key_input and sp_text:
                prompt = f"So sánh câu gốc: '{spk_w['examples'][0]}' và câu người đọc: '{sp_text}'. Đánh giá điểm /100."
                with st.spinner("Đang chấm..."):
                    st.markdown(call_minimax_ai(prompt, api_key=api_key_input, base_url=base_url_input))
            else:
                st.warning("Nhập API Key và nội dung đã đọc.")

# ==========================================
# 7. MÀN HÌNH 3: AI TUTOR ASSISTANT
# ==========================================
elif menu == "🤖 AI Tutor Assistant":
    st.markdown("<h1 class='main-header'>AI Tutor Assistant 🤖</h1>", unsafe_allow_html=True)
    
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if user_prompt := st.chat_input("Hỏi AI (VD: Phân biệt Resilient và Tough...)"):
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.write(user_prompt)

        with st.chat_message("assistant"):
            if api_key_input:
                with st.spinner("AI đang phản hồi..."):
                    reply = call_minimax_ai(user_prompt, api_key=api_key_input, base_url=base_url_input)
                    st.write(reply)
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
            else:
                st.warning("Cung cấp API Key ở Sidebar để chat với AI.")

# ==========================================
# 8 & 9. TIẾN ĐỘ & ONBOARDING (Giữ nguyên)
# ==========================================
elif menu == "📊 Tiến độ & Gamification":
    st.markdown("<h1 class='main-header'>Tiến Độ Học Tập 📊</h1>", unsafe_allow_html=True)
    st.write("*(Chức năng biểu đồ và huy hiệu)*")

elif menu == "⚙️ Onboarding & Thiết lập":
    st.markdown("<h1 class='main-header'>Thiết Lập Lộ Trình ⚙️</h1>", unsafe_allow_html=True)
    st.write("*(Chức năng cài đặt)*")
