// index.js — catálogo principal
const API_URL = '/api';
let urlActual = `${API_URL}/apis/`;

// Función para asignar una clase de color a la etiqueta de categoría basada en un hash del nombre de la categoría, asegurando que cada categoría tenga un color consistente y distintivo.
function badgeClass(nombre) {
  const colores = [
    'badge-entretenimiento',
    'badge-meteorologia',
    'badge-geografia',
    'badge-ciencia',
    'badge-gastronomia',
    'badge-criptomonedas',
    'badge-default',
  ];
  let hash = 0;
  for (let i = 0; i < (nombre || '').length; i++) {
    hash = nombre.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colores[Math.abs(hash) % colores.length];
}

// Función para cargar las categorías desde la API y poblar el filtro de categorías en el formulario de búsqueda, además de actualizar el contador de categorías disponibles.
async function cargarCategorias() {
  const res  = await fetch(`${API_URL}/categorias/`);
  const cats = await res.json();
  const lista = Array.isArray(cats) ? cats : (cats.results || []);
  const sel  = document.getElementById('filtro-categoria');
  document.getElementById('stat-cats').textContent = lista.length;
  lista.forEach(c => {
    sel.innerHTML += `<option value="${c.id}">${c.icono} ${c.nombre}</option>`;
  });
}

// Función para cargar las APIs desde la API REST, aplicando los filtros de búsqueda, categoría, tipo de autenticación, orden y estado de implementación.
async function cargarApis(search = '', categoria = '', auth = '', orden = '', implementada = '', url = null) {
  mostrarSkeleton();
  if (!url) {
    const params = new URLSearchParams();
    if (search)       params.set('search', search);
    if (categoria)    params.set('categoria', categoria);
    if (auth)         params.set('auth', auth);
    if (orden)        params.set('orden', orden);
    if (implementada) params.set('implementada', implementada);
    url = `${API_URL}/apis/?${params}`;
  }
  urlActual = url;

  const res  = await fetch(url);
  const data = await res.json();
  const lista = Array.isArray(data) ? data : (data.results || []);
  const total = data.count !== undefined ? data.count : lista.length;

  document.getElementById('stat-apis').textContent = total;
  document.getElementById('contador').textContent =
    total === 1 ? '1 API encontrada' : `${total} APIs encontradas`;

  renderApis(lista);
  renderPaginacion(data.previous, data.next);
}

// Función para renderizar los botones de paginación "Anterior" y "Siguiente" en función de la existencia de páginas anteriores o siguientes, 
// y asignarles los eventos de clic correspondientes para cargar las APIs de la página seleccionada.
function renderPaginacion(previous, next) {
  const contenedor = document.getElementById('paginacion');
  if (!contenedor) return;

  if (!previous && !next) {
    contenedor.innerHTML = '';
    return;
  }

  contenedor.innerHTML = `
    <button class="btn-pagina" ${!previous ? 'disabled' : ''} id="btn-anterior">← Anterior</button>
    <button class="btn-pagina" ${!next ? 'disabled' : ''} id="btn-siguiente">Siguiente →</button>
  `;

  if (previous) {
    document.getElementById('btn-anterior').addEventListener('click', () => {
      cargarApis('', '', '', '', '', previous);
    });
  }
  if (next) {
    document.getElementById('btn-siguiente').addEventListener('click', () => {
      cargarApis('', '', '', '', '', next);
    });
  }
}

// Vista activa guardada en localStorage
let vistaActual = localStorage.getItem('apihub_vista') || 'grid';

// Función para cambiar entre vista de cuadrícula y lista, actualizando la clase del contenedor de APIs y 
// el estado activo de los botones de vista, además de guardar la preferencia en localStorage para mantenerla en futuras visitas.
function cambiarVista(vista) {
  vistaActual = vista;
  localStorage.setItem('apihub_vista', vista);
  const grid = document.getElementById('lista-apis');
  const btnGrid = document.getElementById('btn-grid');
  const btnList = document.getElementById('btn-list');
  grid.className = vista === 'list' ? 'lista-apis-list' : 'grid-apis';
  btnGrid.classList.toggle('activo', vista === 'grid');
  btnList.classList.toggle('activo', vista === 'list');
}
// Función para renderizar la lista de APIs en el contenedor principal, creando una tarjeta para cada API con su información relevante
function renderApis(apis) {
  const container = document.getElementById('lista-apis');
  if (!apis.length) {
    container.innerHTML = '<p style="color:var(--muted);padding:2rem 0">No se encontraron APIs.</p>';
    return;
  }
  container.className = vistaActual === 'list' ? 'lista-apis-list' : 'grid-apis';
  container.innerHTML = apis.map((api, i) => {
    const authClass = api.auth_tipo === 'apikey' ? 'apikey' : api.auth_tipo === 'oauth' ? 'oauth' : '';
    const authText  = api.auth_tipo === 'none'   ? '🔓 Libre'
                    : api.auth_tipo === 'apikey'  ? '🔑 API Key' : '🔐 OAuth';
    const estrellas = api.valoracion_media
      ? `<span class="card-rating">★ ${api.valoracion_media}</span>`
      : '';
    const visitas = api.total_visitas
      ? `<span class="card-visitas">👁 ${api.total_visitas}</span>`
      : '';
    const implementada = api.implementada
      ? `<span class="badge-implementada">✓ Implementada</span>`
      : `<span class="badge-desarrollo">⚙ En desarrollo</span>`; 
    return `
      <div class="card ${vistaActual === 'list' ? 'card-list' : ''}" style="animation-delay:${i * 0.04}s" onclick="location.href='/api/${api.id}/'">
        <span class="badge ${badgeClass(api.categoria_nombre)}">${api.categoria_icono || ''} ${api.categoria_nombre || 'General'}</span>
        ${implementada}
        <h3>${api.nombre}</h3>
        <p>${api.descripcion.slice(0, 95)}${api.descripcion.length > 95 ? '…' : ''}</p>
        <div class="card-footer">
          <span class="auth-tag ${authClass}">${authText}</span>
          ${estrellas}
          ${visitas}
          <span class="card-arrow">→</span>
        </div>
      </div>`;
  }).join('');

  // Aplicar vista guardada al cargar
  const btnGrid = document.getElementById('btn-grid');
  const btnList = document.getElementById('btn-list');
  if (btnGrid && btnList) {
    btnGrid.classList.toggle('activo', vistaActual === 'grid');
    btnList.classList.toggle('activo', vistaActual === 'list');
  }
}
// Función para mostrar un esqueleto de carga mientras se obtienen los datos de las APIs, creando varias tarjetas 
// de esqueleto con animación para mejorar la experiencia del usuario durante la espera.
function mostrarSkeleton() {
  const container = document.getElementById('lista-apis');
  container.innerHTML = Array(6).fill(`
    <div class="skeleton-card">
      <div class="skeleton skeleton-badge"></div>
      <div class="skeleton skeleton-title"></div>
      <div class="skeleton skeleton-text"></div>
      <div class="skeleton skeleton-text-short"></div>
      <div class="skeleton skeleton-footer"></div>
    </div>
  `).join('');
}
// Evento para cargar las categorías y las APIs al cargar la página, y para aplicar los filtros de búsqueda con un debounce para evitar demasiadas solicitudes a la API mientras el usuario escribe.
document.addEventListener('DOMContentLoaded', () => {
  const buscador  = document.getElementById('buscador');
  const filtCat   = document.getElementById('filtro-categoria');
  const filtAuth  = document.getElementById('filtro-auth');
  const filtOrden = document.getElementById('filtro-orden');
  const filtImpl  = document.getElementById('filtro-implementada');
  cambiarVista(vistaActual);

  // Función para aplicar los filtros seleccionados y cargar las APIs correspondientes
  function aplicarFiltros() {
    cargarApis(buscador.value, filtCat.value, filtAuth.value, filtOrden.value, filtImpl.checked ? 'true' : '');
  }

  let debounceTimer;
  buscador.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(aplicarFiltros, 400);
  });

  filtCat.addEventListener('change', aplicarFiltros);
  filtAuth.addEventListener('change', aplicarFiltros);
  filtOrden.addEventListener('change', aplicarFiltros);
  filtImpl.addEventListener('change', aplicarFiltros);

  cargarCategorias();
  cargarApis();
});