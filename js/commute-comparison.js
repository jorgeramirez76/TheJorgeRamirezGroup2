(() => {
  'use strict';

  const form = document.querySelector('[data-commute-form]');
  const resultBody = document.querySelector('[data-commute-results]');
  const resultPanel = document.querySelector('[data-results-panel]');
  if (!form || !resultBody || !resultPanel) return;

  const language = document.documentElement.lang === 'es' ? 'es' : 'en';
  const copy = {
    en: {
      option: 'Option',
      minutes: 'min',
      hours: 'hr',
      week: '/week',
      empty: 'Enter at least one time or cost for an option to compare it.'
    },
    es: {
      option: 'Opción',
      minutes: 'min',
      hours: 'h',
      week: '/semana',
      empty: 'Ingrese al menos un tiempo o costo para una opción antes de compararla.'
    }
  }[language];

  const numberValue = (field) => {
    const parsed = Number.parseFloat(field.value);
    return Number.isFinite(parsed) && parsed >= 0 ? parsed : 0;
  };

  const money = new Intl.NumberFormat(language === 'es' ? 'es-US' : 'en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2
  });

  const formatWeeklyTime = (minutes) => {
    if (minutes < 60) return `${Math.round(minutes)} ${copy.minutes}${copy.week}`;
    const hours = Math.round((minutes / 60) * 10) / 10;
    return `${hours} ${copy.hours}${copy.week}`;
  };

  const calculate = () => {
    const days = numberValue(form.elements.days_per_week);
    const rows = [];

    form.querySelectorAll('[data-commute-option]').forEach((option, index) => {
      const fields = option.querySelectorAll('input[type="number"]');
      const entered = Array.from(fields).some((field) => field.value !== '' && numberValue(field) > 0);
      if (!entered) return;

      const labelField = option.querySelector('[data-option-label]');
      const label = labelField.value.trim() || `${copy.option} ${index + 1}`;
      const oneWay = ['first_leg', 'wait_transfer', 'scheduled_ride', 'final_leg', 'buffer']
        .reduce((sum, name) => sum + numberValue(option.querySelector(`[data-field="${name}"]`)), 0);
      const dailyCost = numberValue(option.querySelector('[data-field="fare_tolls"]'))
        + numberValue(option.querySelector('[data-field="parking_local"]'));
      const weeklyMinutes = oneWay * 2 * days;
      const weeklyCost = dailyCost * days;

      rows.push({ label, oneWay, weeklyMinutes, weeklyCost });
    });

    resultBody.replaceChildren();
    rows.forEach((row) => {
      const tr = document.createElement('tr');
      [row.label, `${Math.round(row.oneWay)} ${copy.minutes}`, formatWeeklyTime(row.weeklyMinutes), `${money.format(row.weeklyCost)}${copy.week}`]
        .forEach((value) => {
          const cell = document.createElement('td');
          cell.textContent = value;
          tr.appendChild(cell);
        });
      resultBody.appendChild(tr);
    });

    const empty = resultPanel.querySelector('[data-empty-result]');
    empty.hidden = rows.length > 0;
    empty.textContent = copy.empty;
    resultPanel.hidden = false;
    if (rows.length > 0) resultPanel.focus();
  };

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    calculate();
  });

  form.addEventListener('reset', () => {
    window.setTimeout(() => {
      resultBody.replaceChildren();
      resultPanel.hidden = true;
    }, 0);
  });

  const printButton = document.querySelector('[data-print-results]');
  if (printButton) printButton.addEventListener('click', () => window.print());
})();
