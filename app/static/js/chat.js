/* chat.js — Sport AI chat interface */
const form = document.getElementById('chatForm');
const input = document.getElementById('messageInput');
const messagesEl = document.getElementById('messages');
const sendBtn = document.getElementById('sendBtn');
const newChatBtn = document.getElementById('newChatBtn');
const sessionList = document.getElementById('sessionList');

// Auto-resize textarea
input.addEventListener('input', () => {
  input.style.height = 'auto';
  input.style.height = Math.min(input.scrollHeight, 140) + 'px';
});

// Submit on Enter (Shift+Enter for newline)
input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); form.dispatchEvent(new Event('submit')); }
});

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  appendMessage('user', message);
  input.value = '';
  input.style.height = 'auto';
  sendBtn.disabled = true;

  const typingEl = appendTyping();

  try {
    const res = await fetch('/api/v1/chat/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${ACCESS_TOKEN}` },
      body: JSON.stringify({ message, session_id: currentSessionId || null }),
    });

    typingEl.remove();

    if (res.status === 401) { window.location.href = '/login'; return; }
    if (!res.ok) {
      const err = await res.json();
      appendMessage('assistant', '⚠️ ' + (err.detail || 'Xato yuz berdi'));
      return;
    }

    const data = await res.json();
    if (!currentSessionId) {
      currentSessionId = data.session_id;
      // Add to session list
      const li = document.createElement('li');
      li.className = 'session-item active';
      li.dataset.id = data.session_id;
      li.textContent = message.substring(0, 40);
      // Deactivate others
      document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));
      sessionList.prepend(li);
      li.addEventListener('click', () => loadSession(data.session_id));
    }
    appendMessage('assistant', data.answer);
  } catch (err) {
    typingEl.remove();
    appendMessage('assistant', '⚠️ Tarmoq xatosi. Qayta urinib ko\'ring.');
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
});

newChatBtn.addEventListener('click', () => {
  currentSessionId = '';
  messagesEl.innerHTML = `
    <div class="welcome-msg">
      <h2>Yangi suhbat</h2>
      <p>Sport haqida savol bering.</p>
    </div>`;
  document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));
  input.focus();
});

// Click on session
document.querySelectorAll('.session-item').forEach(el => {
  el.addEventListener('click', () => loadSession(el.dataset.id));
});

async function loadSession(sessionId) {
  currentSessionId = sessionId;
  document.querySelectorAll('.session-item').forEach(el =>
    el.classList.toggle('active', el.dataset.id === sessionId));

  messagesEl.innerHTML = '<div style="color:var(--text-muted);padding:16px">Yuklanmoqda...</div>';

  const res = await fetch(`/api/v1/chat/sessions/${sessionId}/messages`, {
    headers: { Authorization: `Bearer ${ACCESS_TOKEN}` },
  });
  if (!res.ok) return;
  const msgs = await res.json();
  messagesEl.innerHTML = '';
  msgs.forEach(m => appendMessage(m.role, m.content));
  scrollToBottom();
}

function appendMessage(role, content) {
  const div = document.createElement('div');
  div.className = `message ${role}`;
  const inner = document.createElement('div');
  inner.className = 'message-content';
  inner.textContent = content;
  div.appendChild(inner);
  messagesEl.appendChild(div);
  scrollToBottom();
  return div;
}

function appendTyping() {
  const div = document.createElement('div');
  div.className = 'message assistant typing-indicator';
  div.innerHTML = '<div class="message-content">Yozmoqda...</div>';
  messagesEl.appendChild(div);
  scrollToBottom();
  return div;
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}
