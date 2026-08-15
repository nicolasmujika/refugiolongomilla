function confirmarEliminarReserva(form, nombre) {
  const primero = confirm(`¿Estás seguro de eliminar la reserva de ${nombre}?\n\nEsta acción no se puede deshacer.`);
  if (!primero) return false;

  const segundo = confirm(`Última confirmación: se eliminará la reserva de ${nombre} de forma permanente. ¿Confirmas?`);
  return segundo;
}

function manejarCambioEstado(select) {
  const form = select.form;
  if (select.value === 'confirmada') {
    const link = form.dataset.waConfirmar;
    if (link) window.open(link, '_blank');
  }
  form.submit();
}