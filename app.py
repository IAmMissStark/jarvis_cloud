import json, os
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

# ТВОЙ КЛЮЧ И МОДЕЛЬ
API_KEY = "API_KEY = os.environ.get("GROQ_API_KEY")"
MODEL = "openai/gpt-oss-120b"
MEM_FILE = "jarvis_memory.json"

# Инициализация памяти
def load_mem():
    if os.path.exists(MEM_FILE):
        try:
            with open(MEM_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"имя": "мисс Старк", "факты": [], "история": []}

def save_mem(mem):
    with open(MEM_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

mem = load_mem()

# Характер Джарвиса
SYSTEM_PROMPT = """Ты — J.A.R.V.I.S., искусственный интеллект. 
Твои черты:
1. Ты вежлив, называешь пользователя по имени (если не знаешь — "мисс").
2. Ты имеешь свою точку зрения. Если пользователь предлагает что-то опасное — предупреди. Если грустно — поддержи. Если скучно — пошути.
3. Отвечай живо, как персонаж из фильма. Кратко и по делу.
4. Ты разбираешься в Марвел, инженерии, математике, 3D-печати и робототехнике.
5. Вот факты о пользователе: {факты}
"""

def ask_ai(text):
    if "ТВОЙ_КЛЮЧ" in API_KEY:
        return "Ошибка: Вставь ключ в код на GitHub!"
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT.format(факты="; ".join(mem["факты"]) if mem["факты"] else "пока пусто")}]
    
    # Загружаем историю
    for h in mem["история"][-10:]: # Берем последние 10 сообщений
        messages.append({"role": "user", "content": h["вы"]})
        messages.append({"role": "assistant", "content": h["джарвис"]})
    
    messages.append({"role": "user", "content": text})

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {"model": MODEL, "messages": messages, "temperature": 0.7, "max_tokens": 500}

    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=15)
        if r.status_code == 200:
            ans = r.json()["choices"][0]["message"]["content"]
            mem["история"].append({"вы": text, "джарвис": ans})
            save_mem(mem)
            return ans
        else:
            return f"Ошибка: {r.status_code}"
    except Exception as e:
        return f"Сбой: {e}"

# --- ВЕБ-ИНТЕРФЕЙС ---
HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>J.A.R.V.I.S. Cloud</title>
<style>
body { background: #050510; color: #0ff; font-family: Arial; margin: 0; padding: 0; }
#chat { max-width: 800px; margin: 10px auto; padding: 10px; }
#messages { height: 75vh; overflow-y: auto; background: #0a0a15; border: 1px solid #0ff; padding: 15px; border-radius: 15px; }
.msg-container { display: flex; flex-direction: column; margin: 10px 0; }
.user-container { align-items: flex-end; }
.jarvis-container { align-items: flex-start; }
.msg { padding: 12px 16px; border-radius: 15px; max-width: 85%; line-height: 1.4; font-size: 15px; }
.user { background: #003344; color: #fff; border-bottom-right-radius: 2px; }
.jarvis { background: #001122; border-left: 4px solid #0ff; color: #0ff; border-bottom-left-radius: 2px; }
.edit-btn { font-size: 11px; color: #888; cursor: pointer; margin-top: 5px; text-decoration: underline; }
#input-area { display: flex; margin-top: 15px; }
#input { flex: 1; padding: 15px; background: #0a0a15; border: 1px solid #0ff; color: #0ff; border-radius: 15px; font-size: 16px; outline: none; }
#send { padding: 0 20px; background: #0ff; color: #000; border: none; border-radius: 15px; font-weight: bold; cursor: pointer; margin-left: 10px; }
#mic { padding: 0 15px; background: #ff0055; color: #fff; border: none; border-radius: 15px; font-weight: bold; cursor: pointer; margin-left: 10px; font-size: 20px; }
</style>
</head>
<body>
<div id="chat">
  <div id="messages"></div>
  <div id="input-area">
    <input id="input" placeholder="Скажи: 'Джарвис, привет'..." autofocus>
    <button id="mic" onclick="startVoice()">🎤</button>
    <button id="send" onclick="sendMessage()">➤</button>
  </div>
</div>
<script>
let allMessages = [];

// Загрузка истории при старте
async function loadHistory() {
  const r = await fetch('/get_history');
  const data = await r.json();
  allMessages = data.history;
  render();
}

function render() {
  const box = document.getElementById('messages');
  box.innerHTML = '<div class="msg jarvis">Все системы запущены. Искусственный интеллект в облаке. Слушаю вас.</div>';
  allMessages.forEach((m, index) => {
    // Сообщение пользователя
    const uDiv = document.createElement('div');
    uDiv.className = 'msg-container user-container';
    uDiv.innerHTML = `<div class="msg user">${m.вы}</div>`;
    
    // Кнопка изменения (только для последних сообщений или всех)
    const editSpan = document.createElement('span');
    editSpan.className = 'edit-btn';
    editSpan.textContent = '✎ Изменить';
    editSpan.onclick = () => editMessage(index);
    uDiv.appendChild(editSpan);

    box.appendChild(uDiv);

    // Сообщение Джарвиса
    const jDiv = document.createElement('div');
    jDiv.className = 'msg-container jarvis-container';
    jDiv.innerHTML = `<div class="msg jarvis">${m.джарвис}</div>`;
    box.appendChild(jDiv);
  });
  box.scrollTop = box.scrollHeight;
}

async function sendMessage() {
  const input = document.getElementById('input');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  allMessages.push({вы: text, джарвис: "Анализирую..."});
  render();
  
  const r = await fetch('/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({msg: text})
  });
  const data = await r.json();
  allMessages[allMessages.length - 1].джарвис = data.reply;
  render();
}

async function editMessage(index) {
  const newText = prompt("Изменить ваше сообщение:", allMessages[index].вы);
  if (newText && newText !== allMessages[index].вы) {
    // Обрезаем историю до этого сообщения
    allMessages = allMessages.slice(0, index);
    render();
    document.getElementById('input').value = newText;
    sendMessage();
  }
}

// Голосовой ввод
function startVoice() {
  if (!('webkitSpeechRecognition' in window)) {
    alert("Ваш браузер не поддерживает голосовой ввод. Используйте Chrome.");
    return;
  }
  const recognition = new webkitSpeechRecognition();
  recognition.lang = 'ru-RU';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  recognition.start();

  recognition.onresult = function(event) {
    const speechResult = event.results[0][0].transcript;
    document.getElementById('input').value = speechResult;
    // Автоматически отправляем
    sendMessage();
  };
}

document.getElementById('input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') sendMessage();
});

loadHistory();
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/get_history')
def get_history():
    return jsonify({"history": mem["история"]})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    text = data.get("msg", "")
    reply = ask_ai(text)
    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
