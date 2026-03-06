from flask import Flask, render_template, request, jsonify
from google import genai
import sqlite3
import datetime

app = Flask(__name__)
client = genai.Client(api_key="AIzaSyBZ6Qip3kX4qYO8YmlNNlgCLSjjQ8tUl78")
MODELS = ["gemini-2.5-flash", "gemini-3-flash-preview", "gemini-2.5-flash-lite"]

def init_db():
    conn = sqlite3.connect('kayserai.db')
    conn.execute('CREATE TABLE IF NOT EXISTS chats (id INTEGER PRIMARY KEY, title TEXT, created_at TIMESTAMP)')
    conn.execute('CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, chat_id INTEGER, role TEXT, content TEXT)')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/chats', methods=['GET'])
def get_chats():
    conn = sqlite3.connect('kayserai.db')
    chats = conn.execute('SELECT * FROM chats ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([{'id': c[0], 'title': c[1]} for c in chats])

@app.route('/api/delete/<int:chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    conn = sqlite3.connect('kayserai.db')
    conn.execute('DELETE FROM messages WHERE chat_id = ?', (chat_id,))
    conn.execute('DELETE FROM chats WHERE id = ?', (chat_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/history/<int:chat_id>', methods=['GET'])
def get_history(chat_id):
    conn = sqlite3.connect('kayserai.db')
    msgs = conn.execute('SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id ASC', (chat_id,)).fetchall()
    conn.close()
    return jsonify([{'role': m[0], 'content': m[1]} for m in msgs])

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    chat_id = data.get('chat_id')
    user_msg = data.get('message')
    conn = sqlite3.connect('kayserai.db')
    if not chat_id:
        c = conn.cursor()
        c.execute('INSERT INTO chats (title, created_at) VALUES (?, ?)', (user_msg[:20], datetime.datetime.now()))
        chat_id = c.lastrowid
    
    conn.execute('INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)', (chat_id, 'user', user_msg))
    
    ai_msg = "Sistem yoğun."
    for m in MODELS:
        try:
            res = client.models.generate_content(model=m, contents=user_msg)
            ai_msg = res.text
            break
        except Exception: continue
    
    conn.execute('INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)', (chat_id, 'model', ai_msg))
    conn.commit()
    conn.close()
    return jsonify({'reply': ai_msg, 'chat_id': chat_id})

if __name__ == '__main__':
    # host='0.0.0.0' kodu, uygulamanı dış dünyaya (yani Wi-Fi'na) açar
    app.run(host='0.0.0.0', port=5000, debug=True)