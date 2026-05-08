// stats.js — página de estadísticas globales
async function cargarStats() {
  const res  = await fetch('/api/estadisticas/');
  const data = await res.json();

  // ── Resumen general ───────────────────────────────────────
  document.getElementById('stats-resumen').innerHTML = `
    <div class="resumen-grid">
      <div class="resumen-card">
        <strong>${data.total_apis}</strong>
        <span>APIs activas</span>
      </div>
      <div class="resumen-card">
        <strong>${data.total_categorias}</strong>
        <span>Categorías</span>
      </div>
      <div class="resumen-card">
        <strong>${data.total_usuarios}</strong>
        <span>Usuarios registrados</span>
      </div>
      <div class="resumen-card destacado" onclick="location.href='/api/${data.mas_valorada.id}/'">
        <strong>★ ${data.mas_valorada.media}</strong>
        <span>Mejor valorada</span>
        <p>${data.mas_valorada.nombre || '—'}</p>
      </div>
      <div class="resumen-card destacado" onclick="location.href='/api/${data.mas_visitada.id}/'">
        <strong>👁 ${data.mas_visitada.total_visitas}</strong>
        <span>Más visitada</span>
        <p>${data.mas_visitada.nombre || '—'}</p>
      </div>
      <div class="resumen-card destacado">
        <strong>${data.cat_mas_apis.icono} ${data.cat_mas_apis.nombre}</strong>
        <span>Categoría con más APIs</span>
        <p>${data.cat_mas_apis.total} APIs</p>
      </div>
    </div>`;

  // ── Top valoradas ─────────────────────────────────────────
  document.getElementById('top-valoradas').innerHTML = data.top_valoradas.map((a, i) => `
    <div class="stats-row" onclick="location.href='/api/${a.id}/'">
      <span class="stats-pos">${i + 1}</span>
      <span class="stats-nombre">${a.nombre}</span>
      <span class="stats-valor">★ ${a.media}</span>
    </div>
  `).join('');

  // ── Top visitadas ─────────────────────────────────────────
  document.getElementById('top-visitadas').innerHTML = data.top_visitadas.map((a, i) => `
    <div class="stats-row" onclick="location.href='/api/${a.id}/'">
      <span class="stats-pos">${i + 1}</span>
      <span class="stats-nombre">${a.nombre}</span>
      <span class="stats-valor">👁 ${a.visitas}</span>
    </div>
  `).join('');

  // ── Gráfica de categorías ─────────────────────────────────
  const colores = ['#2563eb', '#f59e0b', '#10b981', '#8b5cf6', '#ef4444', '#ec4899'];
  new Chart(document.getElementById('categorias-chart'), {
    type: 'doughnut',
    data: {
      labels: data.categorias.map(c => `${c.icono} ${c.nombre}`),
      datasets: [{
        data: data.categorias.map(c => c.total),
        backgroundColor: colores,
        borderWidth: 2,
        borderColor: 'var(--surface)',
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'right' },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.parsed} APIs`
          }
        }
      }
    }
  });
}

cargarStats();