import {text, notice} from './dom.js';
import {renderPrinter} from './components/printer.js';
import {renderFirmware} from './components/firmware.js';
import {renderActivity} from './components/activity.js';
export {$, notice} from './dom.js';
export {versions, routeFor} from './components/firmware.js';

export function render(state, target) {
  text('app-version', 'v' + (state.version || '—'));
  const printer = state.printers?.length === 1 ? state.printers[0] : null;
  const job = state.job;
  const running = job?.status === 'running';
  renderPrinter(printer, state, running);
  renderFirmware(printer, target, state, running);
  renderActivity(job, running);
  notice(state.error || (state.interrupted ? 'An interrupted operation requires inspection. Review the log and README.' : state.printers?.length > 1 ? 'Multiple printers detected. Connect only one printer to continue.' : ''));
}
