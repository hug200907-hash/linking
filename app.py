"""
AI Code Generator - Minimal Version
===============================
Upload code → AI reads → Chat → Modify → Generate Full Code → Download

Author: Kyriel for Boss
"""

import os
import re
from flask import (
    Flask, render_template_string, request, jsonify,
    send_file, abort
)
from openai import OpenAI
from dotenv import load_dotenv
import tempfile
import json
from datetime import datetime

# ─── Load Environment ───────────────────────────────────────────────
load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max

# ─── OpenAI Client ──────────────────────────────────────────────────
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# ─── In-Memory Storage (Single Session) ────────────────────────────
# In production, use Redis/Database instead
session_data = {
    'original_code': '',
    'current_code': '',
    'filename': '',
    'chat_history': [],
    'modifications': []  # Track all modifications
}

# ════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT - Embedded directly
# ════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are an expert code analysis and modification AI.

## Your Capabilities:
1. **Read & Understand**: Analyze any source code completely
2. **Explain Flow**: Describe logic, function calls, data flow when asked
3. **Modify Code**: Make precise changes as requested
4. **Generate Full Code**: Output COMPLETE source code (never snippets)

## Critical Rules:

### When User Asks About Code:
- Explain the actual code logic based on what you read
- Identify functions, classes, variables that EXIST in the code
- Show call chains and data flows that are PRESENT
- If something doesn't exist in the code, SAY SO clearly

### When User Requests Modifications:
- ONLY modify the specific parts requested
- Keep ALL other code exactly as-is
- Preserve formatting, comments, style of unchanged parts
- Apply the change to the FULL codebase context

### When User Says "generate full code" or "full code" or "show full code":
- Output THE ENTIRE source code from start to finish
- Every line, every function, every class
- DO NOT summarize, DO NOT use "...", DO NOT skip anything
- This must be complete, runnable code

### What You MUST NOT Do:
- NEVER invent functions/variables/classes that don't exist
- NEVER guess at offsets, memory addresses, or implementation details not shown
- NEVER add features user didn't ask for
- NEVER return partial code when full code is requested
- NEVER say "rest of code remains the same" - SHOW IT ALL

### If You Lack Information:
- Ask the user a specific question
- Or mark with TODO comment explaining what's needed

## Current Code Context:
{code_context}

## Modification History:
{modification_history}

Respond in the same language the user uses.
"""

# ════════════════════════════════════════════════════════════════════
# HTML TEMPLATE - Single Page App
# ════════════════════════════════════════════════════════════════════

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Code Generator</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --bg-dark: #0d1117;
            --bg-card: #161b22;
            --bg-input: #21262d;
            --border: #30363d;
            --text-primary: #e6edf3;
            --text-secondary: #8b949e;
            --accent: #58a6ff;
            --accent-hover: #79c0ff;
            --success: #3fb950;
            --warning: #d29922;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.5;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Header */
        .header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 24px;
        }
        
        .header h1 {
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .header p {
            color: var(--text-secondary);
            font-size: 14px;
        }
        
        /* Main Grid */
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        @media (max-width: 900px) {
            .main-grid { grid-template-columns: 1fr; }
        }
        
        /* Cards */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
        }
        
        .card-header {
            padding: 12px 16px;
            background: var(--bg-input);
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .card-header h2 {
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .card-body {
            padding: 16px;
        }
        
        /* Upload Area */
        .upload-area {
            border: 2px dashed var(--border);
            border-radius: 6px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .upload-area:hover {
            border-color: var(--accent);
            background: rgba(88, 166, 255, 0.05);
        }
        
        .upload-area.dragover {
            border-color: var(--accent);
            background: rgba(88, 166, 255, 0.1);
        }
        
        .upload-icon {
            font-size: 48px;
            margin-bottom: 12px;
        }
        
        .upload-text {
            color: var(--text-secondary);
            margin-bottom: 12px;
        }
        
        .upload-btn {
            display: inline-block;
            padding: 10px 20px;
            background: var(--accent);
            color: #fff;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
        }
        
        .upload-btn:hover {
            background: var(--accent-hover);
        }
        
        #fileInput { display: none; }
        
        .file-info {
            margin-top: 12px;
            padding: 12px;
            background: var(--bg-input);
            border-radius: 6px;
            font-size: 13px;
            display: none;
        }
        
        .file-info.show { display: block; }
        
        .file-name {
            color: var(--accent);
            font-weight: 500;
            word-break: break-all;
        }
        
        /* Chat */
        .chat-container {
            height: 400px;
            overflow-y: auto;
            background: var(--bg-dark);
            border-radius: 6px;
            border: 1px solid var(--border);
        }
        
        .chat-messages {
            padding: 16px;
        }
        
        .chat-empty {
            color: var(--text-secondary);
            text-align: center;
            padding: 60px 20px;
            font-size: 14px;
        }
        
        .message {
            margin-bottom: 16px;
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .message-user {
            text-align: right;
        }
        
        .message-bubble {
            display: inline-block;
            max-width: 85%;
            padding: 10px 14px;
            border-radius: 12px;
            font-size: 14px;
            text-align: left;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-word;
        }
        
        .message-user .message-bubble {
            background: var(--accent);
            color: #fff;
            border-bottom-right-radius: 4px;
        }
        
        .message-ai .message-bubble {
            background: var(--bg-input);
            color: var(--text-primary);
            border-bottom-left-radius: 4px;
        }
        
        .chat-input-area {
            display: flex;
            gap: 10px;
            margin-top: 12px;
        }
        
        .chat-input {
            flex: 1;
            padding: 12px 16px;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text-primary);
            font-size: 14px;
            font-family: inherit;
            resize: vertical;
            min-height: 44px;
        }
        
        .chat-input:focus {
            outline: none;
            border-color: var(--accent);
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .btn-primary {
            background: var(--accent);
            color: #fff;
        }
        
        .btn-primary:hover:not(:disabled) {
            background: var(--accent-hover);
        }
        
        .btn-success {
            background: var(--success);
            color: #fff;
        }
        
        .btn-success:hover:not(:disabled) {
            background: #46d158;
        }
        
        .btn-secondary {
            background: var(--bg-input);
            color: var(--text-primary);
            border: 1px solid var(--border);
        }
        
        .btn-secondary:hover:not(:disabled) {
            background: var(--border);
        }
        
        /* Code Display */
        .code-container {
            height: 500px;
            overflow: auto;
            background: var(--bg-dark);
            border: 1px solid var(--border);
            border-radius: 6px;
            position: relative;
        }
        
        .code-display {
            padding: 16px;
            font-family: 'Fira Code', 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            line-height: 1.7;
            white-space: pre;
            overflow-x: auto;
            tab-size: 4;
        }
        
        .code-empty {
            color: var(--text-secondary);
            text-align: center;
            padding: 80px 20px;
            font-size: 14px;
        }
        
        .line-numbers {
            color: var(--text-secondary);
            user-select: none;
            margin-right: 16px;
            text-align: right;
            min-width: 40px;
            display: inline-block;
        }
        
        /* Action Bar */
        .action-bar {
            display: flex;
            gap: 10px;
            margin-top: 12px;
            flex-wrap: wrap;
        }
        
        /* Loading */
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid var(--border);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .loading-text {
            color: var(--text-secondary);
            font-size: 13px;
            padding: 20px;
            text-align: center;
        }
        
        /* Status Badge */
        .status-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .status-pending {
            background: rgba(210, 153, 34, 0.2);
            color: var(--warning);
        }
        
        .status-ready {
            background: rgba(63, 185, 80, 0.2);
            color: var(--success);
        }
        
        /* Toast Notification */
        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 14px 20px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.4);
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s ease;
            z-index: 1000;
        }
        
        .toast.show {
            transform: translateY(0);
            opacity: 1;
        }
        
        .toast.success { border-left: 4px solid var(--success); }
        .toast.error { border-left: 4px solid #f85149; }
        
        /* Scrollbar */
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: var(--bg-dark); }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--text-secondary); }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🤖 AI Code Generator</h1>
            <p>Upload code → Chat with AI → Modify → Generate Full Code → Download</p>
        </div>
        
        <!-- Main Content -->
        <div class="main-grid">
            <!-- Left Column: Upload + Chat -->
            <div class="left-col">
                <!-- Upload Card -->
                <div class="card" style="margin-bottom: 20px;">
                    <div class="card-header">
                        <h2>📁 Upload Source Code</h2>
                        <span id="uploadStatus" class="status-badge status-pending">No File</span>
                    </div>
                    <div class="card-body">
                        <div class="upload-area" id="uploadArea">
                            <div class="upload-icon">📄</div>
                            <div class="upload-text">Drag & drop your code file here<br>or click to browse</div>
                            <button type="button" class="upload-btn">Choose File</button>
                            <input type="file" id="fileInput" accept=".py,.js,.ts,.java,.c,.cpp,.h,.cs,.go,.rs,.rb,.php,.swift,.kt,.scala,.lua,.r,.m,.sh,.bat,.sql,.html,.css,.json,.xml,.yaml,.yml,.toml,.ini,.cfg,.conf,.md,.txt">
                        </div>
                        <div class="file-info" id="fileInfo">
                            <strong>File:</strong> <span class="file-name" id="fileName"></span><br>
                            <strong>Size:</strong> <span id="fileSize"></span><br>
                            <strong>Lines:</strong> <span id="fileLines"></span>
                        </div>
                    </div>
                </div>
                
                <!-- Chat Card -->
                <div class="card">
                    <div class="card-header">
                        <h2>💬 Chat with AI</h2>
                        <button class="btn btn-secondary" onclick="clearChat()" style="padding: 6px 12px; font-size: 12px;">Clear</button>
                    </div>
                    <div class="card-body">
                        <div class="chat-container" id="chatContainer">
                            <div class="chat-messages" id="chatMessages">
                                <div class="chat-empty">Upload a file and start chatting about your code...</div>
                            </div>
                        </div>
                        <div class="chat-input-area">
                            <textarea 
                                class="chat-input" 
                                id="chatInput" 
                                placeholder="Ask about code flow, request modifications, or type 'full code'..."
                                rows="2"
                                onkeydown="handleKeyDown(event)"
                            ></textarea>
                            <button class="btn btn-primary" id="sendBtn" onclick="sendMessage()" disabled>
                                Send
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Right Column: Code Display -->
            <div class="right-col">
                <div class="card">
                    <div class="card-header">
                        <h2>📝 Current Code</h2>
                        <span id="codeStatus" class="status-badge status-pending">Empty</span>
                    </div>
                    <div class="card-body">
                        <div class="code-container" id="codeContainer">
                            <div class="code-display" id="codeDisplay">
                                <div class="code-empty">Upload a file to see code here...</div>
                            </div>
                        </div>
                        <div class="action-bar">
                            <button class="btn btn-success" id="downloadBtn" onclick="downloadCode()" disabled>
                                ⬇️ Download Code
                            </button>
                            <button class="btn btn-primary" id="fullCodeBtn" onclick="requestFullCode()" disabled>
                                🔄 Generate Full Code
                            </button>
                            <button class="btn btn-secondary" id="copyBtn" onclick="copyCode()" disabled>
                                📋 Copy to Clipboard
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Toast -->
    <div class="toast" id="toast"></div>

    <script>
        // ─── State ────────────────────────────────────────────────
        let currentFilename = '';
        let hasFile = false;
        let isProcessing = false;
        
        // ─── DOM Elements ─────────────────────────────────────────
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        const fileLines = document.getElementById('fileLines');
        const uploadStatus = document.getElementById('uploadStatus');
        const chatMessages = document.getElementById('chatMessages');
        const chatInput = document.getElementById('chatInput');
        const sendBtn = document.getElementById('sendBtn');
        const codeDisplay = document.getElementById('codeDisplay');
        const codeStatus = document.getElementById('codeStatus');
        const downloadBtn = document.getElementById('downloadBtn');
        const fullCodeBtn = document.getElementById('fullCodeBtn');
        const copyBtn = document.getElementById('copyBtn');
        
        // ─── Upload Handlers ──────────────────────────────────────
        uploadArea.addEventListener('click', () => fileInput.click());
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                handleFile(e.dataTransfer.files[0]);
            }
        });
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                handleFile(e.target.files[0]);
            }
        });
        
        async function handleFile(file) {
            const validExtensions = ['.py','.js','.ts','.java','.c','.cpp','.h','.cs','.go','.rs','.rb','.php','.swift','.kt','.scala','.lua','.r','.m','.sh','.bat','.sql','.html','.css','.json','.xml','.yaml','.yml','.toml','.ini','.cfg','.conf','.md','.txt'];
            const ext = '.' + file.name.split('.').pop().toLowerCase();
            
            if (!validExtensions.includes(ext)) {
                showToast('Invalid file type. Please upload a code file.', 'error');
                return;
            }
            
            const content = await file.text();
            const lines = content.split('\\n').length;
            
            // Update UI
            currentFilename = file.name;
            fileName.textContent = file.name;
            fileSize.textContent = formatBytes(file.size);
            fileLines.textContent = lines;
            fileInfo.classList.add('show');
            uploadStatus.textContent = 'Loaded';
            uploadStatus.className = 'status-badge status-ready';
            hasFile = true;
            sendBtn.disabled = false;
            downloadBtn.disabled = false;
            fullCodeBtn.disabled = false;
            copyBtn.disabled = false;
            
            // Display code
            displayCode(content);
            
            // Upload to server
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                if (data.success) {
                    showToast(`File "${file.name}" uploaded successfully!`, 'success');
                    clearChat();
                    addMessage('ai', `✅ File **${file.name}** loaded successfully!\\n\\n📊 **Stats:**\\n• Size: ${formatBytes(file.size)}\\n• Lines: ${lines}\\n\\n💬 You can now ask me about:\\n• Code flow and logic\\n• Function/class explanations\\n• Request modifications\\n• Type "full code" to generate complete code`);
                } else {
                    showToast(data.error || 'Upload failed', 'error');
                }
            } catch (err) {
                showToast('Upload error: ' + err.message, 'error');
            }
        }
        
        // ─── Chat Functions ───────────────────────────────────────
        function handleKeyDown(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        }
        
        async function sendMessage() {
            const message = chatInput.value.trim();
            if (!message || isProcessing || !hasFile) return;
            
            // Add user message
            addMessage('user', message);
            chatInput.value = '';
            
            // Show loading
            isProcessing = true;
            sendBtn.disabled = true;
            sendBtn.innerHTML = '<span class="loading"></span>';
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    addMessage('ai', data.response);
                    
                    // If code was updated
                    if (data.code_updated) {
                        displayCode(data.current_code);
                        codeStatus.textContent = 'Modified';
                        showToast('Code has been updated!', 'success');
                    }
                } else {
                    addMessage('ai', '❌ Error: ' + (data.error || 'Unknown error'));
                }
            } catch (err) {
                addMessage('ai', '❌ Connection error: ' + err.message);
            } finally {
                isProcessing = false;
                sendBtn.disabled = false;
                sendBtn.innerHTML = 'Send';
            }
        }
        
        async function requestFullCode() {
            if (!hasFile || isProcessing) return;
            
            isProcessing = true;
            fullCodeBtn.disabled = true;
            fullCodeBtn.innerHTML = '<span class="loading"></span> Generating...';
            
            addMessage('user', 'Generate the complete full code');
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: 'generate full code' })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    addMessage('ai', '📄 **Complete Full Code Generated:**\\n\\n---\\n\\n' + data.response);
                    
                    if (data.current_code) {
                        displayCode(data.current_code);
                        codeStatus.textContent = 'Full Code';
                    }
                } else {
                    addMessage('ai', '❌ Error: ' + (data.error || 'Unknown error'));
                }
            } catch (err) {
                addMessage('ai', '❌ Connection error: ' + err.message);
            } finally {
                isProcessing = false;
                fullCodeBtn.disabled = false;
                fullCodeBtn.innerHTML = '🔄 Generate Full Code';
            }
        }
        
        function addMessage(role, content) {
            // Remove empty state
            const emptyState = chatMessages.querySelector('.chat-empty');
            if (emptyState) emptyState.remove();
            
            const msgDiv = document.createElement('div');
            msgDiv.className = `message message-${role}`;
            
            // Simple markdown-like formatting
            let formattedContent = content
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/`(.*?)`/g, '<code style="background:var(--bg-dark);padding:2px 6px;border-radius:3px;">$1</code>');
            
            msgDiv.innerHTML = `<div class="message-bubble">${formattedContent}</div>`;
            chatMessages.appendChild(msgDiv);
            chatMessages.parentElement.scrollTop = chatMessages.parentElement.scrollHeight;
        }
        
        function clearChat() {
            chatMessages.innerHTML = '<div class="chat-empty">Upload a file and start chatting about your code...</div>';
        }
        
        // ─── Code Display ─────────────────────────────────────────
        function displayCode(code) {
            const lines = code.split('\\n');
            let html = '';
            
            lines.forEach((line, i) => {
                const escapedLine = escapeHtml(line);
                html += `<span class="line-numbers">${i + 1}</span>${escapedLine}\\n`;
            });
            
            codeDisplay.innerHTML = html;
            codeStatus.textContent = 'Ready';
            codeStatus.className = 'status-badge status-ready';
        }
        
        function getCurrentCode() {
            return codeDisplay.textContent.replace(/^\\s*\\d+\\s*/gm, '');
        }
        
        // ─── Actions ──────────────────────────────────────────────
        async function downloadCode() {
            try {
                const response = await fetch('/api/download');
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = currentFilename || 'code.txt';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                    showToast('Code downloaded successfully!', 'success');
                }
            } catch (err) {
                showToast('Download failed: ' + err.message, 'error');
            }
        }
        
        async function copyCode() {
            try {
                const response = await fetch('/api/download');
                if (response.ok) {
                    const text = await response.text();
                    await navigator.clipboard.writeText(text);
                    showToast('Code copied to clipboard!', 'success');
                }
            } catch (err) {
                showToast('Copy failed: ' + err.message, 'error');
            }
        }
        
        // ─── Utilities ────────────────────────────────────────────
        function formatBytes(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        function showToast(message, type = 'success') {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = `toast ${type} show`;
            setTimeout(() => {
                toast.classList.remove('show');
            }, 3000);
        }
    </script>
</body>
</html>'''

# ════════════════════════════════════════════════════════════════════
# API ROUTES
# ════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    """Serve the main page."""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and initialize session."""
    global session_data
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    try:
        content = file.read().decode('utf-8')
        
        # Initialize session
        session_data = {
            'original_code': content,
            'current_code': content,
            'filename': file.filename,
            'chat_history': [],
            'modifications': []
        }
        
        return jsonify({
            'success': True,
            'filename': file.filename,
            'lines': len(content.split('\\n')),
            'size': len(content)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages with AI."""
    global session_data
    
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'success': False, 'error': 'No message provided'})
    
    user_message = data['message'].strip()
    if not user_message:
        return jsonify({'success': False, 'error': 'Empty message'})
    
    if not session_data['current_code']:
        return jsonify({'success': False, 'error': 'No code loaded. Please upload a file first.'})
    
    try:
        # Add to chat history
        session_data['chat_history'].append({
            'role': 'user',
            'content': user_message
        })
        
        # Build messages for OpenAI
        messages = [
            {
                'role': 'system',
                'content': SYSTEM_PROMPT.format(
                    code_context=session_data['current_code'],
                    modification_history='\\n'.join([
                        f"- {m}" for m in session_data['modifications'][-10:]  # Last 10 mods
                    ]) or 'No modifications yet'
                )
            }
        ]
        
        # Add recent chat history (last 20 messages for context)
        for msg in session_data['chat_history'][-20:]:
            messages.append(msg)
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model='gpt-4o',
            messages=messages,
            temperature=0.3,
            max_tokens=4096
        )
        
        ai_response = response.choices[0].message.content
        
        # Add AI response to history
        session_data['chat_history'].append({
            'role': 'assistant',
            'content': ai_response
        })
        
        # Check if this is a full code request and extract code
        code_updated = False
        current_code = session_data['current_code']
        
        # Detect if AI returned full code
        full_code_triggers = ['generate full code', 'full code', 'show full code', 
                             'complete code', 'entire code', 'all code']
        is_full_code_request = any(trigger in user_message.lower() for trigger in full_code_triggers)
        
        if is_full_code_request:
            # Try to extract code block from response
            extracted_code = extract_code_from_response(ai_response)
            if extracted_code:
                session_data['current_code'] = extracted_code
                session_data['modifications'].append(f"Full code generated at {datetime.now().strftime('%H:%M:%S')}")
                code_updated = True
                current_code = extracted_code
        else:
            # Check if it's a modification request
            mod_triggers = ['modify', 'change', 'fix', 'add', 'remove', 'delete', 
                           'update', 'sửa', 'thêm', 'xóa', 'đổi']
            is_mod_request = any(trigger in user_message.lower() for trigger in mod_triggers)
            
            if is_mod_request:
                extracted_code = extract_code_from_response(ai_response)
                if extracted_code and len(extracted_code) > len(session_data['current_code']) * 0.5:
                    session_data['current_code'] = extracted_code
                    session_data['modifications'].append(f"Modified: {user_message[:50]}... at {datetime.now().strftime('%H:%M:%S')}")
                    code_updated = True
                    current_code = extracted_code
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'code_updated': code_updated,
            'current_code': current_code
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/download', methods=['GET'])
def download():
    """Download current code."""
    if not session_data['current_code']:
        abort(400, description='No code available')
    
    filename = session_data['filename'] or 'code.txt'
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='_' + filename, delete=False) as f:
        f.write(session_data['current_code'])
        temp_path = f.name
    
    return send_file(
        temp_path,
        as_attachment=True,
        download_name=filename,
        mimetype='text/plain'
    )


@app.route('/api/reset', methods=['POST'])
def reset_session():
    """Reset the session."""
    global session_data
    session_data = {
        'original_code': '',
        'current_code': '',
        'filename': '',
        'chat_history': [],
        'modifications': []
    }
    return jsonify({'success': True})


# ════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════

def extract_code_from_response(response):
    """
    Extract code from AI response.
    Handles various formats: ```code```, plain code, etc.
    """
    # Try to extract from code blocks
    code_block_pattern = r'```(?:\\w*)\\n?(.*?)```'
    matches = re.findall(code_block_pattern, response, re.DOTALL)
    
    if matches:
        # Return the longest code block (likely the main code)
        return max(matches, key=len).strip()
    
    # If no code blocks but response looks like code
    # (contains function/class definitions, brackets, etc.)
    if re.search(r'(def |class |function |public |private |\\{\\}|\\[\\])', response):
        # Check if most lines look like code
        lines = response.split('\\n')
        code_like_lines = sum(1 for line in lines if 
                             re.match(r'^\\s*(def |class |import |from |//|/\\*|\\*\\/|\\{|\\}|\\[|\\]|//|=|;|return |if \\(|else|for |while )', line))
        
        if code_like_lines > len(lines) * 0.3:
            return response.strip()
    
    return None


# ════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║           AI Code Generator - Minimal Edition             ║
    ║                                                           ║
    ║   By Kyriel for Boss                                      ║
    ║   http://localhost:5000                                   ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  WARNING: OPENAI_API_KEY not found!")
        print("   Create a .env file with: OPENAI_API_KEY=your_key_here")
        print("")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
