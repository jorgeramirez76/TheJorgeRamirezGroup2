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
    salePrice: new FakeElement({ value: '1000', min: '0.01', required: true }),
    payoff: new FakeElement({ min: '0' }),
    brokerCompensationMethod: new FakeElement({ value: 'percentage' }),
    brokerCompensation: new FakeElement({ min: '0', max: '100', required: true }),
    brokerCompensationLabel: new FakeElement(),
    brokerCompensationHelp: new FakeElement(),
    attorney: new FakeElement({ min: '0' }),
    propertyTaxAdjustmentDirection: new FakeElement(),
    propertyTaxAdjustment: new FakeElement({ min: '0' }),
    otherCosts: new FakeElement({ min: '0' }),
    concessions: new FakeElement({ min: '0' }),
    estimatedTaxPayment: new FakeElement({ min: '0' }),
    reducedRate: new FakeElement(),
    graduatedPercentFeeApplicability: new FakeElement({ value: 'unknown' }),
    results: new FakeElement(),
    lineItems: new FakeElement(),
  };
}

for (const [relative, blankMessage, taxDirectionMessage] of [
  [
    'net-proceeds-calculator.html',
    'Enter the broker compensation from your written agreement.',
    'Select whether the property-tax adjustment is due from or due to the seller.',
  ],
  [
    'es/net-proceeds-calculator.html',
    'Ingresa la compensación del corredor de tu acuerdo escrito.',
    'Selecciona si el ajuste de impuesto a la propiedad está a cargo o a favor del vendedor.',
  ],
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
    // and each started $500 interval within every band incurs the full published rate.
    for (const [price, expected, label] of [
      [0, 0, 'at $0'],
      [99.99, 0, 'below the $100 exemption boundary'],
      [100, 2, 'at $100'],
      [500, 2, 'at the first exact $500 interval'],
      [500.01, 4, 'one cent into the second $500 interval'],
      [150000, 600, 'at the first rate boundary'],
      [150000.01, 603.35, 'one cent into the $3.35 band'],
      [150500, 603.35, 'at an exact interval in the $3.35 band'],
      [150500.01, 606.70, 'fractional interval in the $3.35 band'],
      [200000, 935, 'at the second rate boundary'],
      [200000.01, 938.90, 'one cent into the $3.90 band'],
      [350000, 2105, 'at the total-schedule boundary'],
      [350000.01, 2739.80, 'one cent into the over-$350K schedule'],
      [350500, 2739.80, 'at an exact interval in the $4.80 band'],
      [350500.01, 2744.60, 'fractional interval in the $4.80 band'],
      [550000, 4655, 'at the $550K rate boundary'],
      [550000.01, 4660.30, 'one cent into the $5.30 band'],
      [550500.01, 4665.60, 'fractional interval in the $5.30 band'],
      [850000, 7835, 'at the $850K rate boundary'],
      [850000.01, 7840.80, 'one cent into the $5.80 band'],
      [850500.01, 7846.60, 'fractional interval in the $5.80 band'],
      [999500, 9569.20, 'at the last exact interval below $1M'],
      [999500.01, 9575, 'fractional interval below $1M'],
      [1000000, 9575, 'at $1M'],
      [1000000.01, 9581.05, 'one cent into the $6.05 band'],
      [1000500.01, 9587.10, 'fractional interval in the $6.05 band'],
    ]) assertFee(price, expected, `standard ${label}`);

    elements.reducedRate.checked = true;
    for (const [price, expected, label] of [
      [0, 0, 'at $0'],
      [99.99, 0, 'below the $100 exemption boundary'],
      [100, 0.50, 'at $100'],
      [500, 0.50, 'at the first exact $500 interval'],
      [500.01, 1, 'one cent into the second $500 interval'],
      [150000, 150, 'at the first reduced-rate boundary'],
      [150000.01, 151.25, 'one cent into the $1.25 band'],
      [150500.01, 152.50, 'fractional interval in the $1.25 band'],
      [350000, 650, 'at the total-schedule boundary'],
      [350000.01, 1282.15, 'one cent into the over-$350K schedule'],
      [350500.01, 1284.30, 'fractional interval in the $2.15 band'],
      [550000, 2140, 'at the $550K rate boundary'],
      [550000.01, 2142.65, 'one cent into the $2.65 band'],
      [550500.01, 2145.30, 'fractional interval in the $2.65 band'],
      [850000, 3730, 'at the $850K rate boundary'],
      [850000.01, 3733.15, 'one cent into the $3.15 band'],
      [850500.01, 3736.30, 'fractional interval in the $3.15 band'],
      [999500, 4671.85, 'at the last exact interval below $1M'],
      [999500.01, 4675, 'fractional interval below $1M'],
      [1000000, 4675, 'at $1M'],
      [1000000.01, 4678.40, 'one cent into the $3.40 band'],
      [1000500.01, 4681.80, 'fractional interval in the $3.40 band'],
    ]) assertFee(price, expected, `reduced ${label}`);

    assertFee(Number.NaN, 0, 'reduced nonnumeric input fails closed');
    assertFee(Number.POSITIVE_INFINITY, 0, 'reduced infinite input fails closed');
    assertFee(-1, 0, 'reduced negative input fails closed');
  });

  test(`${relative}: Graduated Percent Fee protects every full-price rate cliff`, () => {
    const elements = netElements();
    const context = contextFor(relative, 'calcNet', elements);
    const calculate = relative.startsWith('es/')
      ? context.calcGPF
      : context.calcGraduatedPercentFee;
    const cases = [
      [1000000, 0],
      [1000000.01, 10000],
      [1000000.50, 10000.01],
      [2000000, 20000],
      [2000000.01, 40000],
      [2000000.25, 40000.01],
      [2500000, 50000],
      [2500000.01, 62500],
      [3000000, 75000],
      [3000000.01, 90000],
      [3500000, 105000],
      [3500000.01, 122500],
    ];
    for (const [price, expected] of cases) {
      assert.ok(
        Math.abs(calculate(price) - expected) < 1e-6,
        `${price}: expected ${expected}, got ${calculate(price)}`,
      );
    }
    elements.reducedRate.checked = true;
    assert.equal(calculate(1000000.01), 10000);
    assert.equal(calculate(-1), 0);
    assert.equal(calculate(Number.NaN), 0);
    assert.equal(calculate(Number.POSITIVE_INFINITY), 0);
  });

  test(`${relative}: property-tax settlement adjustment supports seller debit and credit`, () => {
    const elements = netElements();
    const context = contextFor(relative, 'calcNet', elements);
    const isSpanish = relative.startsWith('es/');
    elements.salePrice.value = '100000';
    elements.brokerCompensation.value = '0';

    context.calcNet();
    assert.equal(elements.results.style.display, 'block', 'blank adjustment needs no direction');

    elements.propertyTaxAdjustment.value = '1000';
    elements.propertyTaxAdjustmentDirection.value = '';
    context.calcNet();
    assert.equal(elements.results.style.display, 'none');
    assert.equal(elements.propertyTaxAdjustmentDirection.validationMessage, taxDirectionMessage);
    assert.equal(elements.propertyTaxAdjustmentDirection.focused, true);

    elements.propertyTaxAdjustmentDirection.value = 'debit';
    elements.propertyTaxAdjustmentDirection.setCustomValidity('');
    context.calcNet();
    assert.match(
      elements.lineItems.innerHTML,
      isSpanish ? /Débito de Impuesto a la Propiedad Ingresado/ : /Property-Tax Debit Entered/,
    );
    assert.match(elements.lineItems.innerHTML, /-\$1,000/);
    assert.match(elements.lineItems.innerHTML, /\$98,600/);

    elements.propertyTaxAdjustmentDirection.value = 'credit';
    context.calcNet();
    assert.match(
      elements.lineItems.innerHTML,
      isSpanish
        ? /Crédito\/Reembolso de Impuesto a la Propiedad Ingresado/
        : /Property-Tax Credit\/Reimbursement Entered/,
    );
    assert.match(elements.lineItems.innerHTML, /\$100,600/);
    assert.doesNotMatch(elements.lineItems.innerHTML, /-\$1,000/);

    elements.propertyTaxAdjustment.value = '-1';
    context.calcNet();
    assert.equal(elements.results.style.display, 'none');
    assert.equal(elements.propertyTaxAdjustment.reported, true);
  });

  test(`${relative}: Graduated Percent Fee is deducted only after explicit confirmation`, () => {
    const elements = netElements();
    const context = contextFor(relative, 'calcNet', elements);
    const gpfLine = relative.startsWith('es/')
      ? /Graduated Percent Fee de NJ estimada \(1% del precio completo\)/
      : /Estimated NJ Graduated Percent Fee \(1% of full price\)/;
    const possibleGpfLine = relative.startsWith('es/')
      ? /Posible Graduated Percent Fee de NJ \(no deducida; requiere confirmación\)/
      : /Possible NJ Graduated Percent Fee \(not deducted; confirmation required\)/;
    const excludedGpfLine = relative.startsWith('es/')
      ? /Graduated Percent Fee de NJ \(confirmada sin deducción de los fondos del vendedor\)/
      : /NJ Graduated Percent Fee \(confirmed not deducted from seller proceeds\)/;
    elements.salePrice.value = '1000000.01';
    elements.brokerCompensation.value = '0';

    elements.graduatedPercentFeeApplicability.value = 'unknown';
    context.calcNet();
    assert.doesNotMatch(elements.lineItems.innerHTML, gpfLine);
    assert.match(elements.lineItems.innerHTML, possibleGpfLine);
    assert.match(elements.lineItems.innerHTML, /\$10,000\.00/);
    assert.match(
      elements.lineItems.innerHTML,
      relative.startsWith('es/')
        ? /Neto Estimado \(Excluye la Posible Tarifa No Confirmada\)/
        : /Estimated Net \(Excludes Unconfirmed Possible Fee\)/,
    );
    assert.match(elements.lineItems.innerHTML, /\$1,000,000\.01/);
    assert.match(elements.lineItems.innerHTML, /\$990,418\.96/);

    elements.graduatedPercentFeeApplicability.value = 'applies';
    context.calcNet();
    assert.match(elements.lineItems.innerHTML, gpfLine);
    assert.doesNotMatch(elements.lineItems.innerHTML, possibleGpfLine);
    assert.match(elements.lineItems.innerHTML, /\$980,418\.96/);

    elements.graduatedPercentFeeApplicability.value = 'not-applicable';
    context.calcNet();
    assert.doesNotMatch(elements.lineItems.innerHTML, gpfLine);
    assert.doesNotMatch(elements.lineItems.innerHTML, possibleGpfLine);
    assert.match(elements.lineItems.innerHTML, excludedGpfLine);
    assert.match(elements.lineItems.innerHTML, /\$0\.00/);
    assert.match(elements.lineItems.innerHTML, /\$990,418\.96/);

    elements.salePrice.value = '1000000';
    elements.graduatedPercentFeeApplicability.value = 'unknown';
    context.calcNet();
    assert.doesNotMatch(elements.lineItems.innerHTML, gpfLine);
    assert.doesNotMatch(elements.lineItems.innerHTML, possibleGpfLine);
    assert.doesNotMatch(elements.lineItems.innerHTML, excludedGpfLine);
    assert.match(elements.lineItems.innerHTML, /\$990,425\.00/);
  });

  test(`${relative}: displayed cents reconcile across percentage and statutory fee calculations`, () => {
    const elements = netElements();
    const context = contextFor(relative, 'calcNet', elements);
    assert.equal(context.roundCurrency(40000.005), 40000.01);
    assert.equal(context.roundCurrency(-40000.005), -40000.01);
    elements.salePrice.value = '333333.33';
    elements.brokerCompensation.value = '2.75';
    context.calcNet();
    assert.match(elements.lineItems.innerHTML, /-\$9,166\.67/);
    assert.match(elements.lineItems.innerHTML, /-\$1,976\.30/);
    assert.match(elements.lineItems.innerHTML, /\$322,190\.36/);

    elements.salePrice.value = '1000000.50';
    elements.brokerCompensationMethod.value = 'flat';
    context.updateBrokerCompensationField();
    assert.equal(elements.brokerCompensation.step, '0.01');
    elements.brokerCompensation.value = '1234.56';
    elements.graduatedPercentFeeApplicability.value = 'unknown';
    context.calcNet();
    assert.match(elements.lineItems.innerHTML, /\$10,000\.01/);
    assert.match(elements.lineItems.innerHTML, /-\$1,234\.56/);
    assert.match(elements.lineItems.innerHTML, /-\$9,581\.05/);
    assert.match(elements.lineItems.innerHTML, /\$989,184\.89/);

    elements.graduatedPercentFeeApplicability.value = 'applies';
    context.calcNet();
    assert.match(elements.lineItems.innerHTML, /-\$10,000\.01/);
    assert.match(elements.lineItems.innerHTML, /\$979,184\.88/);
  });

  test(`${relative}: every negative numeric input fails closed`, () => {
    for (const id of [
      'salePrice', 'brokerCompensation', 'payoff', 'attorney',
      'propertyTaxAdjustment', 'concessions', 'otherCosts', 'estimatedTaxPayment',
    ]) {
      const elements = netElements();
      const context = contextFor(relative, 'calcNet', elements);
      elements.brokerCompensation.value = '0';
      elements[id].value = '-0.01';
      context.calcNet();
      assert.equal(elements.results.style.display, 'none', `${id} must hide stale results`);
      assert.equal(elements[id].reported, true, `${id} must report invalid input`);
    }
  });

  test(`${relative}: calculator controls remain explicit and accessible`, () => {
    const source = fs.readFileSync(path.join(ROOT, relative), 'utf8');
    assert.match(source, /<label for="propertyTaxAdjustmentDirection">/);
    assert.match(source, /<select id="propertyTaxAdjustmentDirection"/);
    assert.match(source, /<label for="graduatedPercentFeeApplicability">/);
    assert.match(source, /<select id="graduatedPercentFeeApplicability"/);
    assert.match(source, /<option value="unknown">/);
    assert.match(source, /<option value="applies">/);
    assert.match(source, /<option value="not-applicable">/);
    assert.match(source, /aria-describedby="graduatedPercentFeeHelp"/);
    assert.match(source, /id="salePrice" min="0\.01" step="0\.01"/);
  });

  test(`${relative}: calculator AI provenance remains source-checked`, () => {
    const source = fs.readFileSync(path.join(ROOT, relative), 'utf8');
    assert.match(source, /<meta name="ai-content-declaration" content="ai-assisted, source-checked">/);
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
    assert.equal(elements.brokerCompensation.step, '0.01');
    elements.brokerCompensation.value = '1234.56';
    context.calcNet();
    assert.equal(elements.results.style.display, 'block');
    assert.match(elements.lineItems.innerHTML, /-\$1,234\.56/);

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
