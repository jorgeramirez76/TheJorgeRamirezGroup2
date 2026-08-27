import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const root = path.resolve(import.meta.dirname, '..');

function api(relative, id, name) {
  const source = fs.readFileSync(path.join(root, relative), 'utf8');
  const match = source.match(new RegExp(`<script id="${id}">([\\s\\S]*?)<\\/script>`));
  assert.ok(match, `${relative} exposes ${id}`);
  const context = { window: {}, Number, Math, Object, Array, String, Error };
  vm.runInNewContext(match[1], context, { filename: relative });
  assert.ok(context.window[name], `${relative} exposes ${name}`);
  return context.window[name];
}

function mortgagePayment(principal, annualRate, termYears) {
  const months = termYears * 12;
  const monthlyRate = annualRate / 1200;
  return monthlyRate === 0
    ? principal / months
    : principal * monthlyRate / (1 - (1 + monthlyRate) ** -months);
}

function remainingBalance(principal, annualRate, termYears, paidMonths) {
  const payment = mortgagePayment(principal, annualRate, termYears);
  const monthlyRate = annualRate / 1200;
  return monthlyRate === 0
    ? principal - payment * paidMonths
    : principal * (1 + monthlyRate) ** paidMonths
      - payment * (((1 + monthlyRate) ** paidMonths - 1) / monthlyRate);
}

const scenario = {
  purchasePrice: 400000,
  downPayment: 80000,
  mortgageRate: 6,
  mortgageTerm: 30,
  plannedYears: 5,
  monthlyRent: 2500,
  annualRentChange: 0,
  annualPropertyTax: 10000,
  annualHomeInsurance: 1800,
  monthlyHoa: 0,
  annualMaintenance: 4000,
  monthlyMortgageInsurance: 0,
  buyerClosingCosts: 12000,
  annualAppreciation: 0,
  sellerExitCosts: 24000,
  monthlyRentersInsurance: 240,
  renterNonrefundableCosts: 0,
  alternativeInvestment: 80000,
  annualInvestmentReturn: 0,
};

for (const relative of ['rent-vs-buy-nj.html', 'es/rent-vs-buy-nj.html']) {
  const worksheet = api(relative, 'rent-buy-worksheet-script', 'RentBuyWorksheet');
  const result = worksheet.calculateScenario(scenario);
  const payment = mortgagePayment(320000, 6, 30);
  const balance = remainingBalance(320000, 6, 30, 60);
  const expectedBuy = 80000 + 12000 + payment * 60 + 10000 * 5 + 1800 * 5
    + 4000 * 5 - (400000 - balance - 24000);
  assert.ok(Math.abs(result.monthlyPrincipalInterest - payment) < 0.000001, relative);
  assert.ok(Math.abs(result.remainingMortgageBalance - balance) < 0.000001, relative);
  assert.ok(Math.abs(result.buyNetOutflow - expectedBuy) < 0.000001, relative);
  assert.equal(result.rentNetOutflow, 164400, relative);
  assert.ok(Math.abs(result.difference - (expectedBuy - 164400)) < 0.000001, relative);
  assert.equal(result.futureHomeValue, 400000, relative);

  const zeroRate = worksheet.calculateScenario({ ...scenario, mortgageRate: 0, mortgageTerm: 20, plannedYears: 5 });
  assert.ok(Number.isFinite(zeroRate.remainingMortgageBalance), `${relative}: zero-rate branch`);
  assert.throws(
    () => worksheet.calculateScenario({ ...scenario, plannedYears: 31, mortgageTerm: 30 }),
    /term|plazo/i,
    `${relative}: holding period cannot exceed loan term`,
  );
  assert.throws(
    () => worksheet.calculateScenario({ ...scenario, annualAppreciation: -100 }),
    /greater|mayor/i,
    `${relative}: unsafe percentage rejected`,
  );
}

const commute = api(
  'blog/nj-commute-cost-nyc-2026.html',
  'commute-cost-worksheet-script',
  'CommuteCostWorksheet',
);
const commuteResult = commute.calculate({
  transitDays: 8,
  transitFarePerDay: 20,
  stationParkingPerDay: 5,
  destinationTransitPerDay: 3,
  otherTransitMonthly: 10,
  drivingDays: 2,
  tollsPerDay: 25,
  drivingParkingPerDay: 40,
  fuelPerDay: 15,
  otherDrivingMonthly: 5,
  annualFees: 120,
  transitRoundTripMinutes: 120,
  drivingRoundTripMinutes: 100,
});
assert.equal(commuteResult.monthlyTransit, 234);
assert.equal(commuteResult.monthlyDriving, 165);
assert.equal(commuteResult.annualCashCost, 4908);
assert.equal(commuteResult.annualTravelHours, (8 * 120 + 2 * 100) * 12 / 60);
assert.throws(() => commute.calculate({ transitDays: -1 }), /negative/i);

console.log('decision-finance worksheet tests passed');
