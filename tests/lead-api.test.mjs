import assert from "node:assert/strict";
import { afterEach, beforeEach, test } from "node:test";
import { readFile } from "node:fs/promises";

const apiSource = await readFile(new URL("../api/lead.js", import.meta.url), "utf8");
const { default: handler } = await import(
  `data:text/javascript;base64,${Buffer.from(apiSource).toString("base64")}`
);

const deliveryEnv = [
  "TWILIO_ACCOUNT_SID",
  "TWILIO_AUTH_TOKEN",
  "TWILIO_FROM",
  "LEAD_ALERT_TO",
  "CRM_WEBHOOK_URL",
  "SITE_LEAD_WEBHOOK_SECRET",
  "RESEND_API_KEY",
  "LEAD_EMAIL",
  "RESEND_FROM",
  "LEAD_DELIVERY_TIMEOUT_MS",
];

let originalFetch;
let originalEnv;
let requestId = 0;

beforeEach(() => {
  originalFetch = globalThis.fetch;
  originalEnv = Object.fromEntries(deliveryEnv.map((key) => [key, process.env[key]]));
  deliveryEnv.forEach((key) => delete process.env[key]);
});

afterEach(() => {
  globalThis.fetch = originalFetch;
  deliveryEnv.forEach((key) => {
    if (originalEnv[key] === undefined) delete process.env[key];
    else process.env[key] = originalEnv[key];
  });
});

function createResponse() {
  const state = { status: 200, headers: {}, body: undefined, redirect: undefined };
  return {
    state,
    response: {
      setHeader(name, value) {
        state.headers[name] = value;
      },
      status(code) {
        state.status = code;
        return this;
      },
      send(body) {
        state.body = body;
        return this;
      },
      json(body) {
        state.body = body;
        return this;
      },
      redirect(code, destination) {
        state.status = code;
        state.redirect = destination;
        return this;
      },
    },
  };
}

function request(body, { json = true, ip } = {}) {
  requestId += 1;
  return {
    method: "POST",
    body,
    headers: {
      accept: json ? "application/json" : "text/html",
      referer: "https://thejorgeramirezgroup.com/home-valuation",
      "x-forwarded-for": ip === undefined ? `203.0.113.${requestId}` : ip,
    },
  };
}

function validValuation(overrides = {}) {
  return {
    leadType: "home-valuation",
    name: "Test Visitor",
    email: "visitor@example.com",
    phone: "908-555-0100",
    address: "123 Test Street, Summit, NJ 07901",
    timeframe: "3-6 months",
    intent: "Home valuation request",
    _source: "/home-valuation",
    _startedAt: String(Date.now() - 5_000),
    ...overrides,
  };
}

test("rejects an invalid valuation before attempting delivery", async () => {
  let fetchCalls = 0;
  globalThis.fetch = async () => {
    fetchCalls += 1;
    return { ok: true, text: async () => "" };
  };
  process.env.CRM_WEBHOOK_URL = "https://crm.invalid.test/leads";
  const { state, response } = createResponse();

  await handler(request(validValuation({ address: "", email: "not-an-email" })), response);

  assert.equal(state.status, 400);
  assert.equal(state.body.ok, false);
  assert.equal(state.body.code, "invalid_lead");
  assert.equal(fetchCalls, 0);
});

test("rejects nested JSON fields without throwing or attempting delivery", async () => {
  let fetchCalls = 0;
  globalThis.fetch = async () => {
    fetchCalls += 1;
  };
  process.env.CRM_WEBHOOK_URL = "https://crm.invalid.test/leads";
  const { state, response } = createResponse();

  await handler(request({
    ...validValuation(),
    leadType: { toString: "not callable" },
    _startedAt: { valueOf: "not callable" },
  }), response);

  assert.equal(state.status, 400);
  assert.deepEqual(state.body, { ok: false, code: "invalid_payload" });
  assert.equal(fetchCalls, 0);
});

test("silently discards honeypot submissions without reporting a confirmed lead", async () => {
  let fetchCalls = 0;
  globalThis.fetch = async () => {
    fetchCalls += 1;
  };
  const { state, response } = createResponse();

  await handler(request(validValuation({ _honey: "bot" })), response);

  assert.deepEqual(state.body, { ok: true, accepted: false });
  assert.equal(fetchCalls, 0);
});

test("silently discards implausibly fast valuation submissions", async () => {
  let fetchCalls = 0;
  globalThis.fetch = async () => {
    fetchCalls += 1;
  };
  const { state, response } = createResponse();

  await handler(request(validValuation({ _startedAt: String(Date.now()) })), response);

  assert.deepEqual(state.body, { ok: true, accepted: false });
  assert.equal(fetchCalls, 0);
});

test("silently discards JSON valuation submissions with no timing marker", async () => {
  let fetchCalls = 0;
  globalThis.fetch = async () => {
    fetchCalls += 1;
  };
  const { state, response } = createResponse();

  await handler(request(validValuation({ _startedAt: "" })), response);

  assert.deepEqual(state.body, { ok: true, accepted: false });
  assert.equal(fetchCalls, 0);
});

test("confirms a valuation only after the CRM accepts it", async () => {
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push({ url, options });
    return { ok: true, text: async () => "" };
  };
  process.env.CRM_WEBHOOK_URL = "https://crm.invalid.test/leads";
  const { state, response } = createResponse();

  await handler(request(validValuation({
    smsConsent: "on",
    consentLanguage: "forged client disclosure",
  }), { ip: "203.0.113.80" }), response);

  assert.equal(state.status, 200);
  assert.deepEqual(state.body, { ok: true, accepted: true });
  assert.equal(calls.length, 1);
  const delivered = JSON.parse(calls[0].options.body);
  assert.equal(delivered.address, "123 Test Street, Summit, NJ 07901");
  assert.equal(delivered.leadType, "home-valuation");
  assert.equal(delivered.smsConsent, true);
  assert.match(delivered.consentLanguage, /Consent is optional and is not a condition of service/);
  assert.notEqual(delivered.consentLanguage, "forged client disclosure");
  assert.equal(delivered.consentIp, "203.0.113.80");
  assert.equal(Number.isNaN(Date.parse(delivered.consentAt)), false);
});

test("records the guide disclosure instead of valuation consent text", async () => {
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push({ url, options });
    return { ok: true, text: async () => "" };
  };
  process.env.CRM_WEBHOOK_URL = "https://crm.invalid.test/leads";
  const { state, response } = createResponse();

  await handler(request({
    name: "Guide Visitor",
    email: "guide@example.com",
    phone: "908-555-0110",
    guide: "seller",
    intent: "Seller guide download",
    smsConsent: "on",
    consentLanguage: "forged client disclosure",
  }, { ip: "203.0.113.81" }), response);

  assert.equal(state.status, 200);
  const delivered = JSON.parse(calls[0].options.body);
  assert.equal(delivered.smsConsent, true);
  assert.match(delivered.consentLanguage, /including by automated technology/);
  assert.match(delivered.consentLanguage, /Message frequency varies/);
  assert.match(delivered.consentLanguage, /HELP for help/);
  assert.doesNotMatch(delivered.consentLanguage, /home valuation request/);
  assert.equal(delivered.consentIp, "203.0.113.81");
});

test("keeps the non-JavaScript valuation fallback classified and truthful", async () => {
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push({ url, options });
    return { ok: true, text: async () => "" };
  };
  process.env.CRM_WEBHOOK_URL = "https://crm.invalid.test/leads";
  const { state, response } = createResponse();

  await handler(
    request(validValuation({ _startedAt: "", _next: "/home-valuation" }), { json: false }),
    response,
  );

  assert.equal(state.status, 303);
  assert.equal(state.redirect, "/home-valuation?submitted=1#valuation-submitted");
  assert.equal(JSON.parse(calls[0].options.body).leadType, "home-valuation");
});

test("keeps the Spanish non-JavaScript valuation fallback on the localized page", async () => {
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push({ url, options });
    return { ok: true, text: async () => "" };
  };
  process.env.CRM_WEBHOOK_URL = "https://crm.invalid.test/leads";
  const { state, response } = createResponse();

  await handler(
    request(validValuation({
      _startedAt: "",
      _next: "/es/home-valuation",
      _source: "/es/home-valuation",
      intent: "Solicitud de valoración de casa",
    }), { json: false }),
    response,
  );

  assert.equal(state.status, 303);
  assert.equal(state.redirect, "/es/home-valuation?submitted=1#valuation-submitted");
  const delivered = JSON.parse(calls[0].options.body);
  assert.equal(delivered.leadType, "home-valuation");
  assert.equal(delivered.source, "/es/home-valuation");
});

test("returns an error when no configured channel confirms delivery", async () => {
  const { state, response } = createResponse();

  await handler(request(validValuation()), response);

  assert.equal(state.status, 502);
  assert.deepEqual(state.body, { ok: false, code: "delivery_failed" });
});

test("does not redirect a failed non-JavaScript valuation to the success page", async () => {
  const { state, response } = createResponse();

  await handler(
    request(validValuation({ _startedAt: "", _next: "/home-valuation" }), { json: false }),
    response,
  );

  assert.equal(state.status, 303);
  assert.equal(state.redirect, "/home-valuation?err=1#valuation-error");
});

test("uses a same-site error destination when a contact lead is not delivered", async () => {
  const { state, response } = createResponse();

  await handler(request({
    leadType: "website-contact",
    name: "Contact Visitor",
    email: "contact@example.com",
    _source: "/",
    _next: "/thank-you",
    _errorNext: "/#contact-error",
  }, { json: false }), response);

  assert.equal(state.status, 303);
  assert.equal(state.redirect, "/#contact-error");
});

test("does not accept an external contact error destination", async () => {
  const { state, response } = createResponse();

  await handler(request({
    leadType: "website-contact",
    name: "Contact Visitor",
    email: "contact@example.com",
    _next: "/thank-you",
    _errorNext: "https://attacker.example/collect",
  }, { json: false }), response);

  assert.equal(state.status, 303);
  assert.equal(state.redirect, "/thank-you?err=1");
});

test("rate limits repeated valid valuation delivery attempts from one IP", async () => {
  let fetchCalls = 0;
  globalThis.fetch = async () => {
    fetchCalls += 1;
    return { ok: true, text: async () => "" };
  };
  process.env.CRM_WEBHOOK_URL = "https://crm.invalid.test/leads";
  const ip = "203.0.113.200";

  for (let attempt = 0; attempt < 5; attempt += 1) {
    const { state, response } = createResponse();
    await handler(request(validValuation(), { ip }), response);
    assert.equal(state.status, 200);
  }

  const { state, response } = createResponse();
  await handler(request(validValuation(), { ip }), response);
  assert.equal(state.status, 429);
  assert.deepEqual(state.body, { ok: false, code: "rate_limited" });
  assert.equal(fetchCalls, 5);
});

test("rate limits every accepted non-valuation lead type by client IP", async () => {
  const leadTypes = [
    {
      label: "website contact",
      body: {
        leadType: "website-contact",
        name: "Contact Visitor",
        email: "contact@example.com",
        _source: "/contact",
      },
    },
    {
      label: "guide download",
      body: {
        name: "Guide Visitor",
        email: "guide@example.com",
        guide: "buyer",
        intent: "Buyer guide download",
        _source: "/nj-home-buyer-guide",
      },
    },
    {
      label: "mortgage calculator",
      body: {
        leadType: "mortgage-calculator",
        name: "Calculator Visitor",
        email: "calculator@example.com",
        intent: "Mortgage calculator follow-up request",
        _source: "/tools/mortgage-calculator",
      },
    },
  ];

  for (const [index, scenario] of leadTypes.entries()) {
    let fetchCalls = 0;
    globalThis.fetch = async () => {
      fetchCalls += 1;
      return { ok: true, text: async () => "" };
    };
    process.env.CRM_WEBHOOK_URL = "https://crm.invalid.test/leads";
    const ip = `203.0.113.${220 + index}`;

    for (let attempt = 0; attempt < 5; attempt += 1) {
      const { state, response } = createResponse();
      await handler(request(scenario.body, { ip }), response);
      assert.equal(state.status, 200, scenario.label);
    }

    const { state, response } = createResponse();
    await handler(request(scenario.body, { ip }), response);
    assert.equal(state.status, 429, scenario.label);
    assert.deepEqual(state.body, { ok: false, code: "rate_limited" }, scenario.label);
    assert.equal(state.headers["Retry-After"], "600", scenario.label);
    assert.equal(fetchCalls, 5, scenario.label);
  }
});

test("fails closed before delivery when no client IP is available", async () => {
  let fetchCalls = 0;
  globalThis.fetch = async () => {
    fetchCalls += 1;
    return { ok: true, text: async () => "" };
  };
  process.env.CRM_WEBHOOK_URL = "https://crm.invalid.test/leads";
  const { state, response } = createResponse();

  await handler(request({
    leadType: "website-contact",
    name: "Contact Visitor",
    email: "contact@example.com",
    _source: "/contact",
  }, { ip: "" }), response);

  assert.equal(state.status, 429);
  assert.deepEqual(state.body, { ok: false, code: "rate_limited" });
  assert.equal(state.headers["Retry-After"], "600");
  assert.equal(fetchCalls, 0);
});

test("keeps rate-limited HTML contact submissions on the configured error route", async () => {
  globalThis.fetch = async () => ({ ok: true, text: async () => "" });
  process.env.CRM_WEBHOOK_URL = "https://crm.invalid.test/leads";
  const ip = "203.0.113.230";
  const body = {
    leadType: "website-contact",
    name: "Contact Visitor",
    email: "contact@example.com",
    _source: "/contact",
    _next: "/thank-you",
    _errorNext: "/contact#contact-error",
  };

  for (let attempt = 0; attempt < 5; attempt += 1) {
    const { response } = createResponse();
    await handler(request(body, { json: false, ip }), response);
  }

  const { state, response } = createResponse();
  await handler(request(body, { json: false, ip }), response);
  assert.equal(state.status, 303);
  assert.equal(state.redirect, "/contact#contact-error");
  assert.equal(state.headers["Retry-After"], "600");
});

test("does not allow a protocol-relative redirect through _next", async () => {
  const { state, response } = createResponse();

  await handler(
    request({ name: "Test", email: "test@example.com", _honey: "bot", _next: "//malicious.invalid" }, { json: false }),
    response,
  );

  assert.equal(state.status, 303);
  assert.equal(state.redirect, "/thank-you");
});

test("bounds a hanging provider while preserving another confirmed delivery", async () => {
  const signals = [];
  globalThis.fetch = async (url, options) => {
    signals.push(options.signal);
    if (url.includes("crm.invalid.test")) return new Promise(() => {});
    return { ok: true, text: async () => "" };
  };
  process.env.CRM_WEBHOOK_URL = "https://crm.invalid.test/leads";
  process.env.RESEND_API_KEY = "test-key";
  process.env.RESEND_FROM = "sender@example.test";
  process.env.LEAD_EMAIL = "receiver@example.test";
  process.env.LEAD_DELIVERY_TIMEOUT_MS = "30";
  const { state, response } = createResponse();
  const started = Date.now();

  await handler(request(validValuation(), { ip: "203.0.113.210" }), response);

  assert.equal(state.status, 200);
  assert.deepEqual(state.body, { ok: true, accepted: true });
  assert.ok(Date.now() - started < 500);
  assert.equal(signals.length, 2);
  assert.ok(signals.every((signal) => signal instanceof AbortSignal));
  assert.equal(signals[0].aborted, true);
});

test("does not wait on a stalled provider error body", async () => {
  globalThis.fetch = async (url) => {
    if (url.includes("api.twilio.com")) {
      return { ok: false, status: 500, text: async () => new Promise(() => {}) };
    }
    return { ok: true, text: async () => "" };
  };
  process.env.TWILIO_ACCOUNT_SID = "test-sid";
  process.env.TWILIO_AUTH_TOKEN = "test-token";
  process.env.TWILIO_FROM = "+19085550101";
  process.env.LEAD_ALERT_TO = "+19085550102";
  process.env.CRM_WEBHOOK_URL = "https://crm.invalid.test/leads";
  process.env.LEAD_DELIVERY_TIMEOUT_MS = "30";
  const { state, response } = createResponse();
  const started = Date.now();

  await handler(request(validValuation(), { ip: "203.0.113.211" }), response);

  assert.equal(state.status, 200);
  assert.deepEqual(state.body, { ok: true, accepted: true });
  assert.ok(Date.now() - started < 500);
});
