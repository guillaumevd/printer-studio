import {request} from './api.js';
import {$, render, notice, routeFor} from './view.js';
let state = {}, target = '02.21', pending = false, lastScan = Date.now(), staged = null;
async function refresh() {
  try { state = await request('state'); render(state, target); }
  catch (error) { notice('Connection to the local server lost. ' + error.message); $('update').disabled = true; }
}
async function scan() {
  if (pending) return;
  pending = true; $('scan').disabled = true; $('scan').textContent = 'Detecting printers…';
  try { await request('scan', {}); await refresh(); }
  catch (error) { notice(error.message); }
  finally { pending = false; lastScan = Date.now(); $('scan').textContent = '⟳  Refresh detection'; $('scan').disabled = state.job?.status === 'running'; }
}
$('scan').addEventListener('click', scan);
$('version-options').addEventListener('click', event => {
  const button = event.target.closest('button[data-version]');
  if (!button || button.disabled) return;
  target = button.dataset.version; $('target').value = target; render(state, target);
});
$('update').addEventListener('click', () => {
  const printer = state.printers[0];
  staged = {serial: printer.serial, source: printer.firmware, target, confirmed: true};
  $('confirm-info').textContent = `${printer.serial}\n${printer.firmware} → ${routeFor(printer, target).join(' → ')}${printer.firmware.startsWith('DS-RX1 ') && target < printer.firmware.slice(7) ? (printer.firmware === 'DS-RX1 02.21' && target === '02.10' ? '\nThis downgrade route has been tested on this printer.' : '\nThis downgrade route has not yet been validated on hardware.') : ''}${state.demo ? '\nSimulation only.' : ''}`;
  $('ack').checked = false; $('confirm-start').disabled = true; $('confirm').showModal();
});
$('ack').addEventListener('change', () => { $('confirm-start').disabled = !$('ack').checked; });
$('confirm-start').addEventListener('click', async () => {
  $('confirm-start').disabled = true;
  try { await request('update', staged); $('confirm').close(); await refresh(); $('activity').scrollIntoView({behavior: 'smooth'}); }
  catch (error) { $('confirm').close(); notice(error.message); }
});
$('export').addEventListener('click', () => {
  const blob = new Blob([JSON.stringify(state.job, null, 2)], {type: 'application/json'});
  const url = URL.createObjectURL(blob), link = document.createElement('a');
  link.href = url; link.download = 'printer-studio-' + state.job.id + '.json'; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});
window.addEventListener('beforeunload', event => { if (state.job?.status === 'running') { event.preventDefault(); event.returnValue = ''; } });
await refresh();
setInterval(async () => { if (!pending) { await refresh(); if (state.job?.status !== 'running' && Date.now() - lastScan > 15000) await scan(); } }, 2000);
