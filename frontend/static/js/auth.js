const API = '/api/users';

// ── Modal HTML ────────────────────────────────────────────────────────
function crearModal() {
  if (document.getElementById('auth-modal')) return;
  document.body.insertAdjacentHTML('beforeend', `
    <div id="auth-modal" class="modal-overlay" onclick="cerrarModal(event)">
      <div class="modal-box">
        <button class="modal-close" onclick="document.getElementById('auth-modal').remove()">✕</button>

        <div id="tab-btns" style="display:flex;gap:0;margin-bottom:1.5rem;border-radius:8px;overflow:hidden;border:1px solid #ddd">
          <button id="tab-login" class="tab-btn tab-active" onclick="mostrarTab('login')">Iniciar sesión</button>
          <button id="tab-register" class="tab-btn" onclick="mostrarTab('register')">Registrarse</button>
        </div>

        <!-- LOGIN -->
        <div id="form-login">
          <div class="input-group">
            <label>Usuario</label>
            <input id="login-user" type="text" placeholder="Tu nombre de usuario">
          </div>
          <div class="input-group">
            <label>Contraseña</label>
            <input id="login-pass" type="password" placeholder="Tu contraseña">
          </div>
          <p id="login-error" class="form-error"></p>
          <button class="btn-primary" onclick="hacerLogin()">Entrar</button>
        </div>

        <!-- REGISTRO -->
        <div id="form-register" style="display:none">
          <div class="input-group">
            <label>Usuario</label>
            <input id="reg-user" type="text" placeholder="Elige un nombre de usuario">
          </div>
          <div class="input-group">
            <label>Email</label>
            <input id="reg-email" type="email" placeholder="tu@email.com">
          </div>
          <div class="input-group">
            <label>Contraseña</label>
            <input id="reg-pass" type="password" placeholder="Mínimo 6 caracteres">
          </div>
          <p id="reg-error" class="form-error"></p>
          <button class="btn-primary" onclick="hacerRegistro()">Crear cuenta</button>
        </div>
      </div>
    </div>
  `);
}

function mostrarTab(tab) {
  document.getElementById('form-login').style.display    = tab === 'login'    ? 'block' : 'none';
  document.getElementById('form-register').style.display = tab === 'register' ? 'block' : 'none';
  document.getElementById('tab-login').classList.toggle('tab-active',    tab === 'login');
  document.getElementById('tab-register').classList.toggle('tab-active', tab === 'register');
}

function cerrarModal(e) {
  if (e.target.id === 'auth-modal') document.getElementById('auth-modal').remove();
}

function showAuthModal() { crearModal(); }

// ── Login ─────────────────────────────────────────────────────────────
async function hacerLogin() {
  const username = document.getElementById('login-user').value.trim();
  const password = document.getElementById('login-pass').value;
  const errEl    = document.getElementById('login-error');
  errEl.textContent = '';

  if (!username || !password) { errEl.textContent = 'Rellena todos los campos.'; return; }

  const res  = await fetch(`${API}/login/`, {
    method: 'POST', credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
    body: JSON.stringify({ username, password })
  });
  const data = await res.json();
  if (res.ok) {
    document.getElementById('auth-modal').remove();
    location.reload();
  } else {
    errEl.textContent = data.error || 'Credenciales incorrectas.';
  }
}

// ── Registro ──────────────────────────────────────────────────────────
async function hacerRegistro() {
  const username = document.getElementById('reg-user').value.trim();
  const email    = document.getElementById('reg-email').value.trim();
  const password = document.getElementById('reg-pass').value;
  const errEl    = document.getElementById('reg-error');
  errEl.textContent = '';

  if (!username || !password) { errEl.textContent = 'Usuario y contraseña son obligatorios.'; return; }
  if (password.length < 6)    { errEl.textContent = 'La contraseña debe tener al menos 6 caracteres.'; return; }

  const res  = await fetch(`${API}/register/`, {
    method: 'POST', credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
    body: JSON.stringify({ username, email, password })
  });
  const data = await res.json();
if (res.ok) {
  mostrarTab('login');
  const loginErr = document.getElementById('login-error');
  loginErr.textContent = '📧 Cuenta creada. Revisa tu email para verificarla antes de iniciar sesión.';
  loginErr.style.color = '#16a34a';

  } else {
    const msgs = Object.values(data).flat().join(' ');
    errEl.textContent = msgs || 'Error al registrarse.';
  }
}

// ── Logout ────────────────────────────────────────────────────────────
async function logoutUser() {
  await fetch(`${API}/logout/`, {
    method: 'POST', credentials: 'include',
    headers: { 'X-CSRFToken': getCookie('csrftoken') }
  });
  location.href = '/';
}
// ── Toast notifications ───────────────────────────────────────
function showToast(mensaje, tipo = 'success', duracion = 3000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const iconos = { success: '✅', error: '❌', info: 'ℹ️' };
  const toast  = document.createElement('div');
  toast.className = `toast ${tipo}`;
  toast.innerHTML = `
    <span class="toast-icon">${iconos[tipo] || '✅'}</span>
    <span class="toast-msg">${mensaje}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'toast-out .25s ease forwards';
    setTimeout(() => toast.remove(), 250);
  }, duracion);
}

// ── Sesión ────────────────────────────────────────────────────────────
async function checkSession() {
  try {
    const res = await fetch(`${API}/me/`, { credentials: 'include' });
    const nav = document.getElementById('nav-user');
    if (res.ok) {
      const user = await res.json();
      const favsRes = await fetch(`${API}/favoritos/`, { credentials: 'include' });
      const favs    = await favsRes.json();
      const historial = (() => {
        try { return JSON.parse(localStorage.getItem('apihub_historial')) || []; } catch { return []; }
      })();
      // Renderizar dropdown con info del usuario
      nav.innerHTML = `
        <div class="nav-perfil" id="nav-perfil">
          <div class="nav-avatar" onclick="toggleDropdown()" id="nav-avatar-btn">
            <span class="avatar-inicial">${user.username[0].toUpperCase()}</span>
          </div>
          <div class="nav-dropdown" id="nav-dropdown">
            <div class="dropdown-header">
              <div class="dropdown-avatar">${user.username[0].toUpperCase()}</div>
              <div class="dropdown-info">
                <strong>${user.username}</strong>
                <span>${user.email || 'Sin email'}</span>
              </div>
            </div>
            <div class="dropdown-stats">
              <div class="dropdown-stat">
                <strong>${favs.length}</strong>
                <span>Favoritos</span>
              </div>
              <div class="dropdown-stat">
                <strong>${historial.length}</strong>
                <span>Peticiones</span>
              </div>
            </div>
            <div class="dropdown-links">
              <a href="/perfil/?tab=favoritos" class="dropdown-link">⭐ Mis favoritos</a>
              <a href="/perfil/?tab=historial" class="dropdown-link">🕐 Historial</a>
              <a href="/perfil/?tab=ajustes" class="dropdown-link">⚙️ Ajustes de cuenta</a>
            </div>
            <button class="dropdown-logout" onclick="logoutUser()">Cerrar sesión</button>
          </div>
        </div>`;

      // Cerrar dropdown al hacer click fuera
      document.addEventListener('click', e => {
        const perfil = document.getElementById('nav-perfil');
        if (perfil && !perfil.contains(e.target)) {
          document.getElementById('nav-dropdown')?.classList.remove('activo');
        }
      });

    } else {
      nav.innerHTML = `<a href="#" onclick="showAuthModal()" class="btn-nav-login">Iniciar sesión</a>`;
    }
  } catch(e) {}
}

function toggleDropdown() {
  document.getElementById('nav-dropdown').classList.toggle('activo');
}

function getCookie(name) {
  return document.cookie.split(';')
    .map(c => c.trim()).find(c => c.startsWith(name + '='))
    ?.split('=')[1] || '';
}

// ── Tema oscuro ───────────────────────────────────────────────
function toggleTema() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const nuevo  = isDark ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', nuevo);
  localStorage.setItem('tema', nuevo);
  document.getElementById('btn-tema').textContent = nuevo === 'dark' ? '☀️' : '🌙';
}

// Aplicar tema guardado al cargar
(function() {
  const tema = localStorage.getItem('tema') || 'light';
  if (tema === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
    document.addEventListener('DOMContentLoaded', () => {
      const btn = document.getElementById('btn-tema');
      if (btn) btn.textContent = '☀️';
    });
  }
})();
checkSession();