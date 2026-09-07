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
        padding: 20px;
        border-left: 5px solid #1E88E5;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .word-title {
        font-size: 1.8rem;
        font-weight: bold;
        color: #0D47A1;
    }
    .ipa-text {
        font-size: 1.1rem;
        color: #E65100;
        font-style: italic;
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
            "examples": [
                "The local economy is remarkably resilient despite global turbulence.",
                "She showed a resilient spirit during her job search."
            ],
            "collocations": ["resilient economy", "highly resilient", "resilient nature"],
            "mnemonic": "Gợi nhớ: 'Re' (Lại) + 'Silient' (im lặng âm thầm vượt qua mọi sóng gió) -> Kiên cường.",
            "status": "Learning",
            "memory_strength": 75
        },
        {
            "word": "Foster",
            "ipa": "/ˈfɒs.tər/",
            "vietnamese": "Nuôi dưỡng, thúc đẩy",
            "english_meaning": "Encourage or promote the development of something.",
            "examples": [
                "The teacher aims to foster a creative environment in the classroom.",
                "Good leaders foster teamwork and trust."
            ],
            "collocations": ["foster innovation", "foster collaboration", "foster growth"],
            "mnemonic": "Gợi nhớ: 'FOSter' phát âm gần như 'Phở' -> Ăn phở để nuôi dưỡng cơ thể.",
            "status": "Learning",
            "memory_strength": 60
        },
        {
            "word": "Pragmatic",
            "ipa": "/præɡˈmæt.ɪk/",
            "vietnamese": "Thực tế, thực dụng",
            "english_meaning": "Dealing with things sensibly and realistically based on practical considerations.",
            "examples": [
                "We need a pragmatic approach to solving this budget issue.",
                "He made a pragmatic decision to accept the offer."
            ],
            "collocations": ["pragmatic approach", "pragmatic solution", "pragmatic view"],
            "mnemonic": "Gợi nhớ: 'Prag' gần giống 'Practice' (Thực hành) -> Hướng tới thực tế.",
            "status": "Reviewing",
            "memory_strength": 85
        },
        {
            "word": "Lucid",
            "ipa": "/ˈluː.sɪd/",
            "vietnamese": "Rõ ràng, minh mẫn",
            "english_meaning": "Expressed clearly; easy to understand.",
            "examples": [
                "She gave a lucid explanation of a complex scientific theory.",
                "He remained lucid and alert throughout his speech."
            ],
            "collocations": ["lucid explanation", "lucid dream", "lucid thinking"],
            "mnemonic": "Gợi nhớ: 'Lucid' nghe như 'Lúc đi' -> Lúc đi học tư duy luôn sáng suốt, rõ ràng.",
            "status": "Learning",
            "memory_strength": 50
        },
        {
            "word": "Mitigate",
            "ipa": "/ˈmɪt.ɪ.ɡeɪt/",
            "vietnamese": "Giảm nhẹ, làm dịu",
            "english_meaning": "Make less severe, serious, or painful.",
            "examples": [
                "New safety measures were introduced to mitigate risks.",
                "Planting trees helps mitigate the impacts of climate change."
            ],
            "collocations": ["mitigate risk", "mitigate impact", "mitigate damage"],
            "mnemonic": "Gợi nhớ: 'Miti' -> Mi-ni (nhỏ lại) + 'gate' (cổng) -> Thu nhỏ cổng để giảm thiểu rủi ro.",
            "status": "Reviewing",
            "memory_strength": 90
        }
    ]

# Khởi tạo an toàn cho lịch sử học tập & trạng thái Flashcard để tránh KeyError
if "learning_history" not in st.session_state:
    st.session_state.learning_history = {}

if "flashcard_index" not in st.session_state:
    st.session_state.flashcard_index = 0

if "show_answer" not in st.session_state:
    st.session_state.show_answer = False

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "notes" not in st.session_state:
    st.session_state.notes = {}

# Đảm bảo tất cả từ hiện tại đều có record trong learning_history
for item in st.session_state.daily_words:
    w_key = item['word']
    if w_key not in st.session_state.learning_history:
        st.session_state.learning_history[w_key] = {
            "streak": 0,
            "reviews": 0,
            "last_reviewed": None,
            "status": item.get("status", "Learning")
        }

# ==========================================
# 3. AI HELPER FUNCTION (MINIMAX/MINIMAX-M3:FREE)
# ==========================================
def call_minimax_ai(prompt: str, system_prompt: str = "You are an expert AI English Tutor.", api_key: str = "", base_url: str = "https://openrouter.ai/api/v1") -> str:
    """Gọi API mô hình minimax/minimax-m3:free thông qua OpenAI client format"""
    if not api_key:
        return "⚠️ Vui lòng nhập OpenRouter/MiniMax API Key ở thanh Sidebar bên trái để kích hoạt AI."
    
    try:
        client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        response = client.chat.completions.create(
            model="minimax/minimax-m3:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
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
    
    # Cấu hình AI API
    st.subheader("🔑 Cấu hình AI Model")
    api_key_input = st.text_input("OpenRouter / MiniMax API Key:", type="password", help="Nhập API Key để dùng model minimax/minimax-m3:free")
    base_url_input = st.text_input("Base URL:", value="https://openrouter.ai/api/v1")
    
    st.markdown("---")
    
    # Navigation Menu
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
    # Quick Stats Widget
    st.markdown(f"🔥 **Streak:** <span class='badge-streak'>{st.session_state.user_profile['streak']} Ngày</span>", unsafe_allow_html=True)
    st.markdown(f"🏆 **Từ đã Master:** **{st.session_state.user_profile['total_mastered']} từ**")
    st.markdown(f"📈 **Tỷ lệ ghi nhớ:** **{st.session_state.user_profile['retention_rate']}%**")

# ==========================================
# 5. MÀN HÌNH 1: DAILY STREAM (5 TỪ MỖI NGÀY)
# ==========================================
if menu == "🏠 Daily Stream (5 từ hôm nay)":
    st.markdown("<h1 class='main-header'>Daily Stream 📚</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Học ít – Nhớ sâu. Dưới đây là 5 từ vựng tối ưu cho hôm nay dựa trên mục tiêu của bạn.</p>", unsafe_allow_html=True)
    
    col_btn1, col_btn2 = st.columns([3, 7])
    with col_btn1:
        if st.button("✨ AI Tạo Stream mới (5 từ)"):
            if api_key_input:
                with st.spinner("AI đang soạn 5 từ phù hợp nhất..."):
                    prompt = f"""
                    Tạo danh sách 5 từ vựng tiếng Anh theo tiêu chí:
                    - Trình độ: {st.session_state.user_profile['level']}
                    - Mục tiêu: {st.session_state.user_profile['goal']}
                    - Chủ đề: {', '.join(st.session_state.user_profile['topics'])}
                    Trả về định dạng JSON duy nhất là một Array gồm 5 Object với các key chính xác sau:
                    "word", "ipa", "vietnamese", "english_meaning", "examples" (mảng 2 câu), "collocations" (mảng 3 cụm), "mnemonic" (mẹo nhớ).
                    Chỉ trả về JSON thuần, không chèn markdown hay văn bản ngoài.
                    """
                    res = call_minimax_ai(prompt, api_key=api_key_input, base_url=base_url_input)
                    try:
                        clean_json = res.strip().strip("```json").strip("```").strip()
                        parsed_words = json.loads(clean_json)
                        for w in parsed_words:
                            w["status"] = "Learning"
                            w["memory_strength"] = 50
                            st.session_state.learning_history[w['word']] = {
                                "streak": 0, "reviews": 0, "last_reviewed": None, "status": "Learning"
                            }
                        st.session_state.daily_words = parsed_words
                        st.success("Đã tạo thành công 5 từ mới từ MiniMax AI!")
                        st.rerun()
                    except Exception as e:
                        st.error("Lỗi khi đọc phản hồi JSON từ AI. Vui lòng thử lại.")
            else:
                st.warning("Vui lòng nhập API Key ở sidebar để tạo từ mới bằng AI.")

    # Hiển thị danh sách 5 từ
    for idx, item in enumerate(st.session_state.daily_words):
        with st.container():
            st.markdown(f"""
            <div class='word-card'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span class='word-title'>{idx+1}. {item['word']}</span>
                    <span class='ipa-text'>{item['ipa']}</span>
                </div>
                <p><b>Nghĩa Việt:</b> <span style='color: #2E7D32; font-weight: bold;'>{item['vietnamese']}</span></p>
                <p><b>English Meaning:</b> {item['english_meaning']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Audio Stream Simulator (st.iframe thay cho st.html)
            sound_url = f"https://dict.youdao.com/dictvoice?audio={item['word']}&type=2"
            st.components.v1.iframe(src=sound_url, height=40, scrolling=False)
            
            # Chi tiết mở rộng
            with st.expander(f"🔍 Xem ví dụ, Collocations & Mnemonic cho '{item['word']}'"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**📝 Câu ví dụ:**")
                    for ex in item.get('examples', []):
                        st.markdown(f"- *{ex}*")
                    
                    st.markdown("**🔗 Collocations quan trọng:**")
                    for col in item.get('collocations', []):
                        st.markdown(f"- `{col}`")
                
                with col_b:
                    st.markdown("**💡 Mnemonic (Gợi nhớ):**")
                    st.info(item.get('mnemonic', 'Không có mẹo nhớ.'))
                    
                    # Thêm ghi chú cá nhân
                    current_note = st.session_state.notes.get(item['word'], "")
                    user_note = st.text_input("📝 Ghi chú cá nhân:", value=current_note, key=f"input_{item['word']}")
                    if user_note != current_note:
                        st.session_state.notes[item['word']] = user_note
                        st.toast(f"Đã lưu ghi chú cho từ {item['word']}!")

            # Action Buttons
            c1, c2, c3 = st.columns([2, 2, 6])
            with c1:
                if st.button(f"✅ Quen rồi", key=f"easy_{idx}"):
                    item['status'] = "Mastered"
                    item['memory_strength'] = min(100, item['memory_strength'] + 20)
                    st.toast(f"Đã đánh dấu '{item['word']}' là Mastered!")
            with c2:
                if st.button(f"🔴 Khó nhớ", key=f"hard_{idx}"):
                    item['status'] = "Reviewing"
                    item['memory_strength'] = max(20, item['memory_strength'] - 15)
                    st.toast(f"Đã thêm '{item['word']}' vào danh sách cần ôn gấp!")

            st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 6. MÀN HÌNH 2: HỆ THỐNG ÔN TẬP ĐA DẠNG (FIX KEYERROR 'STREAK')
# ==========================================
elif menu == "🎯 Ôn tập đa dạng (Practice)":
    st.markdown("<h1 class='main-header'>Hệ Thống Ôn Tập Đa Dạng 🎯</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Học theo nguyên lý Spaced Repetition (SRS) với các chế độ ôn tập chủ động.</p>", unsafe_allow_html=True)

    words = st.session_state.daily_words
    
    tabs = st.tabs([
        "🃏 Flashcard", 
        "⌨️ Typed Recall", 
        "📝 Fill-in-the-blank", 
        "🔘 Multiple Choice", 
        "📖 Story Mode (AI)", 
        "🎭 Situation Quiz",
        "🗣️ Speaking Practice"
    ])
    
    # 1. Flashcard (Fixed logic & KeyError)
    with tabs[0]:
        st.subheader("🃏 Flashcard Thông Minh")
        if len(words) > 0:
            current_idx = st.session_state.flashcard_index % len(words)
            current_word = words[current_idx]
            word_str = current_word['word']
            
            # Cập nhật an toàn vào learning_history nếu từ chưa tồn tại
            if word_str not in st.session_state.learning_history:
                st.session_state.learning_history[word_str] = {
                    "streak": 0, "reviews": 0, "last_reviewed": None, "status": "Learning"
                }

            # Mặt trước / Mặt sau Flashcard
            st.markdown("<div class='flashcard-box'>", unsafe_allow_html=True)
            if not st.session_state.show_answer:
                st.markdown(f"## ❓ {current_word['vietnamese']}")
                st.caption("Hãy tự nhớ lại từ tiếng Anh tương ứng...")
            else:
                st.markdown(f"# 🔤 {current_word['word']} <span style='font-size: 1.2rem; color: gray;'>{current_word['ipa']}</span>", unsafe_allow_html=True)
                st.markdown(f"**Nghĩa Việt:** {current_word['vietnamese']}")
                st.markdown(f"**English:** {current_word['english_meaning']}")
                st.markdown(f"*Ví dụ:* {current_word['examples'][0]}")
            st.markdown("</div>", unsafe_allow_html=True)

            # Control buttons
            if not st.session_state.show_answer:
                if st.button("👀 Hiện Mặt Sau (Xem đáp án)", use_container_width=True):
                    st.session_state.show_answer = True
                    st.rerun()
            else:
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("🔴 Quên / Khó"):
                        hist = st.session_state.learning_history.setdefault(word_str, {})
                        hist['streak'] = 0
                        hist['reviews'] = hist.get('reviews', 0) + 1
                        hist['last_reviewed'] = datetime.date.today().isoformat()
                        
                        st.session_state.show_answer = False
                        st.session_state.flashcard_index += 1
                        st.rerun()

                with col2:
                    if st.button("🟡 Quen thuộc"):
                        hist = st.session_state.learning_history.setdefault(word_str, {})
                        hist['streak'] = hist.get('streak', 0) + 1
                        hist['reviews'] = hist.get('reviews', 0) + 1
                        hist['last_reviewed'] = datetime.date.today().isoformat()
                        
                        st.session_state.show_answer = False
                        st.session_state.flashcard_index += 1
                        st.rerun()

                with col3:
                    if st.button("🟢 Nhớ rất rõ"):
                        hist = st.session_state.learning_history.setdefault(word_str, {})
                        hist['streak'] = hist.get('streak', 0) + 1
                        hist['reviews'] = hist.get('reviews', 0) + 1
                        hist['last_reviewed'] = datetime.date.today().isoformat()
                        
                        st.session_state.show_answer = False
                        st.session_state.flashcard_index += 1
                        st.rerun()

    # 2. Typed Recall
    with tabs[1]:
        st.subheader("⌨️ Typed Recall (Chủ động gõ từ)")
        target_w = words[st.session_state.flashcard_index % len(words)]
        st.write(f"Định nghĩa: **{target_w['english_meaning']}** (Nghĩa Việt: *{target_w['vietnamese']}*)")
        user_input = st.text_input("Nhập chính xác từ tiếng Anh:", key="typed_recall_input")
        if st.button("Kiểm tra gõ từ"):
            if user_input.strip().lower() == target_w['word'].lower():
                st.success("🎉 Chính xác! Bạn đã ghi nhớ từ này rất chuẩn.")
            else:
                st.error(f"❌ Sai rồi. Đáp án đúng là: **{target_w['word']}**")

    # 3. Fill-in-the-blank
    with tabs[2]:
        st.subheader("📝 Điền từ vào chỗ trống")
        target_w = words[0]
        example_sentence = target_w['examples'][0]
        masked_sentence = example_sentence.replace(target_w['word'], "_______").replace(target_w['word'].lower(), "_______")
        
        st.markdown(f"**Câu:** {masked_sentence}")
        ans = st.text_input("Từ còn thiếu là gì?", key="fill_blank_input")
        if st.button("Kiểm tra đáp án"):
            if target_w['word'].lower() in ans.strip().lower():
                st.success("🎉 Xuất sắc! Sử dụng đúng ngữ cảnh.")
            else:
                st.error(f"❌ Đáp án đúng là: **{target_w['word']}**")

    # 4. Multiple Choice
    with tabs[3]:
        st.subheader("🔘 Trắc nghiệm nhanh")
        q_word = words[1]
        options = [q_word['vietnamese']] + [w['vietnamese'] for w in words if w['word'] != q_word['word']][:3]
        random.shuffle(options)
        
        st.markdown(f"Từ **'{q_word['word']}'** có nghĩa là gì?")
        choice = st.radio("Chọn đáp án đúng:", options, key="mc_choice")
        if st.button("Gửi đáp án"):
            if choice == q_word['vietnamese']:
                st.success("✅ Đúng rồi!")
            else:
                st.error(f"❌ Khái niệm đúng phải là: {q_word['vietnamese']}")

    # 5. Story Mode (AI)
    with tabs[4]:
        st.subheader("📖 Story Mode (AI tạo câu chuyện)")
        st.write("AI sẽ tạo một câu chuyện ngắn kết nối cả 5 từ vựng hôm nay để giúp bạn nhớ theo ngữ cảnh liên hoàn.")
        if st.button("🎬 Tạo đoạn văn với 5 từ hôm nay (dùng MiniMax AI)"):
            if api_key_input:
                word_list = ", ".join([w['word'] for w in words])
                prompt = f"Viết một đoạn văn ngắn tiếng Anh (khoảng 80-120 từ) lồng ghép tự nhiên 5 từ vựng sau: {word_list}. Bôi đen (bold) 5 từ đó và kèm dịch nghĩa tiếng Việt bên dưới."
                with st.spinner("AI đang sáng tạo câu chuyện..."):
                    story = call_minimax_ai(prompt, api_key=api_key_input, base_url=base_url_input)
                    st.markdown(story)
            else:
                st.warning("Vui lòng nhập API Key ở thanh bên trái để sử dụng tính năng này.")

    # 6. Situation Quiz
    with tabs[5]:
        st.subheader("🎭 Tình huống thực tế")
        st.write("Bạn đang làm việc trong dự án công ty và đối mặt với khủng hoảng chi phí.")
        st.markdown("> *“Tình huống đòi hỏi bạn phải đưa ra giải pháp giảm thiểu tối đa rủi ro thiệt hại.”*")
        st.markdown("Bạn sẽ chọn hành động nào ứng với từ vựng đúng?")
        sit_choice = st.selectbox("Chọn hành động:", [
            "Pragmatic approach to mitigate risk",
            "Lucid dream to ignore reality",
            "Foster the problem"
        ])
        if st.button("Kiểm tra tình huống"):
            if "mitigate risk" in sit_choice:
                st.success("🎯 Chính xác! 'Mitigate risk' là giảm thiểu rủi ro trong kinh doanh.")
            else:
                st.info("💡 Hãy thử lại với hành động mang nghĩa giảm nhẹ rủi ro.")

    # 7. Speaking Practice
    with tabs[6]:
        st.subheader("🗣️ Luyện nói & Phát âm")
        spk_word = words[0]
        st.markdown(f"Đọc to câu sau: **'{spk_word['examples'][0]}'**")
        st.caption("Nhập nội dung bạn đã đọc vào bên dưới để AI kiểm tra và chấm điểm:")
        spoken_text = st.text_input("Văn bản câu bạn vừa đọc:")
        if st.button("🤖 AI Chấm điểm phát âm"):
            if api_key_input and spoken_text:
                prompt = f"So sánh câu gốc: '{spk_word['examples'][0]}' và câu người học đọc: '{spoken_text}'. Đánh giá điểm phát âm/độ chính xác trên thang 100 và góp ý sửa lỗi ngắn gọn."
                with st.spinner("AI đang chấm điểm..."):
                    feedback = call_minimax_ai(prompt, api_key=api_key_input, base_url=base_url_input)
                    st.markdown(feedback)
            else:
                st.warning("Nhập API Key và nội dung đã đọc để AI chấm điểm.")

# ==========================================
# 7. MÀN HÌNH 3: AI TUTOR ASSISTANT (MINIMAX-M3)
# ==========================================
elif menu == "🤖 AI Tutor Assistant":
    st.markdown("<h1 class='main-header'>AI Tutor Assistant 🤖</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Hỏi bất kỳ thắc mắc nào về từ vựng, ngữ pháp, ngữ cảnh sử dụng với model MiniMax-M3.</p>", unsafe_allow_html=True)

    # Hiển thị lịch sử chat
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if user_prompt := st.chat_input("Hỏi AI (VD: Phân biệt Resilient và Tough, Tạo thêm ví dụ cho từ Lucid...)"):
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.write(user_prompt)

        with st.chat_message("assistant"):
            if api_key_input:
                with st.spinner("AI đang phản hồi..."):
                    system_p = f"You are VocabStream AI Tutor, specialized in helping English learners (Target: {st.session_state.user_profile['goal']}). Give clear, friendly, and structured responses."
                    reply = call_minimax_ai(user_prompt, system_prompt=system_p, api_key=api_key_input, base_url=base_url_input)
                    st.write(reply)
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
            else:
                st.warning("Vui lòng cung cấp API Key ở Sidebar để chat với AI.")

# ==========================================
# 8. MÀN HÌNH 4: TIẾN ĐỘ & GAMIFICATION
# ==========================================
elif menu == "📊 Tiến độ & Gamification":
    st.markdown("<h1 class='main-header'>Tiến Độ Học Tập 📊</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Theo dõi chỉ số ghi nhớ dài hạn (Retention Rate) & Huy hiệu đạt được.</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("🔥 Chuỗi Streak", f"{st.session_state.user_profile['streak']} Ngày", "+1 ngày so với hôm qua")
    col2.metric("🏆 Tổng từ đã Master", f"{st.session_state.user_profile['total_mastered']} Từ", "+5 từ tuần này")
    col3.metric("🧠 Retention Rate", f"{st.session_state.user_profile['retention_rate']}%", "+2%")

    st.markdown("---")
    
    st.subheader("📊 Độ mạnh ký ức (Memory Strength) của 5 từ hôm nay")
    df_words = pd.DataFrame([
        {"Từ vựng": w["word"], "Chỉ số ghi nhớ (%)": w.get("memory_strength", 50), "Trạng thái": w.get("status", "Learning")}
        for w in st.session_state.daily_words
    ])
    st.bar_chart(df_words.set_index("Từ vựng")["Chỉ số ghi nhớ (%)"])

    st.markdown("---")
    st.subheader("🏅 Huy hiệu đạt được (Badges)")
    b1, b2, b3, b4 = st.columns(4)
    b1.info("🔥 **7-Day Streak**\n\nHọc liên tục 7 ngày")
    b2.info("🎯 **Master 50**\n\nThành thạo 50 từ")
    b3.info("⚡ **Perfect Week**\n\nHoàn thành 100% bài tập tuần")
    b4.success("🛡️ **Memory Guard**\n\nGiữ retention rate > 85%")

# ==========================================
# 9. MÀN HÌNH 5: ONBOARDING & CÁ NHÂN HÓA
# ==========================================
elif menu == "⚙️ Onboarding & Thiết lập":
    st.markdown("<h1 class='main-header'>Thiết Lập Lộ Trình Cá Nhân ⚙️</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Điều chỉnh mục tiêu và thời lượng học để AI tối ưu 5 từ vựng mỗi ngày.</p>", unsafe_allow_html=True)

    with st.form("onboarding_form"):
        goal = st.selectbox("1. Mục tiêu chính của bạn:", [
            "IELTS 6.5–7.5+", "TOEIC 700+", "Giao tiếp công việc", "Du lịch & Đời sống", "Chuyên ngành IT / Tech"
        ], index=0)
        
        level = st.select_slider("2. Trình độ hiện tại:", options=["A2", "B1", "B2", "C1"], value="B1")
        
        topics = st.multiselect("3. Chủ đề ưu tiên:", [
            "Technology", "Business & Finance", "Health & Lifestyle", "Academic & Science", "Daily Life", "Travel"
        ], default=["Technology", "Business & Finance"])
        
        daily_mins = st.radio("4. Thời gian học mỗi ngày:", [5, 10, 15], index=1, format_func=lambda x: f"{x} phút/ngày")

        submitted = st.form_submit_button("💾 Lưu cấu hình & Cập nhật lộ trình")
        if submitted:
            st.session_state.user_profile["goal"] = goal
            st.session_state.user_profile["level"] = level
            st.session_state.user_profile["topics"] = topics
            st.session_state.user_profile["daily_minutes"] = daily_mins
            st.success("Đã cập nhật hồ sơ cá nhân thành công! AI sẽ tạo lộ trình dựa trên cài đặt mới.")
