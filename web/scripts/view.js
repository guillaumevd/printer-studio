export const $ = (id) => document.getElementById(id);
export const versions = ['02.04', '02.07', '02.10', '02.21'];
const text = (id, value) => { $(id).textContent = value ?? '—'; };
export function routeFor(printer, target) {
  if (!printer) return [];
  const current = printer.firmware === 'DI-RS1 01.02' ? -1 : versions.indexOf(printer.firmware.replace('DS-RX1 ', ''));
  if (current < 0 && printer.firmware !== 'DI-RS1 01.02') return [];
  const destination = versions.indexOf(target);
  if (destination < 0 || destination === current) return [];
  return destination < current ? [target] : versions.slice(current + 1, destination + 1);
}
export function notice(message) { $('notice').hidden = !message; text('notice', message); }
export function render(state, target) {
  text('app-version', 'v' + (state.version || '1.4.0'));
  const printer = state.printers?.length === 1 ? state.printers[0] : null;
  const job = state.job;
  const running = job?.status === 'running';
  $('demo-banner').hidden = !state.demo;
  const connected = Boolean(printer);
  text('connection', connected ? (state.demo ? 'Simulation' : 'Connected') : 'Disconnected');
  $('connection').classList.toggle('connected', connected);
  $('device-dot').classList.toggle('on', connected);
  text('model', connected ? (printer.model === 91 ? 'DI-RS1' : 'DNP DS-RX1') : 'No printer');
  text('serial', connected ? 'Serial number · ' + (printer.serial || 'Unavailable') : 'Connect your printer via USB');
  text('device-status', running ? 'Changing firmware' : connected ? 'Device detected' : 'Waiting for connection');
  text('device-kind', state.demo ? 'DEMO' : 'USB');
  $('firmware').replaceChildren(document.createTextNode(printer?.firmware?.replace(/^(DS-RX1|DI-RS1) /, '') || '—'));
  const badge = document.createElement('span'); badge.textContent = 'CURRENT VERSION'; $('firmware').append(badge);
  text('detail-model', printer ? (printer.model === 91 ? 'DI-RS1 · type 91' : 'DS-RX1 · type ' + printer.model) : '—');
  text('detail-serial', printer?.serial || '—'); text('cwd', printer?.cwd || '—'); text('raw-status', printer?.status);
  text('counter', printer?.counter >= 0 ? printer.counter.toLocaleString('en-GB') : '—');
  text('media', printer?.media >= 0 ? printer.media.toLocaleString('en-GB') : '—');
  const steps = routeFor(printer, target);
  $('version-options').replaceChildren(...versions.map(version => {
    const button = document.createElement('button'); button.className = 'version-option' + (version === target ? ' active' : '');
    button.type = 'button'; button.dataset.version = version; button.setAttribute('aria-pressed', String(version === target));
    const item = state.catalog?.find(item => item.version === version);
    button.disabled = running || !item?.available;
    button.textContent = version;
    const small = document.createElement('small'); small.textContent = !item?.available ? 'UNAVAILABLE' : version === '02.21' ? 'LATEST LOCAL' : 'DNP · RX1';
    button.append(small); return button;
  }));
  $('route').replaceChildren();
  if (steps.length) {
    [printer.firmware.replace(/^(DS-RX1|DI-RS1) /, ''), ...steps].forEach((version, index) => {
      if (index) $('route').append(document.createTextNode('→'));
      const chip = document.createElement('span'); chip.className = 'route-chip'; chip.textContent = version; $('route').append(chip);
    });
  } else text('route', !printer ? 'Connect a printer to calculate the route.' : printer.firmware === 'DS-RX1 ' + target ? 'This version is already installed.' : 'No supported route to this version.');
  const downgrade = printer?.firmware?.startsWith('DS-RX1 ') && versions.indexOf(target) < versions.indexOf(printer.firmware.slice(7));
  text('update-title', downgrade ? 'Return to DNP ' + target : printer?.firmware === 'DS-RX1 ' + target ? 'This version is installed' : 'Install DNP ' + target);
  text('update-description', downgrade ? 'Direct downgrade using a verified local image. The 02.21 to 02.10 route has been tested on this printer; other downgrade routes remain unverified.' : 'Automatic source detection and verification after each restart.');
  $('update').disabled = !steps.length || !printer?.serial || running || state.interrupted || !steps.every(v => state.catalog?.find(x => x.version === v)?.available);
  $('scan').disabled = running;
  $('export').disabled = !job;
  text('job-status', job ? ({running: 'Operation in progress', success: 'Firmware change complete', error: 'Operation stopped · inspection required'}[job.status] + ' · ' + job.completed + ' / ' + job.steps.length + ' verified steps') : 'No operation in progress');
  $('steps-progress').replaceChildren(...(job?.steps || []).map((_, index) => {
    const step = document.createElement('span'); step.className = 'step' + (index < job.completed ? ' done' : index === job.completed && running ? ' running' : ''); return step;
  }));
  if (job?.events.length) {
    const atBottom = $('events').scrollTop + $('events').clientHeight >= $('events').scrollHeight - 30;
    $('events').replaceChildren(...job.events.map(event => {
      const row = document.createElement('div'); row.className = 'event'; const time = document.createElement('time');
      time.textContent = new Date(event.time).toLocaleTimeString('en-GB'); const message = document.createElement('span'); message.textContent = event.message; row.append(time, message); return row;
    }));
    if (atBottom) $('events').scrollTop = $('events').scrollHeight;
  }
  notice(state.error || (state.interrupted ? 'An interrupted operation requires inspection. Review the log and README.' : state.printers?.length > 1 ? 'Multiple printers detected. Connect only one printer to continue.' : ''));
}
