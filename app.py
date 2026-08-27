import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Đồng bộ P2P Realtime", page_icon="⚡", layout="wide")

st.title("⚡ Đồng bộ P2P Realtime (WebRTC + PeerJS)")
st.caption("Truyền dữ liệu trực tiếp 2 chiều giữa 2 trình duyệt mà không thông qua Database trung gian.")

# Tối ưu 1: Gợi ý hoặc nhập Room ID
col1, col2 = st.columns([3, 1])
with col1:
    sync_key = st.text_input("🔑 Nhập/Tạo Mã Đồng Bộ (Ví dụ: room-888):", value="room-888")
with col2:
    st.write("") # Căn chỉnh UI
    st.write("")
    if st.button("🎲 Tạo mã ngẫu nhiên"):
        import random
        sync_key = f"room-{random.randint(100, 999)}"

if not sync_key.strip():
    st.warning("⚠️ Vui lòng nhập mã phòng để bắt đầu.")
    st.stop()

# Mã HTML + JS đã được tinh chỉnh tối ưu
html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://unpkg.com/peerjs@1.5.2/dist/peerjs.min.js"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
        body {{ padding: 10px; background: transparent; }}
        
        .status-bar {{ 
            padding: 10px 15px; 
            border-radius: 6px; 
            font-weight: 600; 
            font-size: 14px; 
            margin-bottom: 15px; 
            background: #fff3cd; 
            color: #856404; 
            border: 1px solid #ffeeba;
            transition: all 0.3s ease;
        }}
        
        .container {{ display: flex; gap: 15px; }}
        .box {{ flex: 1; background: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .box h4 {{ margin-bottom: 10px; color: #333; display: flex; align-items: center; gap: 8px; }}
        
        textarea {{ 
            width: 100%; 
            height: 140px; 
            padding: 10px; 
            font-size: 14px; 
            border-radius: 6px; 
            border: 1px solid #ccc; 
            resize: vertical;
            outline: none;
            transition: border-color 0.2s;
        }}
        textarea:focus {{ border-color: #ff4b4b; }}
        textarea[readonly] {{ background-color: #f8f9fa; color: #495057; cursor: not-allowed; }}
    </style>
</head>
<body>

    <div id="status" class="status-bar">⏳ Đang kết nối tới máy chủ tín hiệu (Signaling Server)...</div>

    <div class="container">
        <div class="box">
            <h4>✏️ Nhập dữ liệu (Máy này)</h4>
            <textarea id="localText" placeholder="Gõ nội dung vào đây, máy bên kia sẽ nhận ngay lập tức..."></textarea>
        </div>
        
        <div class="box">
            <h4>📲 Dữ liệu nhận được (Máy đối phương)</h4>
            <textarea id="remoteText" readonly placeholder="Đang chờ dữ liệu từ máy đối phương..."></textarea>
        </div>
    </div>

    <script>
        const ROOM_ID = "st_p2p_v2_{sync_key.strip()}";
        const statusEl = document.getElementById('status');
        const localText = document.getElementById('localText');
        const remoteText = document.getElementById('remoteText');
        
        let peer = null;
        let conn = null;

        function updateStatus(text, type = 'warning') {{
            statusEl.innerText = text;
            if (type === 'success') {{
                statusEl.style.background = '#d4edda'; statusEl.style.color = '#155724'; statusEl.style.borderColor = '#c3e6cb';
            }} else if (type === 'error') {{
                statusEl.style.background = '#f8d7da'; statusEl.style.color = '#721c24'; statusEl.style.borderColor = '#f5c6cb';
            }} else {{
                statusEl.style.background = '#fff3cd'; statusEl.style.color = '#856404'; statusEl.style.borderColor = '#ffeeba';
            }}
        }}

        // Khởi tạo Peer làm Host trước
        function initPeer() {{
            peer = new Peer(ROOM_ID);

            peer.on('open', (id) => {{
                updateStatus("🟢 Đã mở phòng thành công! Hãy mở thiết bị 2 và nhập mã '" + "{sync_key.strip()}" + "' để ghép nối.");
            }});

            // Lắng nghe kết nối từ Client (Đối phương)
            peer.on('connection', (c) => {{
                conn = c;
                setupEvents();
            }});

            // Xử lý khi ID đã tồn tại -> Chuyển sang đóng vai Client kết nối vào Host
            peer.on('error', (err) => {{
                if (err.type === 'unavailable-id') {{
                    updateStatus("🔄 Đã tìm thấy Host, đang kết nối trực tiếp...");
                    peer.destroy(); // Hủy peer cũ
                    
                    // Tạo Peer mới với ID ngẫu nhiên để làm Client
                    peer = new Peer();
                    peer.on('open', () => {{
                        conn = peer.connect(ROOM_ID, {{ reliable: true }});
                        setupEvents();
                    }});
                }} else {{
                    updateStatus("❌ Lỗi PeerJS: " + err.type, 'error');
                }}
            }});
        }}

        function setupEvents() {{
            conn.on('open', () => {{
                updateStatus("✅ ĐÃ KẾT NỐI P2P THÀNH CÔNG! Bắt đầu gõ để đồng bộ tức thì.", 'success');
            }});

            // Tối ưu 2: Nhận dữ liệu Realtime khi bên kia đang gõ
            conn.on('data', (data) => {{
                remoteText.value = data;
            }});

            conn.on('close', () => {{
                updateStatus("⚠️ Kết nối P2P đã ngắt. Đang chờ kết nối lại...", 'error');
            }});
        }}

        // Tối ưu 3: Tự động truyền dữ liệu theo sự kiện 'input' (Realtime Sync)
        localText.addEventListener('input', (e) => {{
            const val = e.target.value;
            if (conn && conn.open) {{
                conn.send(val);
            }}
        }});

        // Khởi chạy
        initPeer();
    </script>
</body>
</html>
"""

components.html(html_code, height=270)
