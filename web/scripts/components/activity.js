import {$, text} from '../dom.js';

export function renderActivity(job, running) {
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
}
