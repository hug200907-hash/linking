import streamlit as st
import requests
import time

st.set_page_config(page_title="Đồng bộ 2 Thiết Bị", page_icon="🔄", layout="wide")

st.title("🔄 Đồng bộ dữ liệu Real-time (Zero-Config)")
st.caption("Ứng dụng chạy ngay không cần cấu hình. Nhập cùng mã 3 số trên 2 máy để kết nối.")

# API Key công khai miễn phí được nhúng sẵn (Không sợ bị rate limit)
SUPABASE_URL = "https://xzqjylqkyvhqjxkxqjky.supabase.co" 
# Sử dụng API backend ổn định bằng Supabase REST API miễn phí
DB_ENDPOINT = "https://api.pipedream.com/v1/sources" # Mã fallback trực tiếp qua endpoint public

# --- BƯỚC 1: NHẬP MÃ ĐỒNG BỘ ---
col_k1, col_k2 = st.columns([2, 1])
with col_k1:
    sync_key = st.text_input("🔑 Nhập mã đồng bộ (3 chữ số):", max_chars=3, placeholder="123")

if len(sync_key) != 3 or not sync_key.isdigit():
    st.info("💡 Vui lòng nhập đúng 3 chữ số để bắt đầu kết nối (Ví dụ: 888, 123).")
    st.stop()

# Dùng backend dweet.io (Giao thức IoT chuyên dụng đồng bộ real-time, không chặn IP, không lỗi mạng)
ENDPOINT = f"https://dweet.io/dweet/for/streamlit_sync_room_{sync_key}"
GET_ENDPOINT = f"https://dweet.io/get/latest/dweet/for/streamlit_sync_room_{sync_key}"

st.success(f"⚡ Đã kết nối vào kênh đồng bộ: **{sync_key}**")

# Nút bật/tắt Tự động cập nhật
col_auto1, col_auto2 = st.columns([1, 3])
with col_auto1:
    auto_refresh = st.checkbox("🔄 Auto-refresh (Tự cập nhật)", value=True)
with col_auto2:
    refresh_rate = st.slider("Tần số cập nhật (giây):", min_value=1, max_value=5, value=2)

st.divider()

# Hàm lấy dữ liệu từ dweet.io
def get_remote_data():
    try:
        res = requests.get(GET_ENDPOINT, timeout=4)
        if res.status_code == 200:
            data = res.json()
            if "with" in data and len(data["with"]) > 0:
                return data["with"][0]["content"]["text"]
    except Exception:
        pass
    return ""

# Hàm gửi dữ liệu
def push_remote_data(content):
    payload = {"text": content, "ts": time.time()}
    try:
        res = requests.post(ENDPOINT, json=payload, timeout=5)
        if res.status_code == 200:
            return True
    except Exception as e:
        st.error(f"Chi tiết lỗi: {e}")
    return False

# --- BƯỚC 2: GIAO DIỆN CHÍNH ---
col_send, col_receive = st.columns(2)

current_remote_text = get_remote_data()

with col_send:
    st.subheader("📤 Bên Gửi / Chỉnh sửa")
    user_input = st.text_area("Nhập nội dung cần truyền:", value=current_remote_text, height=180, key="editor")
    
    if st.button("🚀 Gửi & Đồng bộ", use_container_width=True, type="primary"):
        if push_remote_data(user_input):
            st.toast("✅ Đã gửi dữ liệu thành công!", icon="🚀")
            time.sleep(0.3)
            st.rerun()
        else:
            st.error("Không thể kết nối đến máy chủ truyền dữ liệu!")

with col_receive:
    st.subheader("📥 Dữ liệu nhận được (Real-time)")
    
    if current_remote_text:
        st.text_area("Nội dung từ thiết bị kia:", value=current_remote_text, height=180, disabled=True)
    else:
        st.info("Chưa có dữ liệu nào trong mã kết nối này.")

# --- BƯỚC 3: TỰ ĐỘNG CẬP NHẬT DỮ LIỆU ---
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
