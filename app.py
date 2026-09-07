import streamlit as st
import json
import random
import datetime
import pandas as pd
import urllib.parse
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
    .srs-box {
        background-color: #E3F2FD;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        border-left: 4px solid #1976D2;
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

if "stream_idx" not in st.session_state:
    st.session_state.stream_idx = 0

if "learning_history" not in st.session_state:
    st.session_state.learning_history = {}

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "review_active" not in st.session_state:
    st.session_state.review_active = False
if "review_mode" not in st.session_state:
    st.session_state.review_mode = None
if "review_word" not in st.session_state:
    st.session_state.review_word = None
if "review_answered" not in st.session_state:
    st.session_state.review_answered = False
if "review_user_ans" not in st.session_state:
    st.session_state.review_user_ans = ""

for item in st.session_state.daily_words:
    w_key = item['word']
    if w_key not in st.session_state.learning_history:
        st.session_state.learning_history[w_key] = {
            "streak": 0, 
            "reviews": 0, 
            "last_reviewed": None, 
            "status": item.get("status", "Learning")
        }

def get_srs_schedule(streak):
    if streak == 0:
        return "🔴 Hôm nay (Cần ôn ngay)", 0
    elif streak == 1:
        return "🟡 1 ngày sau", 1
    elif streak == 2:
        return "🟢 3 ngày sau", 3
    elif streak >= 3:
        return f"🟢 {streak * 2} ngày sau", streak * 2
    return "🔴 Hôm nay", 0

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
# 5. MÀN HÌNH 1: DAILY STREAM
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
                        st.session_state.stream_idx = 0
                        st.success("Đã tạo thành công 5 từ mới từ MiniMax AI!")
                        st.rerun()
                    except Exception as e:
                        st.error("Lỗi khi đọc JSON từ AI. Vui lòng thử lại.")
            else:
                st.warning("Vui lòng nhập API Key ở sidebar để tạo từ mới.")

    st.markdown("---")

    total_words = len(st.session_state.daily_words)
    if st.session_state.stream_idx < total_words:
        idx = st.session_state.stream_idx
        current_word = st.session_state.daily_words[idx]
        
        st.progress(idx / total_words)
        st.caption(f"Tiến độ hôm nay: Trải nghiệm từ {idx + 1} / {total_words}")
        
        st.markdown(f"""
        <div class='word-card'>
            <div class='word-title'>{current_word['word']}</div>
            <div class='ipa-text'>{current_word['ipa']}</div>
            <div class='meaning-text'>{current_word['vietnamese']}</div>
            <p style='color: #666; margin-top: 10px;'>{current_word['english_meaning']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("🔊 **Nghe phát âm:**")
        sound_url = f"https://dict.youdao.com/dictvoice?audio={current_word['word']}&type=2"
        st.iframe(src=sound_url, height=45)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"<div class='mnemonic-box'>{current_word.get('mnemonic', '💡 Không có mẹo nhớ.')}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("**📝 Ví dụ thực tế:**")
            st.info(f"*{current_word['examples'][0]}*")
        
        st.markdown("---")
        st.subheader("✍️ Thực hành ghi nhớ cách viết")
        user_typing = st.text_input("Hãy gõ lại từ vựng vào ô bên dưới để chuyển sang từ tiếp theo:", placeholder="Nhập từ tiếng Anh...", key=f"stream_input_{idx}")
        
        if st.button("Kiểm tra & Tiếp tục ➡️", key=f"stream_btn_{idx}"):
            if user_typing.strip().lower() == current_word['word'].lower():
                st.session_state.stream_idx += 1
                st.rerun()
            else:
                st.error(f"❌ Sai chính tả. Hãy nhìn kỹ từ '{current_word['word']}' và gõ lại nhé!")
    else:
        st.progress(1.0)
        st.success("🎉 TUYỆT VỜI! Bạn đã hoàn thành Stream 5 từ vựng của ngày hôm nay.")
        st.balloons()
        if st.button("🔄 Học lại từ đầu (Review)"):
            st.session_state.stream_idx = 0
            st.rerun()

# ==========================================
# 6. MÀN HÌNH 2: ÔN TẬP ĐA DẠNG
# ==========================================
elif menu == "🎯 Ôn tập đa dạng (Practice)":
    st.markdown("<h1 class='main-header'>Hệ Thống Ôn Tập SRS Đa Dạng 🎯</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Hệ thống tự động tính lịch ôn tập (Spaced Repetition) và kiểm tra phản xạ ngẫu nhiên.</p>", unsafe_allow_html=True)

    st.subheader("📅 Lịch ôn tập & Thời gian đến lần tiếp theo")
    for w in st.session_state.daily_words:
        w_hist = st.session_state.learning_history.get(w['word'], {"streak": 0})
        schedule_text, _ = get_srs_schedule(w_hist['streak'])
        st.markdown(f"""
        <div class='srs-box'>
            <b>🔤 {w['word']}</b> ({w['vietnamese']}) &nbsp;|&nbsp; 🔥 Streak: <b>{w_hist['streak']}</b> &nbsp;|&nbsp; ⏰ Lần ôn tiếp theo: <b>{schedule_text}</b>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    if not st.session_state.review_active:
        if st.button("🚀 Bắt đầu phiên ôn tập ngẫu nhiên", use_container_width=True):
            st.session_state.review_active = True
            st.session_state.review_answered = False
            st.session_state.review_word = random.choice(st.session_state.daily_words)
            st.session_state.review_mode = random.choice(["Flashcard", "Typed Recall", "Fill-in", "Multiple Choice"])
            st.rerun()
    else:
        w = st.session_state.review_word
        mode = st.session_state.review_mode
        
        st.info(f"⚡ **Dạng bài kiểm tra ngẫu nhiên:** `{mode}`")
        
        if mode == "Flashcard":
            st.markdown("<div class='flashcard-box'>", unsafe_allow_html=True)
            st.markdown(f"## ❓ Nghĩa Việt: {w['vietnamese']}")
            st.caption("Hãy nhớ lại từ tiếng Anh tương ứng...")
            st.markdown("</div>", unsafe_allow_html=True)
            
            if not st.session_state.review_answered:
                if st.button("👀 Xem đáp án & Đánh giá"):
                    st.session_state.review_answered = True
                    st.rerun()
            else:
                st.success(f"Đáp án đúng: **{w['word']}** ({w['ipa']}) - *{w['english_meaning']}*")

        elif mode == "Typed Recall":
            st.write(f"Định nghĩa: **{w['english_meaning']}** (Nghĩa Việt: *{w['vietnamese']}*)")
            ans = st.text_input("Nhập chính xác từ tiếng Anh:", key="rand_typed")
            if not st.session_state.review_answered:
                if st.button("Kiểm tra đáp án"):
                    st.session_state.review_user_ans = ans
                    st.session_state.review_answered = True
                    st.rerun()
            else:
                if st.session_state.review_user_ans.strip().lower() == w['word'].lower():
                    st.success("🎉 Chính xác tuyệt đối!")
                else:
                    st.error(f"❌ Chưa chính xác. Đáp án đúng là: **{w['word']}**")

        elif mode == "Fill-in":
            masked = w['examples'][0].replace(w['word'], "_____").replace(w['word'].lower(), "_____")
            st.markdown(f"**Câu hoàn chỉnh:** {masked}")
            ans_fill = st.text_input("Điền từ vào chỗ trống:", key="rand_fill")
            if not st.session_state.review_answered:
                if st.button("Kiểm tra điền từ"):
                    st.session_state.review_user_ans = ans_fill
                    st.session_state.review_answered = True
                    st.rerun()
            else:
                if w['word'].lower() in st.session_state.review_user_ans.strip().lower():
                    st.success("🎉 Chính xác ngữ cảnh!")
                else:
                    st.error(f"❌ Sai rồi. Từ đúng phải là: **{w['word']}**")

        elif mode == "Multiple Choice":
            options = [w['vietnamese']] + [item['vietnamese'] for item in st.session_state.daily_words if item['word'] != w['word']][:3]
            random.shuffle(options)
            st.markdown(f"Từ **'{w['word']}'** có nghĩa tiếng Việt là gì?")
            choice = st.radio("Chọn đáp án:", options, key="rand_mc")
            if not st.session_state.review_answered:
                if st.button("Gửi đáp án trắc nghiệm"):
                    st.session_state.review_user_ans = choice
                    st.session_state.review_answered = True
                    st.rerun()
            else:
                if st.session_state.review_user_ans == w['vietnamese']:
                    st.success("✅ Chính xác!")
                else:
                    st.error(f"❌ Sai rồi. Nghĩa đúng là: **{w['vietnamese']}**")

        # TỰ ĐỘNG ĐỌC CẢ TỪ TIẾNG ANH LẪN NGHĨA TIẾNG VIỆT QUA st.iframe DATA URI
        if st.session_state.review_answered:
            st.markdown("---")
            st.markdown(f"🔊 **Đang tự động đọc từ & nghĩa:** *{w['word']}* — *{w['vietnamese']}*")
            
            tts_code = f"""
            <script>
                function speakWord() {{
                    if ('speechSynthesis' in window) {{
                        window.speechSynthesis.cancel();
                        
                        let utteranceEn = new SpeechSynthesisUtterance("{w['word']}");
                        utteranceEn.lang = 'en-US';
                        utteranceEn.rate = 0.9;
                        
                        utteranceEn.onend = function() {{
                            let utteranceVi = new SpeechSynthesisUtterance("{w['vietnamese']}");
                            utteranceVi.lang = 'vi-VN';
                            utteranceVi.rate = 1.0;
                            
                            let voices = window.speechSynthesis.getVoices();
                            let viVoice = voices.find(v => v.lang.toLowerCase().includes('vi') || v.lang.toLowerCase().includes('viet'));
                            if (viVoice) {{
                                utteranceVi.voice = viVoice;
                            }}
                            
                            window.speechSynthesis.speak(utteranceVi);
                        }};
                        
                        window.speechSynthesis.speak(utteranceEn);
                    }}
                }}
                
                if (window.speechSynthesis.getVoices().length > 0) {{
                    speakWord();
                }} else {{
                    window.speechSynthesis.onvoiceschanged = speakWord;
                    speakWord();
                }}
            </script>
            """
            
            encoded_html = urllib.parse.quote(tts_code)
            data_uri = f"data:text/html;charset=utf-8,{encoded_html}"
            st.iframe(src=data_uri, height=0)
            
            col_next, col_stop = st.columns(2)
            with col_next:
                if st.button("➡️ Câu hỏi ngẫu nhiên tiếp theo"):
                    hist = st.session_state.learning_history.setdefault(w['word'], {"streak": 0})
                    hist['streak'] += 1
                    hist['reviews'] += 1
                    hist['last_reviewed'] = datetime.date.today().isoformat()
                    
                    st.session_state.review_answered = False
                    st.session_state.review_word = random.choice(st.session_state.daily_words)
                    st.session_state.review_mode = random.choice(["Flashcard", "Typed Recall", "Fill-in", "Multiple Choice"])
                    st.rerun()
            with col_stop:
                if st.button("⏹️ Kết thúc phiên ôn tập"):
                    st.session_state.review_active = False
                    st.session_state.review_answered = False
                    st.rerun()

# ==========================================
# 7. MÀN HÌNH 3: AI TUTOR ASSISTANT
# ==========================================
elif menu == "🤖 AI Tutor Assistant":
    st.markdown("<h1 class='main-header'>AI Tutor Assistant 🤖</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Trợ lý AI thông minh sẵn sàng giải đáp ngữ pháp, phân biệt từ vựng hoặc tạo ngữ cảnh giao tiếp cho bạn.</p>", unsafe_allow_html=True)
    
    st.markdown("💡 **Gợi ý câu hỏi nhanh:**")
    q_col1, q_col2, q_col3 = st.columns(3)
    if q_col1.button("🔍 Phân biệt các từ vựng hôm nay"):
        st.session_state.chat_history.append({"role": "user", "content": "Hãy giúp tôi phân biệt các từ vựng trong Daily Stream hôm nay một cách dễ hiểu nhất."})
    if q_col2.button("✍️ Viết đoạn văn chêm từ"):
        st.session_state.chat_history.append({"role": "user", "content": "Hãy viết một đoạn hội thoại ngắn tiếng Anh sử dụng các từ vựng hiện tại và dịch nghĩa."})
    if q_col3.button("🎯 Mẹo ghi nhớ lâu"):
        st.session_state.chat_history.append({"role": "user", "content": "Chia sẻ cho tôi phương pháp ghi nhớ từ vựng tiếng Anh theo ngữ cảnh hiệu quả nhất."})
        
    st.markdown("---")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if user_prompt := st.chat_input("Hỏi AI bất cứ điều gì về tiếng Anh..."):
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.write(user_prompt)

        with st.chat_message("assistant"):
            if api_key_input:
                with st.spinner("AI đang tư duy và phản hồi..."):
                    reply = call_minimax_ai(user_prompt, api_key=api_key_input, base_url=base_url_input)
                    st.write(reply)
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
            else:
                st.warning("⚠️ Vui lòng cấu hình OpenRouter / MiniMax API Key ở Sidebar bên trái để trò chuyện với AI.")

# ==========================================
# 8. MÀN HÌNH 4: TIẾN ĐỘ & GAMIFICATION
# ==========================================
elif menu == "📊 Tiến độ & Gamification":
    st.markdown("<h1 class='main-header'>Tiến Độ Học Tập & Thống Kê 📊</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Theo dõi hành trình chinh phục từ vựng và các thành tích cá nhân của bạn.</p>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔥 Chuỗi Streak", f"{st.session_state.user_profile['streak']} Ngày", "+1 hôm nay")
    col2.metric("🏆 Tổng từ đã Master", f"{st.session_state.user_profile['total_mastered']} Từ", "+5 từ mới")
    col3.metric("🧠 Retention Rate", f"{st.session_state.user_profile['retention_rate']}%", "+3% hiệu suất")
    col4.metric("⏱️ Thời gian học", f"{st.session_state.user_profile['daily_minutes']} phút/ngày", "Mục tiêu đạt chuẩn")
    
    st.markdown("---")
    
    st.subheader("📈 Biểu đồ ghi nhớ từ vựng qua các tuần")
    chart_data = pd.DataFrame(
        {"Số từ đã ghi nhớ": [10, 15, 22, 28, 35, 42, 50]},
        index=["Tuần 1", "Tuần 2", "Tuần 3", "Tuần 4", "Tuần 5", "Tuần 6", "Tuần này"]
    )
    st.line_chart(chart_data)
    
    st.markdown("---")
    st.subheader("🏅 Bộ sưu tập huy hiệu thành tựu")
    b_col1, b_col2, b_col3 = st.columns(3)
    b_col1.success("🌟 **Chăm chỉ 5 ngày**\nHoàn thành streak 5 ngày liên tục không gián đoạn.")
    b_col2.success("🧠 **Siêu trí nhớ từ vựng**\nĐạt tỷ lệ ghi nhớ (Retention Rate) trên 85%.")
    b_col3.info("🚀 **Nhà thám hiểm AI**\nSử dụng thành công tính năng tạo từ vựng thông minh qua MiniMax AI.")

# ==========================================
# 9. MÀN HÌNH 5: ONBOARDING & THIẾT LẬP
# ==========================================
elif menu == "⚙️ Onboarding & Thiết lập":
    st.markdown("<h1 class='main-header'>Thiết Lập Lộ Trình & Cá Nhân Hóa ⚙️</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Tùy chỉnh mục tiêu học tập, trình độ và các chủ đề yêu thích để hệ thống tinh chỉnh từ vựng phù hợp nhất.</p>", unsafe_allow_html=True)
    
    with st.form("settings_form"):
        goal = st.selectbox("🎯 Mục tiêu chính:", ["IELTS 6.5+", "Giao tiếp công sở", "Du lịch & Cuộc sống", "Luyện thi TOEIC"], index=0)
        level = st.selectbox("📊 Trình độ hiện tại:", ["A2", "B1", "B2", "C1"], index=1)
        topics = st.multiselect("📚 Chủ đề quan tâm:", ["Technology", "Business", "Environment", "Science", "Lifestyle", "Education"], default=["Technology", "Business"])
        daily_min = st.slider("⏱️ Thời gian học mục tiêu mỗi ngày (phút):", 5, 30, 10)
        
        submitted = st.form_submit_button("💾 Lưu thay đổi lộ trình")
        if submitted:
            st.session_state.user_profile["goal"] = goal
            st.session_state.user_profile["level"] = level
            st.session_state.user_profile["topics"] = topics
            st.session_state.user_profile["daily_minutes"] = daily_min
            st.success("🎉 Đã cập nhật thiết lập lộ trình thành công!")
            
    st.markdown("---")
    st.subheader("🛠️ Quản lý dữ liệu hệ thống")
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        if st.button("🗑️ Reset lịch sử học tập"):
            st.session_state.learning_history = {}
            st.success("Đã xóa sạch lịch sử SRS hiện tại.")
    with d_col2:
        if st.button("📥 Xuất dữ liệu từ vựng hiện tại (JSON)"):
            st.json(st.session_state.daily_words)import streamlit as st
import json
import random
import datetime
import pandas as pd
import urllib.parse
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
    .srs-box {
        background-color: #E3F2FD;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        border-left: 4px solid #1976D2;
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

if "stream_idx" not in st.session_state:
    st.session_state.stream_idx = 0

if "learning_history" not in st.session_state:
    st.session_state.learning_history = {}

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "review_active" not in st.session_state:
    st.session_state.review_active = False
if "review_mode" not in st.session_state:
    st.session_state.review_mode = None
if "review_word" not in st.session_state:
    st.session_state.review_word = None
if "review_answered" not in st.session_state:
    st.session_state.review_answered = False
if "review_user_ans" not in st.session_state:
    st.session_state.review_user_ans = ""

for item in st.session_state.daily_words:
    w_key = item['word']
    if w_key not in st.session_state.learning_history:
        st.session_state.learning_history[w_key] = {
            "streak": 0, 
            "reviews": 0, 
            "last_reviewed": None, 
            "status": item.get("status", "Learning")
        }

def get_srs_schedule(streak):
    if streak == 0:
        return "🔴 Hôm nay (Cần ôn ngay)", 0
    elif streak == 1:
        return "🟡 1 ngày sau", 1
    elif streak == 2:
        return "🟢 3 ngày sau", 3
    elif streak >= 3:
        return f"🟢 {streak * 2} ngày sau", streak * 2
    return "🔴 Hôm nay", 0

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
# 5. MÀN HÌNH 1: DAILY STREAM
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
                        st.session_state.stream_idx = 0
                        st.success("Đã tạo thành công 5 từ mới từ MiniMax AI!")
                        st.rerun()
                    except Exception as e:
                        st.error("Lỗi khi đọc JSON từ AI. Vui lòng thử lại.")
            else:
                st.warning("Vui lòng nhập API Key ở sidebar để tạo từ mới.")

    st.markdown("---")

    total_words = len(st.session_state.daily_words)
    if st.session_state.stream_idx < total_words:
        idx = st.session_state.stream_idx
        current_word = st.session_state.daily_words[idx]
        
        st.progress(idx / total_words)
        st.caption(f"Tiến độ hôm nay: Trải nghiệm từ {idx + 1} / {total_words}")
        
        st.markdown(f"""
        <div class='word-card'>
            <div class='word-title'>{current_word['word']}</div>
            <div class='ipa-text'>{current_word['ipa']}</div>
            <div class='meaning-text'>{current_word['vietnamese']}</div>
            <p style='color: #666; margin-top: 10px;'>{current_word['english_meaning']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("🔊 **Nghe phát âm:**")
        sound_url = f"https://dict.youdao.com/dictvoice?audio={current_word['word']}&type=2"
        st.iframe(src=sound_url, height=45)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"<div class='mnemonic-box'>{current_word.get('mnemonic', '💡 Không có mẹo nhớ.')}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("**📝 Ví dụ thực tế:**")
            st.info(f"*{current_word['examples'][0]}*")
        
        st.markdown("---")
        st.subheader("✍️ Thực hành ghi nhớ cách viết")
        user_typing = st.text_input("Hãy gõ lại từ vựng vào ô bên dưới để chuyển sang từ tiếp theo:", placeholder="Nhập từ tiếng Anh...", key=f"stream_input_{idx}")
        
        if st.button("Kiểm tra & Tiếp tục ➡️", key=f"stream_btn_{idx}"):
            if user_typing.strip().lower() == current_word['word'].lower():
                st.session_state.stream_idx += 1
                st.rerun()
            else:
                st.error(f"❌ Sai chính tả. Hãy nhìn kỹ từ '{current_word['word']}' và gõ lại nhé!")
    else:
        st.progress(1.0)
        st.success("🎉 TUYỆT VỜI! Bạn đã hoàn thành Stream 5 từ vựng của ngày hôm nay.")
        st.balloons()
        if st.button("🔄 Học lại từ đầu (Review)"):
            st.session_state.stream_idx = 0
            st.rerun()

# ==========================================
# 6. MÀN HÌNH 2: ÔN TẬP ĐA DẠNG
# ==========================================
elif menu == "🎯 Ôn tập đa dạng (Practice)":
    st.markdown("<h1 class='main-header'>Hệ Thống Ôn Tập SRS Đa Dạng 🎯</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Hệ thống tự động tính lịch ôn tập (Spaced Repetition) và kiểm tra phản xạ ngẫu nhiên.</p>", unsafe_allow_html=True)

    st.subheader("📅 Lịch ôn tập & Thời gian đến lần tiếp theo")
    for w in st.session_state.daily_words:
        w_hist = st.session_state.learning_history.get(w['word'], {"streak": 0})
        schedule_text, _ = get_srs_schedule(w_hist['streak'])
        st.markdown(f"""
        <div class='srs-box'>
            <b>🔤 {w['word']}</b> ({w['vietnamese']}) &nbsp;|&nbsp; 🔥 Streak: <b>{w_hist['streak']}</b> &nbsp;|&nbsp; ⏰ Lần ôn tiếp theo: <b>{schedule_text}</b>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    if not st.session_state.review_active:
        if st.button("🚀 Bắt đầu phiên ôn tập ngẫu nhiên", use_container_width=True):
            st.session_state.review_active = True
            st.session_state.review_answered = False
            st.session_state.review_word = random.choice(st.session_state.daily_words)
            st.session_state.review_mode = random.choice(["Flashcard", "Typed Recall", "Fill-in", "Multiple Choice"])
            st.rerun()
    else:
        w = st.session_state.review_word
        mode = st.session_state.review_mode
        
        st.info(f"⚡ **Dạng bài kiểm tra ngẫu nhiên:** `{mode}`")
        
        if mode == "Flashcard":
            st.markdown("<div class='flashcard-box'>", unsafe_allow_html=True)
            st.markdown(f"## ❓ Nghĩa Việt: {w['vietnamese']}")
            st.caption("Hãy nhớ lại từ tiếng Anh tương ứng...")
            st.markdown("</div>", unsafe_allow_html=True)
            
            if not st.session_state.review_answered:
                if st.button("👀 Xem đáp án & Đánh giá"):
                    st.session_state.review_answered = True
                    st.rerun()
            else:
                st.success(f"Đáp án đúng: **{w['word']}** ({w['ipa']}) - *{w['english_meaning']}*")

        elif mode == "Typed Recall":
            st.write(f"Định nghĩa: **{w['english_meaning']}** (Nghĩa Việt: *{w['vietnamese']}*)")
            ans = st.text_input("Nhập chính xác từ tiếng Anh:", key="rand_typed")
            if not st.session_state.review_answered:
                if st.button("Kiểm tra đáp án"):
                    st.session_state.review_user_ans = ans
                    st.session_state.review_answered = True
                    st.rerun()
            else:
                if st.session_state.review_user_ans.strip().lower() == w['word'].lower():
                    st.success("🎉 Chính xác tuyệt đối!")
                else:
                    st.error(f"❌ Chưa chính xác. Đáp án đúng là: **{w['word']}**")

        elif mode == "Fill-in":
            masked = w['examples'][0].replace(w['word'], "_____").replace(w['word'].lower(), "_____")
            st.markdown(f"**Câu hoàn chỉnh:** {masked}")
            ans_fill = st.text_input("Điền từ vào chỗ trống:", key="rand_fill")
            if not st.session_state.review_answered:
                if st.button("Kiểm tra điền từ"):
                    st.session_state.review_user_ans = ans_fill
                    st.session_state.review_answered = True
                    st.rerun()
            else:
                if w['word'].lower() in st.session_state.review_user_ans.strip().lower():
                    st.success("🎉 Chính xác ngữ cảnh!")
                else:
                    st.error(f"❌ Sai rồi. Từ đúng phải là: **{w['word']}**")

        elif mode == "Multiple Choice":
            options = [w['vietnamese']] + [item['vietnamese'] for item in st.session_state.daily_words if item['word'] != w['word']][:3]
            random.shuffle(options)
            st.markdown(f"Từ **'{w['word']}'** có nghĩa tiếng Việt là gì?")
            choice = st.radio("Chọn đáp án:", options, key="rand_mc")
            if not st.session_state.review_answered:
                if st.button("Gửi đáp án trắc nghiệm"):
                    st.session_state.review_user_ans = choice
                    st.session_state.review_answered = True
                    st.rerun()
            else:
                if st.session_state.review_user_ans == w['vietnamese']:
                    st.success("✅ Chính xác!")
                else:
                    st.error(f"❌ Sai rồi. Nghĩa đúng là: **{w['vietnamese']}**")

        # TỰ ĐỘNG ĐỌC CẢ TỪ TIẾNG ANH LẪN NGHĨA TIẾNG VIỆT QUA st.iframe DATA URI
        if st.session_state.review_answered:
            st.markdown("---")
            st.markdown(f"🔊 **Đang tự động đọc từ & nghĩa:** *{w['word']}* — *{w['vietnamese']}*")
            
            tts_code = f"""
            <script>
                function speakWord() {{
                    if ('speechSynthesis' in window) {{
                        window.speechSynthesis.cancel();
                        
                        let utteranceEn = new SpeechSynthesisUtterance("{w['word']}");
                        utteranceEn.lang = 'en-US';
                        utteranceEn.rate = 0.9;
                        
                        utteranceEn.onend = function() {{
                            let utteranceVi = new SpeechSynthesisUtterance("{w['vietnamese']}");
                            utteranceVi.lang = 'vi-VN';
                            utteranceVi.rate = 1.0;
                            
                            let voices = window.speechSynthesis.getVoices();
                            let viVoice = voices.find(v => v.lang.toLowerCase().includes('vi') || v.lang.toLowerCase().includes('viet'));
                            if (viVoice) {{
                                utteranceVi.voice = viVoice;
                            }}
                            
                            window.speechSynthesis.speak(utteranceVi);
                        }};
                        
                        window.speechSynthesis.speak(utteranceEn);
                    }}
                }}
                
                if (window.speechSynthesis.getVoices().length > 0) {{
                    speakWord();
                }} else {{
                    window.speechSynthesis.onvoiceschanged = speakWord;
                    speakWord();
                }}
            </script>
            """
            
            encoded_html = urllib.parse.quote(tts_code)
            data_uri = f"data:text/html;charset=utf-8,{encoded_html}"
            st.iframe(src=data_uri, height=0)
            
            col_next, col_stop = st.columns(2)
            with col_next:
                if st.button("➡️ Câu hỏi ngẫu nhiên tiếp theo"):
                    hist = st.session_state.learning_history.setdefault(w['word'], {"streak": 0})
                    hist['streak'] += 1
                    hist['reviews'] += 1
                    hist['last_reviewed'] = datetime.date.today().isoformat()
                    
                    st.session_state.review_answered = False
                    st.session_state.review_word = random.choice(st.session_state.daily_words)
                    st.session_state.review_mode = random.choice(["Flashcard", "Typed Recall", "Fill-in", "Multiple Choice"])
                    st.rerun()
            with col_stop:
                if st.button("⏹️ Kết thúc phiên ôn tập"):
                    st.session_state.review_active = False
                    st.session_state.review_answered = False
                    st.rerun()

# ==========================================
# 7. MÀN HÌNH 3: AI TUTOR ASSISTANT
# ==========================================
elif menu == "🤖 AI Tutor Assistant":
    st.markdown("<h1 class='main-header'>AI Tutor Assistant 🤖</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Trợ lý AI thông minh sẵn sàng giải đáp ngữ pháp, phân biệt từ vựng hoặc tạo ngữ cảnh giao tiếp cho bạn.</p>", unsafe_allow_html=True)
    
    st.markdown("💡 **Gợi ý câu hỏi nhanh:**")
    q_col1, q_col2, q_col3 = st.columns(3)
    if q_col1.button("🔍 Phân biệt các từ vựng hôm nay"):
        st.session_state.chat_history.append({"role": "user", "content": "Hãy giúp tôi phân biệt các từ vựng trong Daily Stream hôm nay một cách dễ hiểu nhất."})
    if q_col2.button("✍️ Viết đoạn văn chêm từ"):
        st.session_state.chat_history.append({"role": "user", "content": "Hãy viết một đoạn hội thoại ngắn tiếng Anh sử dụng các từ vựng hiện tại và dịch nghĩa."})
    if q_col3.button("🎯 Mẹo ghi nhớ lâu"):
        st.session_state.chat_history.append({"role": "user", "content": "Chia sẻ cho tôi phương pháp ghi nhớ từ vựng tiếng Anh theo ngữ cảnh hiệu quả nhất."})
        
    st.markdown("---")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if user_prompt := st.chat_input("Hỏi AI bất cứ điều gì về tiếng Anh..."):
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.write(user_prompt)

        with st.chat_message("assistant"):
            if api_key_input:
                with st.spinner("AI đang tư duy và phản hồi..."):
                    reply = call_minimax_ai(user_prompt, api_key=api_key_input, base_url=base_url_input)
                    st.write(reply)
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
            else:
                st.warning("⚠️ Vui lòng cấu hình OpenRouter / MiniMax API Key ở Sidebar bên trái để trò chuyện với AI.")

# ==========================================
# 8. MÀN HÌNH 4: TIẾN ĐỘ & GAMIFICATION
# ==========================================
elif menu == "📊 Tiến độ & Gamification":
    st.markdown("<h1 class='main-header'>Tiến Độ Học Tập & Thống Kê 📊</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Theo dõi hành trình chinh phục từ vựng và các thành tích cá nhân của bạn.</p>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔥 Chuỗi Streak", f"{st.session_state.user_profile['streak']} Ngày", "+1 hôm nay")
    col2.metric("🏆 Tổng từ đã Master", f"{st.session_state.user_profile['total_mastered']} Từ", "+5 từ mới")
    col3.metric("🧠 Retention Rate", f"{st.session_state.user_profile['retention_rate']}%", "+3% hiệu suất")
    col4.metric("⏱️ Thời gian học", f"{st.session_state.user_profile['daily_minutes']} phút/ngày", "Mục tiêu đạt chuẩn")
    
    st.markdown("---")
    
    st.subheader("📈 Biểu đồ ghi nhớ từ vựng qua các tuần")
    chart_data = pd.DataFrame(
        {"Số từ đã ghi nhớ": [10, 15, 22, 28, 35, 42, 50]},
        index=["Tuần 1", "Tuần 2", "Tuần 3", "Tuần 4", "Tuần 5", "Tuần 6", "Tuần này"]
    )
    st.line_chart(chart_data)
    
    st.markdown("---")
    st.subheader("🏅 Bộ sưu tập huy hiệu thành tựu")
    b_col1, b_col2, b_col3 = st.columns(3)
    b_col1.success("🌟 **Chăm chỉ 5 ngày**\nHoàn thành streak 5 ngày liên tục không gián đoạn.")
    b_col2.success("🧠 **Siêu trí nhớ từ vựng**\nĐạt tỷ lệ ghi nhớ (Retention Rate) trên 85%.")
    b_col3.info("🚀 **Nhà thám hiểm AI**\nSử dụng thành công tính năng tạo từ vựng thông minh qua MiniMax AI.")

# ==========================================
# 9. MÀN HÌNH 5: ONBOARDING & THIẾT LẬP
# ==========================================
elif menu == "⚙️ Onboarding & Thiết lập":
    st.markdown("<h1 class='main-header'>Thiết Lập Lộ Trình & Cá Nhân Hóa ⚙️</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Tùy chỉnh mục tiêu học tập, trình độ và các chủ đề yêu thích để hệ thống tinh chỉnh từ vựng phù hợp nhất.</p>", unsafe_allow_html=True)
    
    with st.form("settings_form"):
        goal = st.selectbox("🎯 Mục tiêu chính:", ["IELTS 6.5+", "Giao tiếp công sở", "Du lịch & Cuộc sống", "Luyện thi TOEIC"], index=0)
        level = st.selectbox("📊 Trình độ hiện tại:", ["A2", "B1", "B2", "C1"], index=1)
        topics = st.multiselect("📚 Chủ đề quan tâm:", ["Technology", "Business", "Environment", "Science", "Lifestyle", "Education"], default=["Technology", "Business"])
        daily_min = st.slider("⏱️ Thời gian học mục tiêu mỗi ngày (phút):", 5, 30, 10)
        
        submitted = st.form_submit_button("💾 Lưu thay đổi lộ trình")
        if submitted:
            st.session_state.user_profile["goal"] = goal
            st.session_state.user_profile["level"] = level
            st.session_state.user_profile["topics"] = topics
            st.session_state.user_profile["daily_minutes"] = daily_min
            st.success("🎉 Đã cập nhật thiết lập lộ trình thành công!")
            
    st.markdown("---")
    st.subheader("🛠️ Quản lý dữ liệu hệ thống")
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        if st.button("🗑️ Reset lịch sử học tập"):
            st.session_state.learning_history = {}
            st.success("Đã xóa sạch lịch sử SRS hiện tại.")
    with d_col2:
        if st.button("📥 Xuất dữ liệu từ vựng hiện tại (JSON)"):
            st.json(st.session_state.daily_words)
