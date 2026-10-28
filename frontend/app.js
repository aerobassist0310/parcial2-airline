const tid = name => document.querySelector(`[data-testid="${name}"]`);
const message = text => {document.querySelector('#message').textContent = text;};
async function api(path, body) {
  const options = body ? {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)} : {};
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
  return data;
}
let selected = null;
const search = document.querySelector('#search');
if (search) search.addEventListener('submit', async event => {
  event.preventDefault(); message('Buscando…');
  document.querySelector('#flights').replaceChildren();
  document.querySelector('#reserve').hidden = true;
  document.querySelector('#confirmation').hidden = true;
  try {
    const q = new URLSearchParams({origin:tid('search-origin').value.trim().toUpperCase(), destination:tid('search-destination').value.trim().toUpperCase(), date:tid('search-date').value});
    const flights = await api(`/flights/search?${q}`);
    for (const flight of flights) {
      const row = document.createElement('article'); row.dataset.testid = 'flight-row';
      const text = document.createElement('p'); text.textContent = `${flight.route} · ${flight.flight_date} · Cupos: ${flight.seats_available} · Precio (centavos): ${flight.price_cents}`;
      const button = document.createElement('button'); button.dataset.testid = 'reserve-button'; button.textContent = 'Reservar';
      button.onclick = () => {selected = flight.flight_id; document.querySelector('#reserve').hidden = false; tid('passenger-name').focus();};
      row.append(text, button); document.querySelector('#flights').append(row);
    }
    message(flights.length ? 'Selecciona un vuelo.' : 'No hay vuelos disponibles.');
  } catch(error) {message(error.message);}
});
const reserve = document.querySelector('#reserve');
if (reserve) reserve.addEventListener('submit', async event => {
  event.preventDefault(); const button = tid('confirm-submit'); button.disabled = true;
  try {
    const result = await api('/reservations', {flight_id:selected, passenger_name:tid('passenger-name').value, fare_class:'ECONOMY'});
    tid('confirmation-id').textContent = result.reservation_id;
    document.querySelector('#confirmation').hidden = false; reserve.hidden = true; message('Reserva creada.');
  } catch(error) {message(error.message);} finally {button.disabled = false;}
});
const analytics = document.querySelector('#analytics');
if (analytics) analytics.addEventListener('submit', async event => {
  event.preventDefault(); message('Consultando Athena…'); document.querySelector('#result').hidden = true;
  tid('occupancy-value').textContent = '';
  try {
    const q = new URLSearchParams({route:tid('manager-route').value.trim().toUpperCase(), month:tid('manager-month').value});
    const data = await api(`/analytics/occupancy?${q}`);
    tid('occupancy-value').textContent = `${(data.occupancy * 100).toFixed(3)}%`;
    document.querySelector('#counts').textContent = `${data.seats_sold} asientos vendidos de ${data.seats_capacity}.`;
    document.querySelector('#result').hidden = false; message('Consulta completada.');
  } catch(error) {message(error.message);}
});
