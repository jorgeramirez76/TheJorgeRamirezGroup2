(function (root) {
  'use strict';

  const FIVE_HUNDRED_DOLLARS = 50000;
  const ONE_MILLION_DOLLARS = 100000000;

  function toCents(value) {
    if (typeof value === 'number') {
      return Number.isFinite(value) && value >= 0 ? Math.round(value * 100) : null;
    }
    const normalized = String(value || '').replace(/[$,\s]/g, '');
    if (!normalized || !/^\d+(?:\.\d{0,2})?$/.test(normalized)) return null;
    const amount = Number(normalized);
    return Number.isFinite(amount) && amount >= 0 ? Math.round(amount * 100) : null;
  }

  function feeForSchedule(considerationCents, schedule) {
    let feeCents = 0;
    let lower = 0;
    for (const tier of schedule) {
      const upper = tier.upperCents == null ? considerationCents : Math.min(considerationCents, tier.upperCents);
      const segment = Math.max(0, upper - lower);
      if (segment > 0) feeCents += Math.ceil(segment / FIVE_HUNDRED_DOLLARS) * tier.rateCents;
      if (tier.upperCents == null || considerationCents <= tier.upperCents) break;
      lower = tier.upperCents;
    }
    return feeCents;
  }

  function standardFeeCents(considerationCents) {
    if (!Number.isInteger(considerationCents) || considerationCents < 0) throw new TypeError('considerationCents must be a non-negative integer');
    if (considerationCents < 10000) return 0;
    const lowerSchedule = [
      { upperCents: 15000000, rateCents: 200 },
      { upperCents: 20000000, rateCents: 335 },
      { upperCents: 35000000, rateCents: 390 }
    ];
    const higherSchedule = [
      { upperCents: 15000000, rateCents: 290 },
      { upperCents: 20000000, rateCents: 425 },
      { upperCents: 55000000, rateCents: 480 },
      { upperCents: 85000000, rateCents: 530 },
      { upperCents: 100000000, rateCents: 580 },
      { upperCents: null, rateCents: 605 }
    ];
    return feeForSchedule(considerationCents, considerationCents <= 35000000 ? lowerSchedule : higherSchedule);
  }

  function graduatedPercentFeeCents(considerationCents) {
    if (!Number.isInteger(considerationCents) || considerationCents < 0) throw new TypeError('considerationCents must be a non-negative integer');
    if (considerationCents <= ONE_MILLION_DOLLARS) return 0;
    let basisPoints;
    if (considerationCents <= 200000000) basisPoints = 100;
    else if (considerationCents <= 250000000) basisPoints = 200;
    else if (considerationCents <= 300000000) basisPoints = 250;
    else if (considerationCents <= 350000000) basisPoints = 300;
    else basisPoints = 350;
    return Math.round((considerationCents * basisPoints) / 10000);
  }

  function calculate(value) {
    const considerationCents = toCents(value);
    if (considerationCents == null) return null;
    const standardCents = standardFeeCents(considerationCents);
    const graduatedCents = graduatedPercentFeeCents(considerationCents);
    return {
      considerationCents,
      standardCents,
      graduatedCents,
      combinedCents: standardCents + graduatedCents,
      graduatedAppliesByAmount: considerationCents > ONE_MILLION_DOLLARS
    };
  }

  const api = { toCents, standardFeeCents, graduatedPercentFeeCents, calculate };
  root.JRG_RTF_CALCULATOR = api;

  if (typeof document === 'undefined') return;
  document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('rtfCalculator');
    if (!form) return;
    const input = document.getElementById('consideration');
    const standard = document.getElementById('standardFee');
    const graduated = document.getElementById('graduatedFee');
    const combined = document.getElementById('combinedFee');
    const note = document.getElementById('resultNote');
    const error = document.getElementById('calculationError');
    const lang = form.getAttribute('data-lang') === 'es' ? 'es' : 'en';
    const money = new Intl.NumberFormat(lang === 'es' ? 'es-US' : 'en-US', { style: 'currency', currency: 'USD' });

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      const result = calculate(input.value);
      if (!result) {
        error.textContent = lang === 'es' ? 'Ingrese una cantidad válida con hasta dos decimales.' : 'Enter a valid amount with no more than two decimal places.';
        standard.textContent = '—'; graduated.textContent = '—'; combined.textContent = '—';
        return;
      }
      error.textContent = '';
      standard.textContent = money.format(result.standardCents / 100);
      graduated.textContent = money.format(result.graduatedCents / 100);
      combined.textContent = money.format(result.combinedCents / 100);
      if (result.graduatedAppliesByAmount) {
        note.textContent = lang === 'es'
          ? 'La tarifa porcentual mostrada solo aplica si la propiedad está en una clase cubierta y no existe una exención. Confirme la escritura y los formularios vigentes.'
          : 'The graduated amount shown applies only when the property is in a covered class and no exemption applies. Confirm the deed and current forms.';
      } else {
        note.textContent = lang === 'es'
          ? 'La tarifa porcentual estatal comienza solo cuando la contraprestación supera $1,000,000; las exenciones y otras bases todavía requieren revisión.'
          : 'The state graduated fee begins only when consideration is over $1,000,000; exemptions and alternate bases still require review.';
      }
    });
  });
}(typeof globalThis !== 'undefined' ? globalThis : this));
