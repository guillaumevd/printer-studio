import {$, text} from '../dom.js';

export const versions = ['02.04', '02.07', '02.10', '02.21'];
export function routeFor(printer, target) {
  if (!printer) return [];
  const current = printer.firmware === 'DI-RS1 01.02' ? -1 : versions.indexOf(printer.firmware.replace('DS-RX1 ', ''));
  if (current < 0 && printer.firmware !== 'DI-RS1 01.02') return [];
  const destination = versions.indexOf(target);
  if (destination < 0 || destination === current) return [];
  return destination < current ? [target] : versions.slice(current + 1, destination + 1);
}

export function renderFirmware(printer, target, state, running) {
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
}
