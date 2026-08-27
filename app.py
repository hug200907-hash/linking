import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Đồng bộ P2P Realtime", page_icon="⚡", layout="wide")

st.title("⚡ Đồng bộ 2 thiết bị Trực tiếp (P2P - Không qua Máy chủ)")
st.caption("Công nghệ WebRTC: Kết nối trực tiếp giữa 2 máy qua mã 3 chữ số - Không bao giờ lo lỗi kết nối Database.")

sync_key = st.text_input("🔑 Nhập mã đồng bộ (3 chữ số):", max_chars=3, placeholder="123")

if len(sync_key) != 3 or not sync_key.isdigit():
    st.info("💡 Vui lòng nhập đúng 3 chữ số trên cả 2 máy để bắt đầu kết nối.")
    st.stop()

# Mã HTML + JavaScript tích hợp PeerJS để truyền dữ liệu P2P
html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/peerjs@1.5.2/dist/peerjs.min.js"></script>
    <style>
        body {{ font-family: sans-serif; padding: 10px; background: #f9f9f9; }}
        .box {{ background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd; margin-bottom: 10px; }}
        textarea {{ width: 100%; height: 100px; padding: 8px; box-sizing: border-box; font-size: 14px; border-radius: 4px; border: 1px solid #ccc; }}
        button {{ background: #ff4b4b; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: bold; width: 100%; }}
        button:hover {{ background: #e03e3e; }}
        #status {{ font-weight: bold; color: #ff9800; margin-bottom: 10px; }}
    </style>
</head>
<body>

    <div id="status">⏳ Đang khởi tạo kết nối P2P cho mã: {sync_key}...</div>

    <div style="display: flex; gap: 15px;">
        <div class="box" style="flex: 1;">
            <h3>📤 Bên gửi</h3>
            <textarea id="sendText" placeholder="Nhập nội dung cần truyền sang máy kia..."></textarea>
            <button onclick="sendData()">🚀 Gửi trực tiếp sang máy kia</button>
        </div>
        
        <div class="box" style="flex: 1;">
            <h3>📥 Dữ liệu nhận được</h3>
            <textarea id="receiveText" readonly placeholder="Dữ liệu từ máy kia sẽ xuất hiện ở đây ngay lập tức..."></textarea>
        </div>
    </div>

    <script>
        const roomKey = "{sync_key}";
        const statusEl = document.getElementById('status');
        const receiveText = document.getElementById('receiveText');
        const sendText = document.getElementById('sendText');
        
        let conn = null;

        // Khởi tạo Peer với ID dựa trên mã 3 số
        // Thiết bị kết nối trước sẽ làm Host, thiết bị sau sẽ Connect vào
        const peer = new Peer("streamlit_p2p_room_" + roomKey);

        peer.on('open', function(id) {{
            statusEl.innerText = "🟢 Bạn là Máy Chủ (Host). Đang chờ máy thứ 2 nhập mã " + roomKey + "...";
            statusEl.style.color = "green";
        }});

        // Nếu ID đã tồn tại (Đã có Máy A làm Host), tự động chuyển thành Client để kết nối vào Máy A
        peer.on('error', function(err) {{
            if (err.type === 'unavailable-id') {{
                statusEl.innerText = "🔄 Đã tìm thấy Máy 1, đang kết nối...";
                
                // Tạo client mới với ID ngẫu nhiên
                const clientPeer = new Peer();
                clientPeer.on('open', function() {{
                    conn = clientPeer.connect("streamlit_p2p_room_" + roomKey);
                    setupConnection();
                }});
            } else {{
                statusEl.innerText = "❌ Lỗi kết nối: " + err;
                statusEl.style.color = "red";
            }}
        }});

        // Lắng nghe kết nối đến (Dành cho Máy A)
        peer.on('connection', function(c) {{
            conn = c;
            setupConnection();
        }});

        function setupConnection() {{
            conn.on('open', function() {{
                statusEl.innerText = "✅ ĐÃ KẾT NỐI TRỰC TIẾP 2 MÁY! Bạn có thể truyền dữ liệu ngay.";
                statusEl.style.color = "green";
            }});

            // Nhận dữ liệu P2P
            conn.on('data', function(data) {{
                receiveText.value = data;
            }});
        }}

        // Gửi dữ liệu P2P
        function sendData() {{
            if (conn && conn.open) {{
                const msg = sendText.value;
                conn.send(msg);
                alert("Đã gửi dữ liệu trực tiếp sang máy bên kia!");
            }} else {{
                alert("Chưa có máy nào kết nối với bạn! Hãy mở máy 2 và nhập đúng mã " + roomKey);
            }}
        }}
    </script>
</body>
</html>
"""

# Hiển thị giao diện WebRTC trực tiếp bên trong Streamlit
components.html(html_code, height=350)
