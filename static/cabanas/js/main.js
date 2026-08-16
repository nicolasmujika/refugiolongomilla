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