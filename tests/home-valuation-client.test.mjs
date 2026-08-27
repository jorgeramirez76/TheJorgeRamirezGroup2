import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";

const clientSource = await readFile(
  new URL("../js/home-valuation.js", import.meta.url),
  "utf8",
);
const client = await import(
  `data:text/javascript;base64,${Buffer.from(clientSource).toString("base64")}`
);

test("validates and normalizes the valuation intake", () => {
  assert.deepEqual(
    client.validateValuationLead({
      name: "  Test Visitor  ",
      email: " visitor@example.com ",
      address: " 123 Test Street, Summit, NJ ",
    }),
    {
      ok: true,
      values: {
        name: "Test Visitor",
        email: "visitor@example.com",
        address: "123 Test Street, Summit, NJ",
        phone: "",
      },
    },
  );
  assert.equal(
    client.validateValuationLead({ name: "Test", email: "bad", address: "123 Test" }).ok,
    false,
  );
  assert.equal(
    client.validateValuationLead({ name: "Test", email: "test@example.com", address: "" }).ok,
    false,
  );
  assert.deepEqual(
    client.validateValuationLead({
      name: "Test",
      email: "test@example.com",
      address: "123 Test Street",
      phone: "123",
    }).fields,
    ["phone"],
  );
});

test("builds a CRM-compatible payload without implying SMS consent", () => {
  const payload = client.buildValuationPayload({
    name: "Test Visitor",
    email: "visitor@example.com",
    phone: "908-555-0100",
    address: "123 Test Street",
    town: "Summit",
    timeframe: "3-6 months",
    message: "Planning ahead",
    smsConsent: false,
    _honey: "",
    _startedAt: "1000",
  });

  assert.equal(payload.leadType, "home-valuation");
  assert.equal(payload.intent, "Home valuation request");
  assert.equal(payload.smsConsent, false);
  assert.equal(payload.address, "123 Test Street");
  assert.equal(payload._source, "/home-valuation");

  const optedIn = client.buildValuationPayload({
    ...payload,
    smsConsent: true,
  });
  assert.equal(optedIn.smsConsent, true);
  assert.match(optedIn.consentLanguage, /Consent is optional and is not a condition of service/);
});

test("tracks generate_lead only after a confirmed API delivery", async () => {
  const tracked = [];
  const confirmed = await client.submitValuationLead(
    { name: "Test" },
    {
      fetchImpl: async () => ({
        ok: true,
        json: async () => ({ ok: true, accepted: true }),
      }),
      track: (event, details) => tracked.push({ event, details }),
    },
  );

  assert.equal(confirmed.ok, true);
  assert.equal(tracked.length, 1);
  assert.equal(tracked[0].event, "generate_lead");
  assert.deepEqual(tracked[0].details, {
    form_id: "home_valuation",
    lead_type: "home_valuation",
  });

  tracked.length = 0;
  const rejected = await client.submitValuationLead(
    { name: "Test" },
    {
      fetchImpl: async () => ({
        ok: true,
        json: async () => ({ ok: true, accepted: false }),
      }),
      track: (event, details) => tracked.push({ event, details }),
    },
  );

  assert.equal(rejected.ok, false);
  assert.equal(tracked.length, 0);
});

test("reports network and server failures without tracking", async () => {
  let tracked = false;
  const result = await client.submitValuationLead(
    { name: "Test" },
    {
      fetchImpl: async () => ({
        ok: false,
        json: async () => ({ ok: false, code: "delivery_failed" }),
      }),
      track: () => {
        tracked = true;
      },
    },
  );

  assert.equal(result.ok, false);
  assert.equal(tracked, false);
});

test("preserves API validation fields and maps actionable error messages", async () => {
  const invalid = await client.submitValuationLead(
    { name: "Test" },
    {
      fetchImpl: async () => ({
        ok: false,
        json: async () => ({ ok: false, code: "invalid_lead", fields: ["phone"] }),
      }),
    },
  );

  assert.deepEqual(invalid, { ok: false, code: "invalid_lead", fields: ["phone"] });
  assert.match(client.valuationErrorMessage(invalid), /at least seven digits/);
  assert.match(
    client.valuationErrorMessage({ ok: false, code: "rate_limited" }),
    /wait a few minutes/,
  );
  assert.match(client.valuationErrorMessage(), /could not confirm/);
  assert.match(client.valuationErrorMessage({}, "es"), /No pudimos confirmar/);
  assert.match(
    client.valuationErrorMessage({ ok: false, code: "rate_limited" }, "es"),
    /Espere unos minutos/,
  );
});

test("preserves the localized valuation intent and source", () => {
  const payload = client.buildValuationPayload({
    name: "María López",
    email: "maria@example.com",
    address: "123 Main St, Summit, NJ",
    intent: "Solicitud de valoración de casa",
    _source: "/es/home-valuation",
  });

  assert.equal(payload.intent, "Solicitud de valoración de casa");
  assert.equal(payload._source, "/es/home-valuation");
});

test("keeps a confirmed lead successful when analytics throws", async () => {
  const result = await client.submitValuationLead(
    { name: "Test" },
    {
      fetchImpl: async () => ({
        ok: true,
        json: async () => ({ ok: true, accepted: true }),
      }),
      track: () => {
        throw new Error("blocked analytics wrapper");
      },
    },
  );

  assert.deepEqual(result, { ok: true });
});
