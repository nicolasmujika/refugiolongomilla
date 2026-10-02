document.addEventListener('DOMContentLoaded', () => {
  const nav = document.getElementById('siteNav');
  window.addEventListener('scroll', () => {
    nav.classList.toggle('solid', window.scrollY > 40);
  });

  const burger = document.getElementById('navBurger');
  const links = document.getElementById('navLinks');
  const backdrop = document.getElementById('navBackdrop');

  function cerrarMenu() {
    burger.classList.remove('open');
    links.classList.remove('open');
    backdrop.classList.remove('open');
    burger.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  }

  function toggleMenu() {
    const abierto = links.classList.toggle('open');
    burger.classList.toggle('open', abierto);
    backdrop.classList.toggle('open', abierto);
    burger.setAttribute('aria-expanded', abierto ? 'true' : 'false');
    document.body.style.overflow = abierto ? 'hidden' : '';
  }

  if (burger && links && backdrop) {
    burger.addEventListener('click', toggleMenu);
    backdrop.addEventListener('click', cerrarMenu);
    links.querySelectorAll('a').forEach(a => a.addEventListener('click', cerrarMenu));
  }
});

const CAL_TEXTOS = {
  es: {
    meses: ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'],
    dias: ['L','M','X','J','V','S','D'],
    disponible: 'Disponible',
    ocupado: 'Ocupado',
  },
  en: {
    meses: ['January','February','March','April','May','June','July','August','September','October','November','December'],
    dias: ['M','T','W','T','F','S','S'],
    disponible: 'Available',
    ocupado: 'Booked',
  },
};

async function cargarCalendarioDisponibilidad() {
  const contenedor = document.getElementById('calendario-disponibilidad');
  if (!contenedor) return;

  const idioma = document.body.dataset.idioma === 'en' ? 'en' : 'es';
  const textos = CAL_TEXTOS[idioma];

  let ocupadoSet = new Set();
  try {
    const res = await fetch('/fechas-ocupadas/');
    const data = await res.json();
    data.ocupado.forEach(rango => {
      let actual = new Date(rango.inicio + 'T00:00:00');
      const fin = new Date(rango.fin + 'T00:00:00');
      while (actual < fin) {
        ocupadoSet.add(actual.toISOString().slice(0, 10));
        actual.setDate(actual.getDate() + 1);
      }
    });
  } catch (e) {
    console.error('No se pudo cargar disponibilidad', e);
  }

  const hoy = new Date();

  function renderMes(anio, mes) {
    const primerDia = new Date(anio, mes, 1);
    const diasEnMes = new Date(anio, mes + 1, 0).getDate();
    const offset = (primerDia.getDay() + 6) % 7;

    let html = `<div class="cal-month"><h4>${textos.meses[mes]} ${anio}</h4><div class="cal-grid">`;
    textos.dias.forEach(d => { html += `<div class="cal-day blank" style="opacity:.4;">${d}</div>`; });
    for (let i = 0; i < offset; i++) { html += `<div class="cal-day blank"></div>`; }

    for (let dia = 1; dia <= diasEnMes; dia++) {
      const fecha = new Date(anio, mes, dia);
      const iso = fecha.toISOString().slice(0, 10);
      const esOcupado = ocupadoSet.has(iso);
      const esHoy = iso === hoy.toISOString().slice(0, 10);
      const clases = ['cal-day', esOcupado ? 'ocupado' : 'disponible', esHoy ? 'hoy' : ''].join(' ');
      const dataAtributo = esOcupado ? '' : `data-fecha="${iso}"`;
      const etiqueta = esOcupado ? textos.ocupado : textos.disponible;
      html += `<div class="${clases}" title="${etiqueta}">${dia}</div>`;
    }
    html += `</div></div>`;
    return html;
  }

  let html = '<div class="cal-months">';
  html += renderMes(hoy.getFullYear(), hoy.getMonth());
  const siguiente = new Date(hoy.getFullYear(), hoy.getMonth() + 1, 1);
  html += renderMes(siguiente.getFullYear(), siguiente.getMonth());
  html += '</div>';
  html += `<div class="cal-legend"><span><span class="cal-dot libre"></span>${textos.disponible}</span><span><span class="cal-dot ocupado"></span>${textos.ocupado}</span></div>`;

  contenedor.innerHTML = html;
  activarClicsCalendario();
}

document.addEventListener('DOMContentLoaded', cargarCalendarioDisponibilidad);

function iniciarCarruselPromo() {
  const slides = document.querySelectorAll('.promo-slide');
  if (slides.length < 2) return;

  let index = 0;
  setInterval(() => {
    slides[index].classList.remove('active');
    index = (index + 1) % slides.length;
    slides[index].classList.add('active');
  }, 5000);
}

document.addEventListener('DOMContentLoaded', iniciarCarruselPromo);

const ISO_PAIS = {
  "+56": "cl", "+54": "ar", "+51": "pe", "+591": "bo", "+57": "co",
  "+52": "mx", "+1": "us", "+34": "es", "+55": "br", "+49": "de",
  "+33": "fr", "+44": "gb",
};

function iniciarSelectorBandera() {
  const select = document.getElementById("id_codigo_pais");
  const bandera = document.getElementById("bandera-pais");
  if (!select || !bandera) return;

  function actualizarBandera() {
    const iso = ISO_PAIS[select.value] || "cl";
    bandera.src = `https://flagcdn.com/24x18/${iso}.png`;
  }

  select.addEventListener("change", actualizarBandera);
  actualizarBandera();
}

document.addEventListener("DOMContentLoaded", iniciarSelectorBandera);


function activarClicsCalendario() {
  const contenedor = document.getElementById('calendario-disponibilidad');
  if (!contenedor) return;

  let seleccionando = 'llegada'; // alterna entre 'llegada' y 'salida'

  contenedor.addEventListener('click', (e) => {
    const dia = e.target.closest('[data-fecha]');
    if (!dia) return;

    const fecha = dia.dataset.fecha;
    const inputLlegada = document.getElementById('id_fecha_llegada');
    const inputSalida = document.getElementById('id_fecha_salida');
    if (!inputLlegada || !inputSalida) return;

    if (seleccionando === 'llegada') {
      inputLlegada.value = fecha;
      inputSalida.value = '';
      seleccionando = 'salida';
    } else {
      if (fecha <= inputLlegada.value) {
        // si eligen una "salida" antes que la llegada, reiniciamos como nueva llegada
        inputLlegada.value = fecha;
        inputSalida.value = '';
        seleccionando = 'salida';
        return;
      }
      inputSalida.value = fecha;
      seleccionando = 'llegada';
      document.getElementById('reserva-form-anchor')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  });
}

// ---------- Total estimado de la reserva (casa x noches + servicios extra) ----------
document.addEventListener("DOMContentLoaded", function () {
  const casasPrecios = JSON.parse(document.getElementById("casas-precios-data").textContent);

  const selectCasa = document.getElementById("id_casa");
  const inputLlegada = document.getElementById("id_fecha_llegada");
  const inputSalida = document.getElementById("id_fecha_salida");
  const checksServicios = document.querySelectorAll(".servicio-check");
  const totalBox = document.getElementById("total-estimado");
  const totalMonto = document.getElementById("total-monto");

  if (!selectCasa || !inputLlegada || !inputSalida || !totalBox) return;

  function formatoCLP(numero) {
    return "$" + numero.toLocaleString("es-CL");
  }

  function getNoches() {
    const llegada = inputLlegada.value;
    const salida = inputSalida.value;
    if (!llegada || !salida) return 0;
    const diff = (new Date(salida) - new Date(llegada)) / (1000 * 60 * 60 * 24);
    return diff > 0 ? diff : 0;
  }

  function calcularTotal() {
    const casaId = selectCasa.value;
    const noches = getNoches();
    const precioNoche = casasPrecios[casaId] || 0;
    let total = noches * precioNoche;

    checksServicios.forEach(chk => {
      const id = chk.dataset.id;
      const porNoche = chk.dataset.porNoche === "1";
      const precio = parseInt(chk.dataset.precio, 10) || 0;
      const wrap = document.getElementById("dias-wrap-" + id);
      const inputDias = document.getElementById("dias_" + id);

      if (porNoche && wrap && inputDias) {
        if (chk.checked && noches > 0) {
          wrap.style.display = "flex";
          inputDias.max = noches;
          if (parseInt(inputDias.value, 10) > noches || !inputDias.dataset.tocado) {
            inputDias.value = noches;
          }
        } else {
          wrap.style.display = "none";
        }
      }

      if (chk.checked) {
        if (porNoche) {
          const dias = Math.min(parseInt(inputDias?.value, 10) || 1, noches || 1);
          total += precio * dias;
        } else {
          total += precio;
        }
      }
    });

    if (total > 0) {
      totalBox.style.display = "flex";
      totalMonto.textContent = formatoCLP(total);
    } else {
      totalBox.style.display = "none";
    }
  }

  selectCasa.addEventListener("change", calcularTotal);
  inputLlegada.addEventListener("change", calcularTotal);
  inputSalida.addEventListener("change", calcularTotal);
  checksServicios.forEach(chk => chk.addEventListener("change", calcularTotal));

  document.querySelectorAll(".dias-servicio-input").forEach(inp => {
    inp.addEventListener("input", () => {
      inp.dataset.tocado = "1";
      calcularTotal();
    });
  });

  calcularTotal();
});


// ---------- Galería de fotos de cada casa (lightbox) ----------
function iniciarLightbox() {
  const galerias = document.querySelectorAll('[data-gallery]');
  if (!galerias.length) return;

  const lb = document.createElement('div');
  lb.className = 'lb';
  lb.setAttribute('role', 'dialog');
  lb.setAttribute('aria-modal', 'true');
  lb.innerHTML = `
    <div class="lb-top"><span class="lb-count"></span><button class="lb-close" aria-label="Cerrar">&times;</button></div>
    <div class="lb-stage">
      <button class="lb-nav lb-prev" aria-label="Anterior">&#8249;</button>
      <img class="lb-img" alt="">
      <button class="lb-nav lb-next" aria-label="Siguiente">&#8250;</button>
    </div>
    <div class="lb-cap"></div>
    <div class="lb-thumbs"></div>`;
  document.body.appendChild(lb);

  const img = lb.querySelector('.lb-img');
  const cap = lb.querySelector('.lb-cap');
  const count = lb.querySelector('.lb-count');
  const thumbs = lb.querySelector('.lb-thumbs');

  let fotos = [];
  let actual = 0;
  let lastFocus = null;

  function mostrar(i) {
    actual = (i + fotos.length) % fotos.length;
    img.src = fotos[actual].src;
    img.alt = fotos[actual].desc;
    cap.textContent = fotos[actual].desc;
    count.textContent = `${actual + 1} / ${fotos.length}`;
    thumbs.querySelectorAll('img').forEach((t, n) => t.classList.toggle('active', n === actual));
    thumbs.children[actual]?.scrollIntoView({ block: 'nearest', inline: 'center' });
  }

  function abrir(galeria, indice) {
    fotos = [...galeria.querySelectorAll('[data-full]')].map(el => ({
      src: el.dataset.full, desc: el.dataset.desc || galeria.dataset.casa || '',
    }));
    if (!fotos.length) return;
    thumbs.innerHTML = fotos.map((f, n) => `<img src="${f.src}" alt="" data-i="${n}" loading="lazy">`).join('');
    lastFocus = document.activeElement;
    lb.classList.add('open');
    document.body.style.overflow = 'hidden';
    mostrar(indice);
    lb.querySelector('.lb-close').focus();
  }

  function cerrar() {
    lb.classList.remove('open');
    document.body.style.overflow = '';
    img.src = '';
    lastFocus?.focus();
  }

  galerias.forEach(g => {
    const abrirDesde = (el) => {
      const todas = [...g.querySelectorAll('[data-full]')];
      abrir(g, Math.max(0, todas.indexOf(el)));
    };
    g.addEventListener('click', e => {
      const el = e.target.closest('.ph-photo[data-full]');
      if (el) abrirDesde(el);
    });
    g.addEventListener('keydown', e => {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      const el = e.target.closest('.ph-photo[data-full]');
      if (el) { e.preventDefault(); abrirDesde(el); }
    });
  });

  lb.querySelector('.lb-close').addEventListener('click', cerrar);
  lb.querySelector('.lb-prev').addEventListener('click', () => mostrar(actual - 1));
  lb.querySelector('.lb-next').addEventListener('click', () => mostrar(actual + 1));
  thumbs.addEventListener('click', e => {
    const t = e.target.closest('img[data-i]');
    if (t) mostrar(parseInt(t.dataset.i, 10));
  });
  lb.addEventListener('click', e => {
    if (e.target === lb || e.target.classList.contains('lb-stage')) cerrar();
  });
  document.addEventListener('keydown', e => {
    if (!lb.classList.contains('open')) return;
    if (e.key === 'Escape') cerrar();
    if (e.key === 'ArrowLeft') mostrar(actual - 1);
    if (e.key === 'ArrowRight') mostrar(actual + 1);
  });

  // deslizar con el dedo en el celular
  let x0 = null;
  lb.addEventListener('touchstart', e => { x0 = e.touches[0].clientX; }, { passive: true });
  lb.addEventListener('touchend', e => {
    if (x0 === null) return;
    const dx = e.changedTouches[0].clientX - x0;
    if (Math.abs(dx) > 50) mostrar(actual + (dx < 0 ? 1 : -1));
    x0 = null;
  });
}

document.addEventListener('DOMContentLoaded', iniciarLightbox);