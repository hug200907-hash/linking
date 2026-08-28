import random
import streamlit as st

st.set_page_config(page_title="Đồng bộ P2P Realtime", page_icon="⚡", layout="wide")

st.title("⚡ Đồng bộ P2P Realtime (WebRTC + PeerJS)")
st.caption("Truyền dữ liệu trực tiếp 2 chiều giữa 2 trình duyệt mà không thông qua Database trung gian.")

# Quản lý Room ID bằng session_state
if "p2p_room_id" not in st.session_state:
    st.session_state.p2p_room_id = "room-888"

col1, col2 = st.columns([3, 1])
with col1:
    user_input = st.text_input("🔑 Nhập/Tạo Mã Đồng Bộ (Ví dụ: room-888):", value=st.session_state.p2p_room_id)
    if user_input != st.session_state.p2p_room_id:
        st.session_state.p2p_room_id = user_input

with col2:
    st.write("")
    st.write("")
    if st.button("🎲 Tạo mã ngẫu nhiên"):
        st.session_state.p2p_room_id = f"room-{random.randint(100, 999)}"
        st.rerun()

sync_key = st.session_state.p2p_room_id.strip()

if not sync_key:
    st.warning("⚠️ Vui lòng nhập mã phòng để bắt đầu.")
    st.stop()

# HTML + JS giữ nguyên logic P2P
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
        const ROOM_ID = "st_p2p_v2_{sync_key}";
        const statusEl = document.getElementById('status');
        const localText = document.getElementById('localText');
        const remoteText = document.getElementById('remoteText');
        
        let peer = null;
        let conn = null;

        const peerConfig = {{
            host: '0.peerjs.com',
            port: 443,
            path: '/',
            secure: true,
            debug: 1,
            config: {{
                iceServers: [
                    {{ urls: 'stun:stun.l.google.com:19302' }},
                    {{ urls: 'stun:stun1.l.google.com:19302' }}
                ]
            }}
        }};

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

        function initPeer() {{
            if (typeof Peer === 'undefined') {{
                updateStatus("⏳ Đang tải thư viện PeerJS...", 'warning');
                setTimeout(initPeer, 300);
                return;
            }}

            peer = new Peer(ROOM_ID, peerConfig);

            peer.on('open', (id) => {{
                updateStatus("🟢 Đã mở phòng thành công! Hãy mở thiết bị 2 và nhập mã '{sync_key}' để ghép nối.", "warning");
            }});

            peer.on('connection', (c) => {{
                conn = c;
                setupEvents();
            }});

            peer.on('error', (err) => {{
                if (err.type === 'unavailable-id') {{
                    updateStatus("🔄 Đã tìm thấy Máy 1 (Host). Đang kết nối P2P...", "warning");
                    if (peer) peer.destroy();
                    
                    peer = new Peer(peerConfig);
                    peer.on('open', () => {{
                        conn = peer.connect(ROOM_ID, {{ reliable: true }});
                        setupEvents();
                    }});
                }} else {{
                    updateStatus("❌ Lỗi P2P: " + err.type, 'error');
                }}
            }});
        }}

        function setupEvents() {{
            if (!conn) return;

            conn.on('open', () => {{
                updateStatus("✅ KẾT NỐI P2P THÀNH CÔNG! Bắt đầu gõ để đồng bộ tức thì.", 'success');
            }});

            conn.on('data', (data) => {{
                remoteText.value = data;
            }});

            conn.on('close', () => {{
                updateStatus("⚠️ Kết nối P2P đã ngắt.", 'error');
            }});
        }}

        localText.addEventListener('input', (e) => {{
            const val = e.target.value;
            if (conn && conn.open) {{
                conn.send(val);
            }}
        }});

        setTimeout(initPeer, 200);
    </script>
</body>
</html>
"""

# Sử dụng st.iframe truyền srcData thay cho components.html
st.iframe(src=html_code, height=300)
