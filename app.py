import streamlit as st
import requests
import time

st.set_page_config(page_title="Đồng bộ 2 Thiết Bị", page_icon="🔄", layout="wide")

st.title("🔄 Đồng bộ dữ liệu Real-time (Zero-Config)")
st.caption("Chỉ cần 2 thiết bị nhập chung Mã 3 chữ số là dữ liệu tự động đồng bộ!")

# --- BƯỚC 1: NHẬP MÃ ĐỒNG BỘ ---
col_k1, col_k2 = st.columns([2, 1])
with col_k1:
    sync_key = st.text_input("🔑 Nhập mã đồng bộ (3 chữ số):", max_chars=3, placeholder="123")

if len(sync_key) != 3 or not sync_key.isdigit():
    st.info("💡 Vui lòng nhập đúng 3 chữ số để bắt đầu kết nối (Ví dụ: 888, 123).")
    st.stop()

# Sử dụng API public của KVdb.io (Tự động tạo namespace theo key 3 số, không cần API Key)
API_URL = f"https://kvdb.io/st_sync_app_demo_key_{sync_key}/shared_data"

st.success(f"⚡ Đã kết nối vào kênh đồng bộ: **{sync_key}**")

# Các nút điều khiển chế độ Tự động cập nhật
col_auto1, col_auto2 = st.columns([1, 3])
with col_auto1:
    auto_refresh = st.checkbox("🔄 Auto-refresh (Tự cập nhật)", value=True)
with col_auto2:
    refresh_rate = st.slider("Tần số cập nhật (giây):", min_value=1, max_value=5, value=2)

st.divider()

# Hàm lấy dữ liệu từ server public
def get_remote_data():
    try:
        res = requests.get(API_URL, timeout=3)
        if res.status_code == 200:
            return res.text
    except Exception:
        pass
    return ""

# Hàm gửi dữ liệu lên server public
def push_remote_data(content):
    try:
        res = requests.post(API_URL, data=content.encode('utf-8'), timeout=3)
        return res.status_code in [200, 201]
    except Exception:
        return False

# --- BƯỚC 2: GIAO DIỆN CHÍNH ---
col_send, col_receive = st.columns(2)

# Đọc dữ liệu hiện tại từ server
current_remote_text = get_remote_data()

with col_send:
    st.subheader("📤 Bên Gửi / Chỉnh sửa")
    user_input = st.text_area("Nhập nội dung cần truyền:", value=current_remote_text, height=180)
    
    if st.button("🚀 Gửi & Đồng bộ", use_container_width=True, type="primary"):
        if push_remote_data(user_input):
            st.toast("✅ Đã gửi dữ liệu thành công!", icon="🚀")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("Lỗi khi gửi dữ liệu, vui lòng thử lại!")

with col_receive:
    st.subheader("📥 Dữ liệu nhận được (Real-time)")
    
    # Hiển thị dữ liệu trong khung
    if current_remote_text:
        st.text_area("Nội dung từ thiết bị kia:", value=current_remote_text, height=180, disabled=True)
    else:
        st.info("Chưa có dữ liệu nào trong mã kết nối này.")

# --- BƯỚC 3: TỰ ĐỘNG CẬP NHẬT DỮ LIỆU (AUTO-REFRESH) ---
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
