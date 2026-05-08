const apiId = location.pathname.split('/').filter(Boolean)[1];
let mapInstance = null;

const BADGE_CLASES = {
  'entretenimiento':   'badge-entretenimiento',
  'meteorologia':      'badge-meteorologia',
  'meteorología':      'badge-meteorologia',
  'geografia':         'badge-geografia',
  'geografía':         'badge-geografia',
  'ciencia y espacio': 'badge-ciencia',
  'gastronomia':       'badge-gastronomia',
  'gastronomía':       'badge-gastronomia',
  'criptomonedas':     'badge-criptomonedas',
};

function badgeClass(nombre) {
  return BADGE_CLASES[(nombre || '').toLowerCase().trim()] || 'badge-default';
}

async function cargarApi() {
  const res = await fetch(`/api/apis/${apiId}/`);
  const api = await res.json();

  document.title = `${api.nombre} — API Hub`;

  document.getElementById('api-info').innerHTML = `
    <div class="api-visitas-badge">👁 ${api.total_visitas || 0} visitas</div>
    <span class="badge ${badgeClass(api.categoria_nombre)}">${api.categoria_icono || ''} ${api.categoria_nombre}</span>
    <h1>${api.nombre}</h1>
    <p>${api.descripcion}</p>
<div class="api-meta">
      <div class="api-meta-item"><strong>URL base:</strong> <code>${api.url_base}</code></div>
      <div class="api-meta-item"><strong>Autenticación:</strong> ${
        api.auth_tipo === 'none'   ? '🔓 Libre' :
        api.auth_tipo === 'apikey' ? '🔑 API Key' : '🔐 OAuth'
      }</div>
      <div class="api-meta-item"><strong>Visitas:</strong> 👁 ${api.total_visitas || 0}</div>
    </div>
    <div class="api-actions">
      ${api.documentacion_url
        ? `<a href="${api.documentacion_url}" target="_blank" class="btn-doc">📄 Documentación oficial</a>`
        : ''}
      <button id="btn-favorito" onclick="toggleFavorito()">⭐ Guardar en favoritos</button>
    </div>
  `;

  const params    = api.parametros_ejemplo || {};
  const container = document.getElementById('params-container');
  container.dataset.endpoint   = api.ejemplo_endpoint || '';
  container.dataset.urlBase    = api.url_base;
  container.dataset.params     = JSON.stringify(Object.keys(params));
  container.dataset.renderTipo = api.render_tipo || 'json';

  if (Object.keys(params).length === 0) {
    container.innerHTML = '<p style="color:var(--muted);font-size:.88rem;margin-bottom:.5rem">Esta API no requiere parámetros.</p>';
  } else {
    container.innerHTML = Object.entries(params).map(([k, v]) => `
      <div class="param-group">
        <label>${k}</label>
        <input id="param-${k}" value="${v}" placeholder="${v}">
      </div>
    `).join('');
  }

  // Cargar valoración del usuario si está logueado
  let miVoto = null;
  const vRes = await fetch(`/api/users/mi-valoracion/${apiId}/`, { credentials: 'include' });
  if (vRes.ok) {
    const vData = await vRes.json();
    miVoto = vData.puntuacion;
  }
  renderEstrellas(api.valoracion_media, api.total_valoraciones, miVoto);
  // Checkbox modo seguro para JokeAPI
if (api.render_tipo === 'joke') {
  container.innerHTML += `
    <div class="param-group">
      <label class="filtro-check" style="margin-top:.5rem">
        <input type="checkbox" id="param-safe-mode" checked>
        🛡️ Modo seguro activado
      </label>
    </div>`;
}
  // Comprobar si la API ya está en favoritos al cargar
  const favRes = await fetch('/api/users/favoritos/', { credentials: 'include' });
  if (favRes.ok) {
    const favs = await favRes.json();
    const esFavorito = favs.some(f => f.api === parseInt(apiId));
    const btn = document.getElementById('btn-favorito');
    if (esFavorito) {
      btn.textContent       = '💔 Eliminar de favoritos';
      btn.style.background  = '#f59e0b';
      btn.style.borderColor = '#f59e0b';
      btn.style.color       = '#fff';
    }
  }

  cargarRelacionadas(api.categoria, api.categoria_icono, api.categoria_nombre);
}

// ── Enviar petición ───────────────────────────────────────────
document.getElementById('btn-enviar').addEventListener('click', async () => {
  const container  = document.getElementById('params-container');
  const paramKeys  = JSON.parse(container.dataset.params || '[]');
  const params     = {};
  paramKeys.forEach(k => { params[k] = document.getElementById(`param-${k}`)?.value || ''; });

  // Sustituir variables en el endpoint con los valores de los parámetros
let endpoint = container.dataset.endpoint;
paramKeys.forEach(k => {
  if (endpoint.includes(`{${k}}`)) {
    endpoint = endpoint.replace(`{${k}}`, params[k]);
    delete params[k];
  }
});
const url = container.dataset.urlBase + endpoint;
  const renderTipo = container.dataset.renderTipo;
  const pre        = document.getElementById('respuesta');
  const btn        = document.getElementById('btn-enviar');
  // Modo seguro para JokeAPI
const safeModeCheck = document.getElementById('param-safe-mode');
if (safeModeCheck) {
  if (safeModeCheck.checked) {
    params['safe-mode'] = true;
  } else {
    delete params['safe-mode'];
  }
}

  btn.disabled    = true;
  btn.innerHTML   = '<span class="spinner"></span> Enviando...';
  pre.textContent = '';
  pre.style.color = '#94a3b8';

  try {
    const res = await fetch('/api/proxy/', {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify({ url, params })
    });
    const envelope = await res.json();
    const data     = envelope.data || envelope;

    pre.textContent = JSON.stringify(data, null, 2);
    pre.style.color = '#4ade80';
    guardarEnHistorial(
  document.title.replace(' — API Hub', ''),
  url,
  params,
  data
);
    document.getElementById('pre-wrapper').style.display = 'block';

    if (renderTipo !== 'json') renderVisual(renderTipo, data);

  } catch(e) {
    pre.textContent = `Error: ${e.message}`;
    pre.style.color = '#f87171';
  } finally {
    btn.disabled  = false;
    btn.innerHTML = '&#9654; Enviar petición';
  }
});

// ── Renderizado visual ────────────────────────────────────────
function renderVisual(tipo, data) {
  const seccion = document.getElementById('seccion-visual');
  const titulo  = document.getElementById('visual-titulo');
  const el      = document.getElementById('resultado-visual');

  seccion.style.display = 'block';

  switch(tipo) {

    case 'apod': {
  titulo.textContent = ' Imagen astronómica del día';
  const esVideo = data.media_type === 'video';
  el.innerHTML = `
    <div class="visual-card">
      <h3 style="font-size:1.3rem;margin-bottom:.5rem">${data.title}</h3>
      <p style="color:var(--muted);font-size:.85rem;margin-bottom:1rem">
         ${data.date} · 
        ${data.copyright ? `© ${data.copyright}` : 'Dominio público'}
      </p>
      ${esVideo
        ? `<iframe src="${data.url}" style="width:100%;height:400px;border-radius:12px;border:none" allowfullscreen></iframe>`
        : `<img src="${data.hdurl || data.url}" alt="${data.title}" style="width:100%;border-radius:12px;max-height:600px;object-fit:cover">`
      }
      <p style="margin-top:1rem;font-size:.9rem;line-height:1.6;color:var(--text)">${data.explanation}</p>
    </div>`;
  break;
}
case 'joke': {
  titulo.textContent = ' Vista previa';
  const esTwopart = data.type === 'twopart';

  el.innerHTML = `
    <div class="visual-card joke-card">
      <div class="joke-categoria">
        ${(data.flags?.nsfw ? '' : '✅ Safe')} 
        ${data.category ? `· ${data.category}` : ''}
      </div>
      ${esTwopart ? `
        <div class="joke-setup">${data.setup}</div>
        <div class="joke-reveal-wrapper">
          <button class="btn-reveal" onclick="
            this.style.display='none';
            this.nextElementSibling.style.display='block';
          ">🎭 Ver remate</button>
          <div class="joke-delivery" style="display:none">${data.delivery}</div>
        </div>
      ` : `
        <div class="joke-single">${data.joke}</div>
      `}
    </div>`;
  break;
}
    case 'pokemon': {
      titulo.textContent = ' Vista previa';
      const sprite = data.sprites?.other?.['official-artwork']?.front_default
                  || data.sprites?.front_default;
      const tipos  = (data.types || []).map(t =>
        `<span class="poke-type type-${t.type.name}">${t.type.name}</span>`
      ).join('');
      const stats  = (data.stats || []).map(s => {
        const pct = Math.min(s.base_stat, 150) / 1.5;
        const color = pct > 66 ? '#22c55e' : pct > 33 ? '#f59e0b' : '#ef4444';
        return `
          <div class="stat-bar">
            <span>${s.stat.name.replace('special-','sp.')}</span>
            <div class="bar">
              <div class="bar-fill" style="width:${pct}%;background:${color}">
                ${s.base_stat}
              </div>
            </div>
          </div>`;
      }).join('');

      el.innerHTML = `
        <div class="visual-card pokemon-card">
          <div class="pokemon-img-wrap">
            <img src="${sprite}" alt="${data.name}">
          </div>
          <div class="pokemon-info">
            <h3 style="text-transform:capitalize;font-size:1.6rem;margin-bottom:.3rem">
              ${data.name} <small style="color:var(--muted);font-weight:400">#${data.id}</small>
            </h3>
            <div style="margin-bottom:1rem">${tipos}</div>
            <div style="display:flex;gap:1rem;margin-bottom:1rem;font-size:.9rem;color:var(--muted)">
              <span>⚖️ ${data.weight / 10} kg</span>
              <span>📏 ${data.height / 10} m</span>
            </div>
            <div class="stats-grid">${stats}</div>
          </div>
        </div>`;
      break;
    }

    case 'iss': {
      titulo.textContent = ' Posición en tiempo real';
      const lat = parseFloat(data.iss_position?.latitude);
      const lon = parseFloat(data.iss_position?.longitude);
      const ts  = new Date(data.timestamp * 1000).toLocaleTimeString('es-ES');

      el.innerHTML = `
        <div class="visual-card">
          <p style="margin-bottom:.8rem;color:var(--muted);font-size:.9rem">
            📍 Lat: <strong>${lat.toFixed(4)}</strong> &nbsp;
            Lon: <strong>${lon.toFixed(4)}</strong> &nbsp;
            🕐 Actualizado: <strong>${ts}</strong>
          </p>
          <div id="mapa-iss" style="height:420px;border-radius:12px;z-index:0"></div>
        </div>`;

      if (mapInstance) { mapInstance.remove(); mapInstance = null; }

      setTimeout(() => {
        mapInstance = L.map('mapa-iss').setView([lat, lon], 3);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '© OpenStreetMap'
        }).addTo(mapInstance);

        const issIcon = L.divIcon({
          html: '<div style="font-size:2rem;line-height:1">🛸</div>',
          iconSize: [40, 40], iconAnchor: [20, 20], className: ''
        });
        L.marker([lat, lon], { icon: issIcon })
          .addTo(mapInstance)
          .bindPopup(`<strong>ISS</strong><br>Lat: ${lat.toFixed(4)}<br>Lon: ${lon.toFixed(4)}`)
          .openPopup();
      }, 100);
      break;
    }
    case 'meal': {
  titulo.textContent = ' Vista previa';
  const meal = data.meals?.[0];
  if (!meal) { el.innerHTML = '<p style="color:var(--muted)">No se encontró ninguna receta.</p>'; break; }

  // Extraer ingredientes y medidas
  const ingredientes = [];
  for (let i = 1; i <= 20; i++) {
    const ing = meal[`strIngredient${i}`];
    const med = meal[`strMeasure${i}`];
    if (ing && ing.trim()) ingredientes.push(`${med ? med.trim() + ' ' : ''}${ing.trim()}`);
  }

  el.innerHTML = `
    <div class="visual-card meal-card">
      <div class="meal-header">
        <img src="${meal.strMealThumb}" alt="${meal.strMeal}" class="meal-img">
        <div class="meal-info">
          <h3>${meal.strMeal}</h3>
          <div class="meal-meta">
            ${meal.strCategory ? `<span class="meal-badge">🍴 ${meal.strCategory}</span>` : ''}
            ${meal.strArea    ? `<span class="meal-badge">🌍 ${meal.strArea}</span>`     : ''}
          </div>
          <div class="meal-ingredientes">
            <strong>Ingredientes:</strong>
            <ul>
              ${ingredientes.map(i => `<li>${i}</li>`).join('')}
            </ul>
          </div>
          ${meal.strYoutube
            ? `<a href="${meal.strYoutube}" target="_blank" class="btn-doc" style="margin-top:1rem;display:inline-block">▶️ Ver receta en YouTube</a>`
            : ''}
        </div>
      </div>
      <div class="meal-instrucciones">
        <strong>Instrucciones:</strong>
        <p>${meal.strInstructions}</p>
      </div>
    </div>`;
  break;
}
case 'weather': {
  titulo.textContent = '🌤️ Clima actual';
  const w = data.current_weather || data.current;
  if (!w) { el.innerHTML = '<p style="color:var(--muted)">No se encontraron datos del clima.</p>'; break; }

  const codigos = {
    0: '☀️ Despejado', 1: '🌤️ Principalmente claro', 2: '⛅ Parcialmente nublado',
    3: '☁️ Nublado', 45: '🌫️ Niebla', 48: '🌫️ Niebla con escarcha',
    51: '🌦️ Llovizna ligera', 53: '🌦️ Llovizna', 55: '🌧️ Llovizna intensa',
    61: '🌧️ Lluvia ligera', 63: '🌧️ Lluvia', 65: '🌧️ Lluvia intensa',
    71: '🌨️ Nieve ligera', 73: '🌨️ Nieve', 75: '🌨️ Nieve intensa',
    80: '🌦️ Chubascos', 81: '🌧️ Chubascos fuertes', 82: '⛈️ Chubascos muy fuertes',
    95: '⛈️ Tormenta', 99: '⛈️ Tormenta con granizo',
  };

  const temp     = w.temperature ?? w.temperature_2m ?? '—';
  const viento   = w.windspeed   ?? w.wind_speed_10m  ?? '—';
  const codigo   = w.weathercode ?? w.weather_code     ?? 0;
  const desc     = codigos[codigo] || ' Desconocido';
  const esNoche  = w.is_day === 0;

  el.innerHTML = `
    <div class="visual-card weather-card">
      <div class="weather-main">
        <div class="weather-icon">${desc.split(' ')[0]}</div>
        <div class="weather-temp">${temp}°C</div>
        <div class="weather-desc">${desc.split(' ').slice(1).join(' ')}</div>
      </div>
      <div class="weather-detalles">
        <div class="weather-stat">
          <span>💨 Viento</span>
          <strong>${viento} km/h</strong>
        </div>
        <div class="weather-stat">
          <span>🕐 Momento</span>
          <strong>${esNoche ? 'Noche' : 'Día'}</strong>
        </div>
        <div class="weather-stat">
          <span>📍 Coordenadas</span>
          <strong>${data.latitude?.toFixed(2) ?? '—'}, ${data.longitude?.toFixed(2) ?? '—'}</strong>
        </div>
      </div>
    </div>`;
  break;
}

case 'country': {
  titulo.textContent = ' Vista previa';
  const paises = Array.isArray(data) ? data : [data];

  el.innerHTML = paises.slice(0, 3).map(p => {
    const poblacion = p.population?.toLocaleString('es-ES') || '—';
    const capital   = p.capital?.[0] || '—';
    const idiomas   = p.languages ? Object.values(p.languages).join(', ') : '—';
    const monedas   = p.currencies
      ? Object.values(p.currencies).map(c => `${c.name} (${c.symbol || ''})`).join(', ')
      : '—';
    const region    = p.region || '—';
    const subregion = p.subregion || '—';

    return `
      <div class="visual-card country-card">
        <div class="country-header">
          <img src="${p.flags?.svg || p.flags?.png}" alt="Bandera de ${p.name?.common}" class="country-flag">
          <div class="country-info">
            <h3>${p.name?.common} <small style="color:var(--muted);font-weight:400">${p.name?.official}</small></h3>
            <div class="country-meta">
              <span> Capital: <strong>${capital}</strong></span>
              <span> Población: <strong>${poblacion}</strong></span>
              <span> Región: <strong>${region} — ${subregion}</strong></span>
              <span> Idiomas: <strong>${idiomas}</strong></span>
              <span> Moneda: <strong>${monedas}</strong></span>
            </div>
          </div>
        </div>
      </div>`;
  }).join('');
  break;
}

    case 'crypto': {
      titulo.textContent = '📈 Vista previa';
      const colores = ['#2563eb', '#f59e0b', '#10b981', '#8b5cf6', '#ef4444'];
      const monedas = Object.keys(data);

      const tarjetas = monedas.map((m, i) => {
        const precios = data[m];
        const divisas = Object.entries(precios).map(([d, v]) =>
          `<div style="margin-top:.3rem;font-size:.85rem;color:var(--muted)">${d}: <strong style="color:var(--text)">${Number(v).toLocaleString('es-ES')}</strong></div>`
        ).join('');
        return `
          <div style="background:var(--bg);border-radius:10px;padding:.8rem 1.2rem;flex:1;min-width:120px;border:1px solid var(--border)">
            <div style="font-size:.78rem;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:.3rem">${m}</div>
            ${divisas}
          </div>`;
      }).join('');

      const primerasDivisas = Object.keys(data[monedas[0]]);
      const datasets = primerasDivisas.map((divisa, i) => ({
        label: divisa,
        data: monedas.map(m => data[m][divisa] || 0),
        backgroundColor: colores[i] || '#2563eb',
        borderRadius: 8,
        borderSkipped: false,
      }));

      el.innerHTML = `
        <div class="visual-card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.2rem">
            <h3 style="font-size:1.3rem">Comparativa de precios</h3>
            <span style="color:var(--muted);font-size:.85rem">Precio actual</span>
          </div>
          <div style="display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:1.5rem">
            ${tarjetas}
          </div>
          <canvas id="crypto-chart" height="120"></canvas>
        </div>`;

      new Chart(document.getElementById('crypto-chart'), {
        type: 'bar',
        data: { labels: monedas, datasets: datasets },
        options: {
          responsive: true,
          plugins: {
            legend: { display: true, position: 'top' },
            tooltip: {
              callbacks: {
                label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y.toLocaleString('es-ES')}`
              }
            }
          },
          scales: {
            y: {
              beginAtZero: false,
              grid: { color: 'rgba(0,0,0,.05)' },
              ticks: { callback: v => v.toLocaleString('es-ES') }
            },
            x: { grid: { display: false } }
          }
        }
      });
      break;
    }
  }
}

// ── Favorito ──────────────────────────────────────────────────
async function toggleFavorito() {
  const res = await fetch(`/api/users/favoritos/${apiId}/toggle/`, {
    method: 'POST', credentials: 'include',
    headers: { 'X-CSRFToken': getCookie('csrftoken') }
  });
  if (res.status === 403) { showAuthModal(); return; }
  const data = await res.json();
  const btn  = document.getElementById('btn-favorito');
  if (data.favorito) {
    btn.textContent       = '💔 Eliminar de favoritos';
    btn.style.background  = '#f59e0b';
    btn.style.borderColor = '#f59e0b';
    btn.style.color       = '#fff';
    showToast('Añadido a favoritos', 'success');
  } else {
    btn.textContent       = '⭐ Guardar en favoritos';
    btn.style.background  = '';
    btn.style.borderColor = '';
    btn.style.color       = '';
    showToast('Eliminado de favoritos', 'info');
  }
}

function copiarJSON() {
  const texto = document.getElementById('respuesta').textContent;
  navigator.clipboard.writeText(texto).then(() => {
    showToast('JSON copiado al portapapeles', 'success');
    const btn = document.getElementById('btn-copiar');
    btn.textContent = '¡Copiado!';
    btn.style.background = '#16a34a';
    setTimeout(() => {
      btn.textContent = 'Copiar';
      btn.style.background = '';
    }, 2000);
  });
}
// ── Valoraciones ──────────────────────────────────────────────
function renderEstrellas(mediaActual, totalActual, miVoto) {
  const media = document.getElementById('valoracion-media');
  const contenedor = document.getElementById('estrellas');

  media.innerHTML = mediaActual
    ? `<span class="media-numero">${mediaActual}★</span> <span class="media-total">(${totalActual} valoración${totalActual !== 1 ? 'es' : ''})</span>`
    : `<span class="media-total">Sin valoraciones aún</span>`;

  contenedor.innerHTML = [1,2,3,4,5].map(n => `
    <span class="estrella ${miVoto >= n ? 'activa' : ''}" data-valor="${n}">★</span>
  `).join('');

  contenedor.querySelectorAll('.estrella').forEach(star => {
    star.addEventListener('click', () => votarApi(parseInt(star.dataset.valor)));
    star.addEventListener('mouseover', () => {
      contenedor.querySelectorAll('.estrella').forEach(s => {
        s.classList.toggle('hover', parseInt(s.dataset.valor) <= parseInt(star.dataset.valor));
      });
    });
    star.addEventListener('mouseout', () => {
      contenedor.querySelectorAll('.estrella').forEach(s => s.classList.remove('hover'));
    });
  });
}

async function votarApi(puntuacion) {
  const msg = document.getElementById('valoracion-msg');
  const res = await fetch(`/api/users/valorar/${apiId}/`, {
    method: 'POST', credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
    body: JSON.stringify({ puntuacion })
  });
  if (res.status === 403) { showAuthModal(); return; }
  const data = await res.json();
  msg.textContent = '¡Gracias por tu valoración!';
  setTimeout(() => msg.textContent = '', 2000);
  const apiRes = await fetch(`/api/apis/${apiId}/`);
  const api = await apiRes.json();
  renderEstrellas(api.valoracion_media, api.total_valoraciones, puntuacion);
}
// ── Historial de peticiones ───────────────────────────────────
const HISTORIAL_KEY = 'apihub_historial';
const HISTORIAL_MAX = 20;

function guardarEnHistorial(apiNombre, url, params, respuesta) {
  const historial = obtenerHistorial();
  historial.unshift({
    apiNombre,
    url,
    params,
    respuesta: JSON.stringify(respuesta).slice(0, 500),
    fecha: new Date().toLocaleString('es-ES'),
  });
  localStorage.setItem(HISTORIAL_KEY, JSON.stringify(historial.slice(0, HISTORIAL_MAX)));
}

function obtenerHistorial() {
  try {
    return JSON.parse(localStorage.getItem(HISTORIAL_KEY)) || [];
  } catch {
    return [];
  }
}
// Carga y muestra APIs de la misma categoría excluyendo la actual
async function cargarRelacionadas(categoriaId, categoriaIcono, categoriaNombre) {
  const res  = await fetch(`/api/apis/?categoria=${categoriaId}`);
  const data = await res.json();
  const lista = (Array.isArray(data) ? data : (data.results || []))
    .filter(a => a.id !== parseInt(apiId))
    .slice(0, 3);

  if (!lista.length) return;

  const seccion = document.createElement('section');
  seccion.className = 'relacionadas-seccion';
  seccion.innerHTML = `
    <h2>APIs relacionadas <span class="badge badge-default" style="font-size:.8rem">${categoriaIcono} ${categoriaNombre}</span></h2>
    <div class="grid-apis relacionadas-grid">
      ${lista.map(api => {
        const authText = api.auth_tipo === 'none'   ? '🔓 Libre'
                       : api.auth_tipo === 'apikey'  ? '🔑 API Key' : '🔐 OAuth';
        const estrellas = api.valoracion_media ? `★ ${api.valoracion_media}` : '';
        return `
          <div class="card" onclick="location.href='/api/${api.id}/'">
            <h3>${api.nombre}</h3>
            <p>${api.descripcion.slice(0, 80)}…</p>
            <div class="card-footer">
              <span class="auth-tag">${authText}</span>
              ${estrellas ? `<span class="card-rating">${estrellas}</span>` : ''}
              <span class="card-arrow">→</span>
            </div>
          </div>`;
      }).join('')}
    </div>`;

  document.querySelector('main.container').appendChild(seccion);
}
cargarApi();