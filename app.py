import streamlit as st
import requests
import time

st.set_page_config(page_title="Đồng bộ 2 Thiết Bị", page_icon="🔄")

# Lấy Firebase Realtime Database URL từ secrets hoặc nhập tay
# URL có dạng: https://your-project-id-default-rtdb.firebaseio.com/
FIREBASE_URL = st.secrets.get("FIREBASE_URL", "")

st.title("🔄 Đồng bộ dữ liệu 2 thiết bị (Key 3 số)")

if not FIREBASE_URL:
    FIREBASE_URL = st.sidebar.text_input("Nhập Firebase Realtime DB URL:", type="password")
    if not FIREBASE_URL:
        st.warning("Vui lòng cấu hình `FIREBASE_URL` trong secrets.toml hoặc nhập ở thanh bên.")
        st.stop()

# Đảm bảo URL kết thúc đúng định dạng Firebase REST API
if not FIREBASE_URL.endswith("/"):
    FIREBASE_URL += "/"

# --- BƯỚC 1: NHẬP MÃ ĐỒNG BỘ ---
col_key1, col_key2 = st.columns([2, 1])
with col_key1:
    sync_key = st.text_input("🔑 Nhập mã đồng bộ (3 chữ số):", max_chars=3, placeholder="123")

if len(sync_key) != 3 or not sync_key.isdigit():
    st.info("💡 Vui lòng nhập đúng 3 chữ số để bắt đầu kết nối (Ví dụ: 888, 123).")
    st.stop()

# Endpoint dữ liệu dựa trên key 3 số
db_endpoint = f"{FIREBASE_URL}sync_rooms/{sync_key}.json"

st.success(f"⚡ Đã kết nối vào phòng đồng bộ: **{sync_key}**")
st.divider()

# --- BƯỚC 2: GIAO DIỆN GỬI & NHẬN DỮ LIỆU ---
col_send, col_receive = st.columns(2)

# Funkton lấy dữ liệu hiện tại
def fetch_data():
    try:
        response = requests.get(db_endpoint)
        if response.status_code == 200 and response.json():
            return response.json().get("content", "")
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
    return ""

# --- CỘT 1: GỬI DỮ LIỆU ---
with col_send:
    st.subheader("📤 Gửi dữ liệu đi")
    current_data = fetch_data()
    
    input_text = st.text_area("Nhập nội dung cần đồng bộ:", value=current_data, height=150)
    
    if st.button("🚀 Đồng bộ ngay", use_container_width=True):
        payload = {
            "content": input_text,
            "updated_at": time.time()
        }
        res = requests.put(db_endpoint, json=payload)
        if res.status_code == 200:
            st.toast("Đã gửi dữ liệu thành công!", icon="✅")
            st.rerun()
        else:
            st.error("Gửi dữ liệu thất bại!")

# --- CỘT 2: NHẬN DỮ LIỆU REAL-TIME ---
with col_receive:
    st.subheader("📥 Dữ liệu nhận được")
    
    live_data = fetch_data()
    st.info(live_data if live_data else "Chưa có dữ liệu nào trong phòng này.")
    
    if st.button("🔄 Cập nhật thủ công", use_container_width=True):
        st.rerun()
