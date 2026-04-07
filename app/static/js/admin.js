/* admin.js — Admin panel helpers */

function openModal(id) { document.getElementById(id).classList.remove('hidden'); }
function closeModal(id) { document.getElementById(id).classList.add('hidden'); }

// Close modal on backdrop click
document.querySelectorAll('.modal').forEach(m => {
  m.addEventListener('click', (e) => { if (e.target === m) m.classList.add('hidden'); });
});

async function apiDelete(url) {
  const res = await fetch(url, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${ACCESS_TOKEN}` },
  });
  if (res.status === 401) { window.location.href = '/login'; return false; }
  if (!res.ok) {
    const e = await res.json().catch(() => ({}));
    alert(e.detail || "Xato yuz berdi");
    return false;
  }
  return true;
}

async function apiPost(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${ACCESS_TOKEN}` },
    body: JSON.stringify(body),
  });
  if (res.status === 401) { window.location.href = '/login'; return null; }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) { alert(data.detail || "Xato yuz berdi"); return null; }
  return data;
}

function formToObj(formEl) {
  const obj = {};
  new FormData(formEl).forEach((v, k) => { if (v !== '') obj[k] = v; });
  return obj;
}

// ── Athletes ──────────────────────────────────────
async function deleteAthlete(id) {
  if (!confirm('Sportchini o\'chirasizmi?')) return;
  if (await apiDelete(`/api/v1/athletes/${id}`)) location.reload();
}

const addAthleteForm = document.getElementById('addAthleteForm');
if (addAthleteForm) {
  addAthleteForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const body = formToObj(addAthleteForm);
    if (body.coach_id) body.coach_id = parseInt(body.coach_id);
    if (await apiPost('/api/v1/athletes', body)) location.reload();
  });
}

// ── Coaches ───────────────────────────────────────
async function deleteCoach(id) {
  if (!confirm('Trenerni o\'chirasizmi?')) return;
  if (await apiDelete(`/api/v1/coaches/${id}`)) location.reload();
}

const addCoachForm = document.getElementById('addCoachForm');
if (addCoachForm) {
  addCoachForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const body = formToObj(addCoachForm);
    body.experience_years = parseInt(body.experience_years);
    if (await apiPost('/api/v1/coaches', body)) location.reload();
  });
}

// ── Competitions ──────────────────────────────────
async function deleteCompetition(id) {
  if (!confirm('Musobaqani o\'chirasizmi?')) return;
  if (await apiDelete(`/api/v1/competitions/${id}`)) location.reload();
}

const addCompetitionForm = document.getElementById('addCompetitionForm');
if (addCompetitionForm) {
  addCompetitionForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (await apiPost('/api/v1/competitions', formToObj(addCompetitionForm))) location.reload();
  });
}

// ── Results ───────────────────────────────────────
async function deleteResult(id) {
  if (!confirm('Natijani o\'chirasizmi?')) return;
  if (await apiDelete(`/api/v1/results/${id}`)) location.reload();
}

const addResultForm = document.getElementById('addResultForm');
if (addResultForm) {
  addResultForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const body = formToObj(addResultForm);
    body.athlete_id = parseInt(body.athlete_id);
    body.competition_id = parseInt(body.competition_id);
    body.year = parseInt(body.year);
    if (body.place) body.place = parseInt(body.place);
    if (body.score) body.score = parseFloat(body.score);
    if (await apiPost('/api/v1/results', body)) location.reload();
  });
}

// ── Users ─────────────────────────────────────────
const addUserForm = document.getElementById('addUserForm');
if (addUserForm) {
  addUserForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (await apiPost('/api/v1/admin/users', formToObj(addUserForm))) location.reload();
  });
}
