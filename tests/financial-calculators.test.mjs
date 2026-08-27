import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

class FakeElement {
  constructor({ value = '', min = '', max = '', required = false, checked = false } = {}) {
    this.value = value;
    this.min = min;
    this.max = max;
    this.required = required;
    this.checked = checked;
    this.step = '';
    this.placeholder = '';
    this.textContent = '';
    this.innerHTML = '';
    this.style = { display: 'none' };
    this.validationMessage = '';
    this.reported = false;
    this.focused = false;
  }

  get valueAsNumber() {
    return this.value === '' ? Number.NaN : Number(this.value);
  }

  setCustomValidity(message) {
    this.validationMessage = message;
  }

  setAttribute(name, value) {
    this[name] = String(value);
  }

  removeAttribute(name) {
    this[name] = '';
  }

  checkValidity() {
    if (this.validationMessage) return false;
    if (this.required && this.value.trim() === '') return false;
    if (this.value.trim() === '') return true;
    const value = Number(this.value);
    if (!Number.isFinite(value)) return false;
    if (this.min !== '' && value < Number(this.min)) return false;
    if (this.max !== '' && value > Number(this.max)) return false;
    return true;
  }

  reportValidity() {
    this.reported = true;
    return this.checkValidity();
  }

  focus() {
    this.focused = true;
  }

  scrollIntoView() {}
  addEventListener() {}
}

function calculatorScript(relative, functionName) {
  const source = fs.readFileSync(path.join(ROOT, relative), 'utf8');
  const blocks = [...source.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)]
    .map((match) => match[1]);
  const block = blocks.find((candidate) => candidate.includes(`function ${functionName}`));
  assert.ok(block, `${relative}: missing ${functionName}`);
  return block;
}

function contextFor(relative, functionName, elements) {
  const document = {
    getElementById(id) {
      assert.ok(elements[id], `${relative}: unexpected element lookup ${id}`);
      return elements[id];
    },
  };
  const context = vm.createContext({ document, console });
  vm.runInContext(calculatorScript(relative, functionName), context, { filename: relative });
  return context;
}

function netElements() {
  return {
    salePrice: new FakeElement({ value: '1000', min: '1', required: true }),
    payoff: new FakeElement({ min: '0' }),
    brokerCompensationMethod: new FakeElement({ value: 'percentage' }),
    brokerCompensation: new FakeElement({ min: '0', max: '100', required: true }),
    brokerCompensationLabel: new FakeElement(),
    brokerCompensationHelp: new FakeElement(),
    attorney: new FakeElement({ min: '0' }),
    propertyTaxAdjustment: new FakeElement({ min: '0' }),
    otherCosts: new FakeElement({ min: '0' }),
    concessions: new FakeElement({ min: '0' }),
    estimatedTaxPayment: new FakeElement({ min: '0' }),
    reducedRate: new FakeElement(),
    results: new FakeElement(),
    lineItems: new FakeElement(),
  };
}

for (const [relative, blankMessage] of [
  ['net-proceeds-calculator.html', 'Enter the broker compensation from your written agreement.'],
  ['es/net-proceeds-calculator.html', 'Ingresa la compensación del corredor de tu acuerdo escrito.'],
]) {
  test(`${relative}: RTF uses each $500 or fraction at statutory boundaries`, () => {
    const elements = netElements();
    const context = contextFor(relative, 'calcNet', elements);
    const assertFee = (price, expected, label) => {
      assert.ok(
        Math.abs(context.calcRTF(price) - expected) < 1e-9,
        `${label}: expected ${expected}, got ${context.calcRTF(price)}`,
      );
    };

    // Standard schedule: the total-consideration schedule changes above $350,000,
    // and each started $500 interval within a band incurs the full published rate.
    assertFee(350000, 2105, 'standard at $350,000');
    assertFee(350000.01, 2739.80, 'standard one cent above $350,000');
    assertFee(999500, 9569.20, 'standard at the last exact $500 interval below $1M');
    assertFee(999500.01, 9575, 'standard fractional interval below $1M');
    assertFee(1000000, 9575, 'standard at $1,000,000');
    assertFee(1000000.01, 9581.05, 'standard one cent above $1,000,000');

    elements.reducedRate.checked = true;
    assertFee(350000, 650, 'reduced at $350,000');
    assertFee(350000.01, 1282.15, 'reduced one cent above $350,000');
    assertFee(999500, 4671.85, 'reduced at the last exact $500 interval below $1M');
    assertFee(999500.01, 4675, 'reduced fractional interval below $1M');
    assertFee(1000000, 4675, 'reduced at $1,000,000');
    assertFee(1000000.01, 4678.40, 'reduced one cent above $1,000,000');
  });

  test(`${relative}: percentage and flat compensation boundaries`, () => {
    const elements = netElements();
    const context = contextFor(relative, 'calcNet', elements);

    context.calcNet();
    assert.equal(elements.results.style.display, 'none');
    assert.equal(elements.brokerCompensation.validationMessage, blankMessage);

    for (const allowed of ['0', '2.75', '100']) {
      elements.brokerCompensation.value = allowed;
      elements.brokerCompensation.setCustomValidity('');
      context.calcNet();
      assert.equal(elements.results.style.display, 'block', `${allowed}% should be valid`);
    }

    elements.brokerCompensation.value = '100.01';
    elements.brokerCompensation.setCustomValidity('');
    context.calcNet();
    assert.equal(elements.results.style.display, 'none');
    assert.equal(elements.brokerCompensation.reported, true);

    elements.brokerCompensationMethod.value = 'flat';
    context.updateBrokerCompensationField();
    assert.equal(elements.brokerCompensation.max, '');
    elements.brokerCompensation.value = '250000';
    context.calcNet();
    assert.equal(elements.results.style.display, 'block');

    elements.brokerCompensationMethod.value = 'percentage';
    context.updateBrokerCompensationField();
    assert.equal(elements.brokerCompensation.max, '100');
  });
}

function worksheetElements() {
  const elements = {
    closingCostsWorksheet: new FakeElement(),
    worksheetStatus: new FakeElement(),
    results: new FakeElement(),
    lineItems: new FakeElement(),
  };
  for (const id of [
    'loanCosts',
    'titleSettlement',
    'governmentFees',
    'prepaids',
    'initialEscrow',
    'attorneyFee',
    'inspectionAppraisal',
    'otherBuyerCosts',
    'credits',
  ]) {
    elements[id] = new FakeElement({ min: '0' });
  }
  return elements;
}

for (const [relative, emptyMessage] of [
  ['closing-costs-calculator.html', 'Enter at least one amount from your documents or quotes.'],
  ['es/closing-costs-calculator.html', 'Ingresa al menos un monto de tus documentos o cotizaciones.'],
]) {
  test(`${relative}: worksheet totals only user-entered amounts`, () => {
    const elements = worksheetElements();
    const context = contextFor(relative, 'calculateWorksheet', elements);
    const event = { prevented: false, preventDefault() { this.prevented = true; } };

    context.calculateWorksheet(event);
    assert.equal(event.prevented, true);
    assert.equal(elements.results.style.display, 'none');
    assert.equal(elements.worksheetStatus.textContent, emptyMessage);

    elements.loanCosts.value = '1250.50';
    elements.titleSettlement.value = '750';
    elements.credits.value = '200';
    context.calculateWorksheet(event);
    assert.equal(elements.results.style.display, 'block');
    assert.match(elements.lineItems.innerHTML, /1,800\.50|1\.800,50/);
  });
}
