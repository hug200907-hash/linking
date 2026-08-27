import streamlit as st
import requests
import time

st.set_page_config(page_title="Đồng bộ 2 Thiết Bị", page_icon="🔄", layout="wide")

st.title("🔄 Đồng bộ dữ liệu Real-time (Zero-Config)")
st.caption("Ứng dụng chạy ngay không cần cấu hình. Nhập cùng mã 3 số trên 2 máy để kết nối.")

# Sử dụng Firebase Realtime DB mở (Hỗ trợ REST API trực tiếp, tốc độ < 0.1s, không bao giờ chặn IP)
FIREBASE_BASE_URL = "https://streamlit-sync-default-rtdb.asia-southeast1.firebasedatabase.app"

# --- BƯỚC 1: NHẬP MÃ ĐỒNG BỘ ---
col_k1, col_k2 = st.columns([2, 1])
with col_k1:
    sync_key = st.text_input("🔑 Nhập mã đồng bộ (3 chữ số):", max_chars=3, placeholder="123")

if len(sync_key) != 3 or not sync_key.isdigit():
    st.info("💡 Vui lòng nhập đúng 3 chữ số để bắt đầu kết nối (Ví dụ: 888, 123).")
    st.stop()

# Đường dẫn URL lưu trữ dữ liệu theo mã 3 số
ROOM_URL = f"{FIREBASE_BASE_URL}/rooms/{sync_key}.json"

st.success(f"⚡ Đã kết nối vào kênh đồng bộ: **{sync_key}**")

# Nút bật/tắt Tự động cập nhật
col_auto1, col_auto2 = st.columns([1, 3])
with col_auto1:
    auto_refresh = st.checkbox("🔄 Auto-refresh (Tự cập nhật)", value=True)
with col_auto2:
    refresh_rate = st.slider("Tần số cập nhật (giây):", min_value=1, max_value=5, value=2)

st.divider()

# Hàm lấy dữ liệu
def get_remote_data():
    try:
        res = requests.get(ROOM_URL, timeout=3)
        if res.status_code == 200 and res.json():
            data = res.json()
            if isinstance(data, dict):
                return data.get("text", "")
    except Exception:
        pass
    return ""

# Hàm gửi dữ liệu
def push_remote_data(content):
    payload = {
        "text": content,
        "updated_at": time.time()
    }
    try:
        # Sử dụng PUT để ghi đè dữ liệu trực tiếp vào đúng node room
        res = requests.put(ROOM_URL, json=payload, timeout=5)
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
            st.error("Lỗi khi gửi dữ liệu!")

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
