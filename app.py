import streamlit as st
import requests
import time

st.set_page_config(page_title="Đồng bộ 2 Thiết Bị", page_icon="🔄", layout="wide")

st.title("🔄 Đồng bộ dữ liệu Real-time (Zero-Config)")
st.caption("Ứng dụng chạy ngay không cần cấu hình. Nhập cùng mã 3 số trên 2 máy để kết nối.")

# --- BƯỚC 1: NHẬP MÃ ĐỒNG BỘ ---
col_k1, col_k2 = st.columns([2, 1])
with col_k1:
    sync_key = st.text_input("🔑 Nhập mã đồng bộ (3 chữ số):", max_chars=3, placeholder="123")

if len(sync_key) != 3 or not sync_key.isdigit():
    st.info("💡 Vui lòng nhập đúng 3 chữ số để bắt đầu kết nối (Ví dụ: 888, 123).")
    st.stop()

# Đổi sang endpoint API cực kỳ ổn định hỗ trợ CORS & Public Write
API_URL = f"https://api.restful-api.dev/objects/sync_app_key_{sync_key}"

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
        res = requests.get(API_URL, timeout=3)
        if res.status_code == 200:
            data = res.json()
            # Kiểm tra định dạng dữ liệu trả về từ API
            if isinstance(data, dict) and "data" in data:
                return data["data"].get("content", "")
    except Exception:
        pass
    return ""

# Hàm gửi dữ liệu (Kết hợp PUT & POST tự động khởi tạo nếu chưa có)
def push_remote_data(content):
    payload = {
        "name": f"Room_{sync_key}",
        "data": {
            "content": content,
            "updated_at": time.time()
        }
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        # Thử ghi đè dữ liệu (PUT)
        res = requests.put(API_URL, json=payload, headers=headers, timeout=5)
        if res.status_code in [200, 201]:
            return True
            
        # Nếu chưa tồn tại, tiến hành tạo mới (POST)
        res_post = requests.post("https://api.restful-api.dev/objects", json={"id": f"sync_app_key_{sync_key}", **payload}, headers=headers, timeout=5)
        if res_post.status_code in [200, 201]:
            return True
    except Exception as e:
        st.warning(f"Lỗi kết nối mạng: {e}")
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
            st.error("Lỗi khi gửi dữ liệu, vui lòng kiểm tra kết nối mạng!")

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
