import {$, text} from '../dom.js';

export function renderPrinter(printer, state, running) {
  $('demo-banner').hidden = !state.demo;
  const connected = Boolean(printer);
  text('connection', connected ? (state.demo ? 'Simulation' : 'Connected') : 'Disconnected');
  $('connection').classList.toggle('connected', connected);
  $('device-dot').classList.toggle('on', connected);
  text('model', connected ? (printer.display_name || (printer.model === 91 ? 'DI-RS1' : 'DNP DS-RX1')) : 'No printer');
  text('serial', connected ? 'Serial number · ' + (printer.serial || 'Unavailable') : 'Connect your printer via USB');
  text('device-status', running ? 'Changing firmware' : connected ? 'Device detected' : 'Waiting for connection');
  text('device-kind', state.demo ? 'DEMO' : 'USB');
  $('firmware').replaceChildren(document.createTextNode(printer?.firmware?.replace(/^(DS-RX1|DI-RS1) /, '') || '—'));
  const badge = document.createElement('span'); badge.textContent = printer?.edition === 'VG-02.21' ? 'VG · THREE MEDIA BRANDS' : 'CURRENT VERSION'; $('firmware').append(badge);
  text('detail-model', printer ? (printer.edition === 'VG-02.21' ? 'DNP VG-RX1HS · type 5' : printer.model === 91 ? 'DI-RS1 · type 91' : 'DS-RX1 · type ' + printer.model) : '—');
  text('detail-serial', printer?.serial || '—'); text('cwd', printer?.cwd || '—'); text('raw-status', printer?.status);
  text('counter', printer?.counter >= 0 ? printer.counter.toLocaleString('en-GB') : '—');
  text('media', printer?.media >= 0 ? Math.max(0, printer.media - 49).toLocaleString('en-GB') : '—');
}
