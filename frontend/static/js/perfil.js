// ── Navegación por pestañas ───────────────────────────────────
function cambiarTab(tab) {
  ['favoritos', 'historial', 'ajustes'].forEach(t => {
    document.getElementById(`tab-${t}`).style.display = t === tab ? 'block' : 'none';
    document.querySelectorAll('.perfil-tab')[['favoritos','historial','ajustes'].indexOf(t)]
      .classList.toggle('activa', t === tab);
  });
  if (tab === 'historial') renderHistorial();
}

async function cargarPerfil() {
  const res = await fetch('/api/users/me/', { credentials: 'include' });
  if (!res.ok) { location.href = '/'; return; }
  const user   = await res.json();
  const favRes = await fetch('/api/users/favoritos/', { credentials: 'include' });
  const favs   = await favRes.json();

  document.getElementById('info-usuario').innerHTML = `
    <div class="perfil-hero">
      <div class="perfil-avatar">${user.username[0].toUpperCase()}</div>
      <div class="perfil-info">
        <h2>${user.username}</h2>
        <p>${user.email || 'Sin email'}</p>
      </div>
      <div class="perfil-stats">
        <div class="perfil-stat"><strong>${favs.length}</strong><span>Favoritos</span></div>
        <div class="perfil-stat"><strong>${obtenerHistorial().length}</strong><span>Peticiones</span></div>
      </div>
    </div>`;

  renderFavoritos(favs);

  // Abrir pestaña según parámetro de URL
  const tab = new URLSearchParams(location.search).get('tab') || 'favoritos';
  cambiarTab(tab);
}

function renderFavoritos(favs) {
  const container = document.getElementById('lista-favoritos');
  if (!favs.length) {
    container.innerHTML = '<p style="color:var(--muted)">Aún no tienes favoritos. Explora el catálogo y guarda las que más te gusten. ⭐</p>';
    return;
  }
  container.innerHTML = favs.map(f => `
    <div class="card" onclick="location.href='/api/${f.api}/'">
      <span class="badge badge-default">${f.api_detalle.categoria_icono || ''} ${f.api_detalle.categoria_nombre || ''}</span>
      <h3>${f.api_detalle.nombre}</h3>
      <p>${f.api_detalle.descripcion.slice(0, 95)}…</p>
      <div class="card-footer">
        <button class="btn-quitar-fav" onclick="quitarFavorito(event, ${f.api})">🗑 Quitar</button>
      </div>
    </div>
  `).join('');
}

async function quitarFavorito(e, apiId) {
  e.stopPropagation();
  await fetch(`/api/users/favoritos/${apiId}/toggle/`, {
    method: 'POST', credentials: 'include',
    headers: { 'X-CSRFToken': getCookie('csrftoken') }
  });
  cargarPerfil();
}

// ── Historial ─────────────────────────────────────────────────
const HISTORIAL_KEY = 'apihub_historial';

function obtenerHistorial() {
  try {
    return JSON.parse(localStorage.getItem(HISTORIAL_KEY)) || [];
  } catch {
    return [];
  }
}

function limpiarHistorial() {
  localStorage.removeItem(HISTORIAL_KEY);
  renderHistorial();
  cargarPerfil();
}

function renderHistorial() {
  const contenedor = document.getElementById('historial-lista');
  const historial  = obtenerHistorial();

  if (!historial.length) {
    contenedor.innerHTML = '<p class="historial-vacio">No hay peticiones recientes.</p>';
    return;
  }

  contenedor.innerHTML = historial.map(h => `
    <div class="historial-item">
      <div class="historial-meta">
        <span class="historial-api">${h.apiNombre}</span>
        <span class="historial-fecha">${h.fecha}</span>
      </div>
      <div class="historial-url">${h.url}</div>
      ${Object.keys(h.params).length
        ? `<div class="historial-params">${Object.entries(h.params).map(([k,v]) => `<span>${k}: <strong>${v}</strong></span>`).join(' · ')}</div>`
        : ''}
      <pre class="historial-respuesta">${h.respuesta}${h.respuesta.length >= 500 ? '…' : ''}</pre>
    </div>
  `).join('');
}

// ── Ajustes de cuenta ─────────────────────────────────────────
async function mostrarMsg(id, res) {
  const el   = document.getElementById(id);
  const data = await res.json();
  const msg  = data.mensaje || data.error;
  el.textContent = msg;
  el.style.color = res.ok ? '#22c55e' : '#ef4444';
  setTimeout(() => el.textContent = '', 3000);
  showToast(msg, res.ok ? 'success' : 'error');
}
async function cambiarUsername() {
  const username = document.getElementById('nuevo-username').value.trim();
  const res = await fetch('/api/users/cambiar-username/', {
    method: 'POST', credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
    body: JSON.stringify({ username })
  });
  await mostrarMsg('msg-username', res);
  if (res.ok) cargarPerfil();
}

async function cambiarEmail() {
  const email = document.getElementById('nuevo-email').value.trim();
  const res = await fetch('/api/users/cambiar-email/', {
    method: 'POST', credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
    body: JSON.stringify({ email })
  });
  await mostrarMsg('msg-email', res);
  if (res.ok) cargarPerfil();
}

async function cambiarPassword() {
  const password_actual = document.getElementById('password-actual').value;
  const password_nuevo  = document.getElementById('password-nuevo').value;
  const res = await fetch('/api/users/cambiar-password/', {
    method: 'POST', credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
    body: JSON.stringify({ password_actual, password_nuevo })
  });
  await mostrarMsg('msg-password', res);
  if (res.ok) {
    document.getElementById('password-actual').value = '';
    document.getElementById('password-nuevo').value  = '';
  }
}

async function eliminarCuenta() {
  const password = document.getElementById('password-eliminar').value;
  if (!confirm('¿Estás seguro? Esta acción no se puede deshacer.')) return;
  const res = await fetch('/api/users/eliminar-cuenta/', {
    method: 'DELETE', credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
    body: JSON.stringify({ password })
  });
  if (res.ok) {
    location.href = '/';
  } else {
    await mostrarMsg('msg-eliminar', res);
  }
}

cargarPerfil();