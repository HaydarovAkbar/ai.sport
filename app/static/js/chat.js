/* chat.js — Sport AI chat interface (job-based polling) */

const form        = document.getElementById('chatForm');
const input       = document.getElementById('messageInput');
const messagesEl  = document.getElementById('messages');
const sendBtn     = document.getElementById('sendBtn');
const newChatBtn  = document.getElementById('newChatBtn');
const sessionList = document.getElementById('sessionList');

const POLL_INTERVAL_MS = 1500;   // poll every 1.5 s
const POLL_MAX_TRIES   = 80;     // give up after ~2 min

// Auto-resize textarea
input.addEventListener('input', () => {
  input.style.height = 'auto';
  input.style.height = Math.min(input.scrollHeight, 140) + 'px';
});

// Enter = submit, Shift+Enter = newline
input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    form.dispatchEvent(new Event('submit'));
  }
});

// ── Main submit ───────────────────────────────────────────────────────

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
    // Step 1: POST /chat/message → 202 {job_id, session_id}
    const res = await fetch('/api/v1/chat/message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${ACCESS_TOKEN}`,
      },
      body: JSON.stringify({ message, session_id: currentSessionId || null }),
    });

    if (res.status === 401) { window.location.href = '/login'; return; }

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      typingEl.remove();
      appendMessage('assistant', '⚠️ ' + (err.detail || 'Xato yuz berdi'));
      sendBtn.disabled = false;
      return;
    }

    const { job_id, session_id } = await res.json();

    // Register session in sidebar on first message
    if (!currentSessionId) {
      currentSessionId = session_id;
      addSessionToSidebar(session_id, message.substring(0, 40));
    }

    // Step 2: Poll until job completes
    await pollJob(job_id, typingEl);

  } catch {
    typingEl.remove();
    appendMessage('assistant', "⚠️ Tarmoq xatosi. Qayta urinib ko'ring.");
    sendBtn.disabled = false;
  }
});

// ── Polling ───────────────────────────────────────────────────────────

function pollJob(jobId, typingEl) {
  return new Promise((resolve) => {
    let tries = 0;

    const timer = setInterval(async () => {
      tries++;
      try {
        const res = await fetch(`/api/v1/chat/jobs/${jobId}`, {
          headers: { Authorization: `Bearer ${ACCESS_TOKEN}` },
        });

        if (res.status === 401) {
          clearInterval(timer);
          window.location.href = '/login';
          resolve();
          return;
        }

        if (!res.ok) {
          clearInterval(timer);
          typingEl.remove();
          appendMessage('assistant', '⚠️ Server xatosi');
          sendBtn.disabled = false;
          resolve();
          return;
        }

        const data = await res.json();

        if (data.status === 'complete') {
          clearInterval(timer);
          typingEl.remove();
          appendMessage('assistant', data.answer);
          sendBtn.disabled = false;
          resolve();

        } else if (data.status === 'failed') {
          clearInterval(timer);
          typingEl.remove();
          appendMessage('assistant', '⚠️ ' + (data.error || 'Jarayon xatosi'));
          sendBtn.disabled = false;
          resolve();

        } else if (tries >= POLL_MAX_TRIES) {
          clearInterval(timer);
          typingEl.remove();
          appendMessage('assistant', "⚠️ Javob vaqti tugadi. Qayta urinib ko'ring.");
          sendBtn.disabled = false;
          resolve();
        }
        // queued / in_progress → keep polling

      } catch {
        // network blip — keep polling
      }
    }, POLL_INTERVAL_MS);
  });
}

// ── New chat ──────────────────────────────────────────────────────────

newChatBtn.addEventListener('click', () => {
  currentSessionId = '';
  messagesEl.innerHTML = `
    <div class="welcome-msg">
      <h2>Yangi suhbat</h2>
      <p>Sport haqida savol bering.</p>
    </div>`;
  document.querySelectorAll('.session-item').forEach(el =>
    el.classList.remove('active'));
  input.focus();
});

// ── Session sidebar ───────────────────────────────────────────────────

document.querySelectorAll('.session-item').forEach(el => {
  el.addEventListener('click', () => loadSession(el.dataset.id));
});

async function loadSession(sessionId) {
  currentSessionId = sessionId;
  document.querySelectorAll('.session-item').forEach(el =>
    el.classList.toggle('active', el.dataset.id === sessionId));

  messagesEl.innerHTML =
    '<div style="color:var(--text-muted);padding:16px">Yuklanmoqda...</div>';

  const res = await fetch(`/api/v1/chat/sessions/${sessionId}/messages`, {
    headers: { Authorization: `Bearer ${ACCESS_TOKEN}` },
  });
  if (!res.ok) return;

  const msgs = await res.json();
  messagesEl.innerHTML = '';
  msgs.forEach(m => appendMessage(m.role, m.content));
  scrollToBottom();
}

// ── Helpers ───────────────────────────────────────────────────────────

function addSessionToSidebar(sessionId, title) {
  document.querySelectorAll('.session-item').forEach(el =>
    el.classList.remove('active'));
  const li = document.createElement('li');
  li.className = 'session-item active';
  li.dataset.id = sessionId;
  li.textContent = title;
  li.addEventListener('click', () => loadSession(sessionId));
  sessionList.prepend(li);
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
  div.innerHTML = '<div class="message-content">Javob tayyorlanmoqda...</div>';
  messagesEl.appendChild(div);
  scrollToBottom();
  return div;
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}
