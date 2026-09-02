
## QUY TẮC BẮT BUỘC:

1. TRẢ LỜI DỰA TRÊN SOURCE CODE - Mọi câu trả lời phải dựa trên code thực tế đã upload

2. GIỮ NGUYÊN CODING STYLE - Khi ví dụ hoặc đề xuất code, dùng đúng style đã học

3. KHÔNG TỰ BỊA - Nếu thông tin không có trong source, nói: "Tôi không tìm thấy thông tin này trong source code."

4. KHI USER YÊU CẦU SỬA CODE:
   - Tìm đúng đoạn liên quan
   - Hiểu logic xung quanh
   - Sửa theo style đã học
   - Giữ nguyên phần không được yêu cầu sửa
   - KHÔNG rewrite toàn bộ project

5. KHI USER YÊU CẦU FULL CODE:
   - Xuất 100% source code hiện tại
   - Bao gồm cả phần không thay đổi
   - KHÔNG dùng "// rest of code..." hoặc "..."
   - KHÔNG bỏ bất kỳ function, variable, include nào

6. CÁC LỆNH ĐẶC BIỆT:
   - "show flow" → Giải thích luồng thực thi chính
   - "giải thích [đoạn]" → Giải thích chi tiết đoạn đó
   - "function X gọi function Y?" → Kiểm tra dependency
   - "sửa [đoạn]" → Sửa code và hiển thị thay đổi
   - "full code" / "generate full code" → Xuất toàn bộ source code

Bạn là assistant thông minh, hiểu deep context của codebase này. Trả lời tự nhiên, chính xác."""


def call_ai(prompt: str, system: Optional[str] = None, temperature: float = 0.3) -> str:
    """Gọi AI model và trả về response"""
    messages = []
    
    if system:
        messages.append({"role": "system", "content": system})
    
    messages.append({"role": "user", "content": prompt})
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=temperature,
            max_tokens=MAX_TOKENS
        )
        return response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")


# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "service": "AI Self-Learning Code Agent",
        "version": "1.0.0",
        "model": MODEL_NAME,
        "active_sessions": len(sessions)
    }


@app.post("/api/upload")
async def upload_code(file: UploadFile = File(...)):
    """
    Endpoint 1: UPLOAD FILE
    - Nhận source code file
    - AI tự đọc, phân tích, học pattern
    - Trả về session_id để chat tiếp
    """
    # Đọc file content
    content = await file.read()
    raw_code = content.decode("utf-8", errors="ignore")
    filename = file.filename or "unknown.txt"
    
    if not raw_code.strip():
        raise HTTPException(status_code=400, detail="File rỗng")
    
    # Tạo session
    session_id = generate_session_id(raw_code)
    
    # PHASE 1: AI TỰ HỌC SOURCE CODE
    learning_prompt = build_learning_prompt(raw_code, filename)
    learned_raw = call_ai(learning_prompt, temperature=0.2)
    
    # Parse JSON response
    try:
        # Try to extract JSON from response
        if "```json" in learned_raw:
            json_str = learned_raw.split("```json")[1].split("```")[0]
        elif "```" in learned_raw:
            json_str = learned_raw.split("```")[1].split("```")[0]
        else:
            json_str = learned_raw
        
        learned_patterns = json.loads(json_str.strip())
    except json.JSONDecodeError:
        # Fallback: wrap in object
        learned_patterns = {
            "raw_analysis": learned_raw,
            "parse_note": "JSON parse failed, storing raw analysis"
        }
    
    # Lưu session
    session = CodeSession(
        session_id=session_id,
        filename=filename,
        raw_code=raw_code,
        created_at=datetime.now().isoformat(),
        learned_patterns=learned_patterns,
        code_versions=[{"version": 0, "code": raw_code, "timestamp": datetime.now().isoformat()}]
    )
    sessions[session_id] = session
    
    return {
        "success": True,
        "session_id": session_id,
        "filename": filename,
        "code_length": len(raw_code),
        "line_count": raw_code.count("\n") + 1,
        "language_detected": learned_patterns.get("language", "unknown"),
        "summary": learned_patterns.get("summary", ""),
        "message": "✅ Code đã được upload và AI đã TỰ HỌC xong pattern. Sẵn sàng chat!"
    }


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Endpoint 2: CHAT VỚI USER
    - User hỏi tự nhiên về code
    - AI trả lời dựa trên source đã học
    - Hỗ trợ yêu cầu sửa code
    """
    session_id = request.session_id
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session không tồn tại. Hãy upload code trước.")
    
    session = sessions[session_id]
    user_message = request.message
    
    # Build context
    system_prompt = build_chat_system_prompt(session.learned_patterns, session.raw_code)
    
    # Thêm chat history vào context
    messages_for_context = []
    for msg in session.chat_history[-10:]:  # Giữ 10 message gần nhất
        messages_for_context.append(f"{'User' if msg['role']=='user' else 'AI'}: {msg['content']}")
    
    history_context = "\n".join(messages_for_context)
    
    # Full prompt
    full_user_prompt = f"{user_message}\n\n## LỊCH SỬ CHAT GẦN NHẤT:\n{history_context}" if history_context else user_message
    
    # Gọi AI
    ai_response = call_ai(full_user_prompt, system_prompt)
    
    # Lưu chat history
    session.chat_history.append({
        "role": "user",
        "content": user_message,
        "timestamp": datetime.now().isoformat()
    })
    session.chat_history.append({
        "role": "assistant", 
        "content": ai_response,
        "timestamp": datetime.now().isoformat()
    })
    
    # Auto-detect nếu AI trả về code modification và cập nhật
    lower_msg = user_message.lower()
    if any(kw in lower_msg for kw in ["sửa", "fix", "change", "modify", "thêm", "add", "update", "edit"]):
        # Extract code block nếu có
        if "```" in ai_response:
            try:
                code_block = ai_response.split("```")[1]
                # Remove language identifier if present
                if "\n" in code_block:
                    code_block = code_block.split("\n", 1)[1]
                session.raw_code = code_block
                session.code_versions.append({
                    "version": len(session.code_versions),
                    "code": code_block,
                    "timestamp": datetime.now().isoformat(),
                    "trigger_message": user_message[:100]
                })
            except IndexError:
                pass
    
    return {
        "success": True,
        "session_id": session_id,
        "response": ai_response,
        "code_version": len(session.code_versions) - 1
    }


@app.post("/api/full-code")
async def get_full_code(request: FullCodeRequest):
    """
    Endpoint 3: XUẤT TOÀN BỘ CODE
    - Trả về 100% source code hiện tại
    - Không bỏ sót gì
    """
    session_id = request.session_id
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session không tồn tại.")
    
    session = sessions[session_id]
    
    return {
        "success": True,
        "session_id": session_id,
        "filename": session.filename,
        "current_version": len(session.code_versions) - 1,
        "total_versions": len(session.code_versions),
        "full_code": session.raw_code,
        "line_count": session.raw_code.count("\n") + 1,
        "char_count": len(session.raw_code),
        "warning": "Đây là 100% source code hiện tại, không bị cắt giảm"
    }


@app.get("/api/session/{session_id}")
async def get_session_info(session_id: str):
    """Lấy thông tin session (không include full code)"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session không tồn tại.")
    
    session = sessions[session_id]
    
    return {
        "session_id": session.session_id,
        "filename": session.filename,
        "created_at": session.created_at,
        "language": session.learned_patterns.get("language", "unknown"),
        "summary": session.learned_patterns.get("summary", ""),
        "functions_count": len(session.learned_patterns.get("functions", [])),
        "patterns_found": len(session.learned_patterns.get("patterns_found", [])),
        "chat_messages": len(session.chat_history),
        "code_versions": len(session.code_versions)
    }


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Xóa session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session không tồn tại.")
    
    del sessions[session_id]
    
    return {"success": True, "message": "Session đã bị xóa"}


@app.get("/api/sessions")
async def list_sessions():
    """Liệt kê tất cả active sessions"""
    return {
        "active_sessions": len(sessions),
        "sessions": [
            {
                "session_id": s.session_id,
                "filename": s.filename,
                "created_at": s.created_at,
                "language": s.learned_patterns.get("language", "unknown"),
                "chat_count": len(s.chat_history)
            }
            for s in sessions.values()
        ]
    }


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║     AI SELF-LEARNING CODE AGENT v1.0                  ║
    ║     Upload → Learn → Chat → Edit → Full Code         ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
